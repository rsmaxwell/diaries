#Requires -Version 7.0
# Live RPC and startup replay verification using disposable PostgreSQL and Mosquitto.
param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference = 'Stop'
$evidence = (New-Item -ItemType Directory $EvidenceDirectory -ErrorAction Stop).FullName
if (Test-Path (Join-Path $evidence 'result.json')) { throw 'Evidence already exists; do not overwrite or repeat this run.' }
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../../../..')).Path
$baseline = Join-Path $repository 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue'
$backup = Join-Path $repository 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
$schema = Join-Path $baseline 'migration/schema.sql'
$frozen = Get-Content -LiteralPath (Join-Path $baseline 'evidence/phase-09-validation/run/validation-summary.json') -Raw | ConvertFrom-Json
$test = 'com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.liveImageFragmentRpcAndRestartReplay'
$gateTest = 'com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.authoringGateRejectsMutationsButPreservesLifecycle'
$container = 'diaries-0025-step13-' + [guid]::NewGuid().ToString('N').Substring(0,12)
$owned = $false
$brokerOwned = $false
$brokerContainer = $container + '-mqtt'
$previousMqtt = $env:DIARIES_IMAGE_MQTT_TEST_URL
$previousUrl = $env:DIARIES_IMAGE_WIRING_TEST_URL
$result = [ordered]@{ status='RUNNING'; startedAtUtc=[DateTime]::UtcNow.ToString('o'); test=$test; gateTest=$gateTest; testInvocations=0; container=$container; liveDatabaseUsed=$false; nasFilesUsed=$false }
function Run([string]$Program, [string[]]$Arguments, [string]$Log) {
    $output = & $Program @Arguments 2>&1
    $code = $LASTEXITCODE
    $safe = ($output -join "`n") -replace 'eyJ[A-Za-z0-9_.-]+','[REDACTED TOKEN]'
    if ($Log) { [IO.File]::WriteAllText((Join-Path $evidence $Log), $safe + "`n") }
    if ($code -ne 0) { throw "$Program failed ($code); see $Log" }
    return $safe
}
try {
    $result.backupFilename = [IO.Path]::GetFileName($backup)
    $result.backupSha256 = (Get-FileHash -LiteralPath $backup).Hash.ToLowerInvariant()
    if ($result.backupSha256 -ne $frozen.backupSha256) { throw 'Backup does not match frozen 0024 evidence.' }
    $result.frozenBackupMatched = $true
    $result.schemaSha256 = (Get-FileHash -LiteralPath $schema).Hash.ToLowerInvariant()
    $source = Join-Path $repository 'diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/ImageWiringIntegrationTest.java'
    $result.testSourceSha256 = (Get-FileHash -LiteralPath $source).Hash.ToLowerInvariant()
    $gitRoot = (Join-Path $repository 'diaries-responder').Replace('\','/')
    $result.responderCommit = Run git @('-c',"safe.directory=$gitRoot",'-C',$gitRoot,'rev-parse','HEAD') 'responder-commit.txt'
    $null = Run git @('-c',"safe.directory=$gitRoot",'-C',$gitRoot,'status','--short') 'responder-status.txt'
    $result.postgresImageId = Run docker @('image','inspect','postgres:18-alpine','--format','{{.Id}}') 'postgres-image-id.txt'
    $null = Run docker @('run','--detach','--rm','--name',$container,'--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries','-e','POSTGRES_DB=image_wiring_test','-e','POSTGRES_HOST_AUTH_METHOD=trust','-p','127.0.0.1::5432',$result.postgresImageId) 'container-start.txt'
    $owned = $true
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        & docker exec $container pg_isready -U diaries 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        if ([DateTime]::UtcNow -gt $deadline) { throw 'PostgreSQL readiness timeout' }
        Start-Sleep -Milliseconds 250
    } while ($true)
    $null = Run docker @('cp',$backup,"${container}:/tmp/baseline.dump")
    $null = Run docker @('exec',$container,'pg_restore','-U','diaries','-d','image_wiring_test','--no-owner','--no-privileges','/tmp/baseline.dump') 'restore.log'
    $null = Run docker @('cp',$schema,"${container}:/tmp/schema.sql")
    $null = Run docker @('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-v','ON_ERROR_STOP=1','-f','/tmp/schema.sql') 'schema.log'
    $null = Run docker @('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-At','-c','SELECT version()') 'postgres-version.txt'
    $migration = (Resolve-Path (Join-Path $PSScriptRoot '../../migration')).Path
    $null = Run docker @('cp',$migration,"${container}:/tmp/migration")
    $null = Run docker @('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-v','ON_ERROR_STOP=1','-f','/tmp/migration/001-preflight.sql','-f','/tmp/migration/002-add-fragment-image-reference.sql','-f','/tmp/migration/003-postflight.sql') '0025-schema.log'
    $snapshot = "SELECT 'diary',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM diary t UNION ALL SELECT 'page',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM page t UNION ALL SELECT 'fragment',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM fragment t UNION ALL SELECT 'marquee',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM marquee t UNION ALL SELECT 'image',count(*),md5(coalesce(jsonb_agg(to_jsonb(t) ORDER BY id)::text,'[]')) FROM image t;"
    $before = Run docker @('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-At','-c',$snapshot) 'database-before.txt'
    $binding = (Run docker @('port',$container,'5432')).Trim()
    if ($binding -notmatch '^127\.0\.0\.1:[0-9]+$') { throw 'Expected loopback-only binding' }
    $env:DIARIES_IMAGE_WIRING_TEST_URL = "jdbc:postgresql://$binding/image_wiring_test"
    $result.testDatabaseUrl = $env:DIARIES_IMAGE_WIRING_TEST_URL
    $result.mosquittoImageId = Run docker @('image','inspect','eclipse-mosquitto:2','--format','{{.Id}}') 'mosquitto-image-id.txt'
    $brokerConfig = Join-Path $PSScriptRoot 'fixture-mosquitto.conf'
    $null = Run docker @('run','--detach','--rm','--name',$brokerContainer,'-p','127.0.0.1::1883','--mount',"type=bind,source=$brokerConfig,target=/mosquitto/config/mosquitto.conf,readonly",$result.mosquittoImageId) 'broker-start.txt'
    $brokerOwned = $true
    $deadline = [DateTime]::UtcNow.AddSeconds(30)
    do {
        & docker exec $brokerContainer mosquitto_pub -h 127.0.0.1 -t fixture/ready -m ready 2>&1 | Out-Null
        if ($LASTEXITCODE -eq 0) { break }
        if ([DateTime]::UtcNow -gt $deadline) { throw 'Broker readiness timeout' }
        Start-Sleep -Milliseconds 250
    } while ($true)
    $mqttBinding = (Run docker @('port',$brokerContainer,'1883')).Trim()
    if ($mqttBinding -notmatch '^127\.0\.0\.1:[0-9]+$') { throw 'Expected loopback-only broker binding' }
    $env:DIARIES_IMAGE_MQTT_TEST_URL = "tcp://$mqttBinding"
    $result.testBrokerUrl = $env:DIARIES_IMAGE_MQTT_TEST_URL
    $result.command = "gradlew.bat :diaries-responder:test --tests $test --tests $gateTest --rerun-tasks --console=plain"
    $result.testInvocations = 1
    $null = Run (Join-Path $repository 'gradlew.bat') @('-p',$repository,':diaries-responder:test','--tests',$test,'--tests',$gateTest,'--rerun-tasks','--console=plain') 'gradle-test.log'
    $report = Join-Path $repository 'diaries-responder/build/test-results/test/TEST-com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.xml'
    $reportText = [IO.File]::ReadAllText($report) -replace 'eyJ[A-Za-z0-9_.-]+','[REDACTED TOKEN]'
    [IO.File]::WriteAllText((Join-Path $evidence 'integration-test.xml'), $reportText)
    [xml]$xml = $reportText
    $result.tests = [int]$xml.testsuite.tests
    $result.failures = [int]$xml.testsuite.failures
    $result.errors = [int]$xml.testsuite.errors
    $result.skipped = [int]$xml.testsuite.skipped
    if ($result.tests -ne 2 -or $result.failures -or $result.errors -or $result.skipped) { throw 'Expected exactly two passing, non-skipped integration test.' }
    $after = Run docker @('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-At','-c',$snapshot) 'database-after.txt'
    if ($before -ne $after) { throw 'Database rows differ after fixture cleanup.' }
    $result.databaseRowsUnchangedAfterCleanup = $true
    $result.status = 'PASSED'
} catch {
    $result.status = 'FAILED'
    $result.failure = $_.Exception.Message
    throw
} finally {
    if ($brokerOwned) {
        $cleanup = & docker stop $brokerContainer 2>&1
        $result.brokerCleanupExitCode = $LASTEXITCODE
        [IO.File]::WriteAllText((Join-Path $evidence 'broker-cleanup.log'), ($cleanup -join "`n") + "`n")
        if ($result.brokerCleanupExitCode -ne 0) { $result.status = 'CLEANUP_FAILED' }
    }
    $env:DIARIES_IMAGE_MQTT_TEST_URL = $previousMqtt
    if ($owned) {
        $cleanup = & docker stop $container 2>&1
        $result.cleanupExitCode = $LASTEXITCODE
        [IO.File]::WriteAllText((Join-Path $evidence 'cleanup.log'), ($cleanup -join "`n") + "`n")
        if ($result.cleanupExitCode -ne 0) { $result.status = 'CLEANUP_FAILED' }
    }
    $env:DIARIES_IMAGE_WIRING_TEST_URL = $previousUrl
    $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
    [IO.File]::WriteAllText((Join-Path $evidence 'result.json'), ($result | ConvertTo-Json -Depth 6) + "`n")
    Write-Output ($result | ConvertTo-Json -Depth 6)
}

