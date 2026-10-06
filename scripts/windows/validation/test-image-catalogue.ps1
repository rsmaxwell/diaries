#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BackupFile,
    [Parameter(Mandatory)][string]$EvidenceDirectory
)
# 0024 Phase 9. All database mutations are confined to new disposable containers.
$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$backup = (Get-Item -LiteralPath $BackupFile).FullName
if (!(Test-Path -LiteralPath $backup -PathType Leaf)) { throw 'BackupFile must be a regular file.' }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Choose a new evidence directory.' }
$evidence = (New-Item -ItemType Directory -Path $EvidenceDirectory).FullName
$migration = Join-Path $repository 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/migration'
$imageFragmentMigration = Join-Path $repository 'change-control/complete/0025-FEAT - add responder ImageFragment persistence and RPC/migration'
$runId = [guid]::NewGuid().ToString('N').Substring(0,12)
$sqlContainer = "diaries-0024-phase9-$runId-sql-test"
$dbContainer = "diaries-0024-phase9-$runId-db-test"
$brokerContainer = "diaries-0024-phase9-$runId-mqtt-test"
$owned = [Collections.Generic.List[string]]::new()
$environmentNames = @('DIARIES_IMAGE_REPOSITORY_TEST_URL','DIARIES_IMAGE_WIRING_TEST_URL','DIARIES_IMAGE_MQTT_TEST_URL','DIARIES_BROWSER_TEST_CLIENT','DIARIES_BROWSER_TEST_EVIDENCE','DIARIES_BROWSER_TEST_MQTT','CHROME_BIN')
$savedEnvironment = @{}
foreach ($name in $environmentNames) { $savedEnvironment[$name] = [Environment]::GetEnvironmentVariable($name,'Process') }
$result = [ordered]@{ phase=9; startedAtUtc=[DateTime]::UtcNow.ToString('o'); status='RUNNING'; backupFilename=[IO.Path]::GetFileName($backup); backupSha256=(Get-FileHash -LiteralPath $backup).Hash.ToLowerInvariant(); productionOrDevelopmentDatabaseUsed=$false; productionFilesRootUsed=$false }
function Invoke-Checked {
    param([string]$Program,[string[]]$Arguments,[string]$Log)
    $output = & $Program @Arguments 2>&1
    $code = $LASTEXITCODE
    if ($Log) { [IO.File]::WriteAllText((Join-Path $evidence $Log),($output -join "`n")+"`n") }
    if ($code -ne 0) { throw "$Program failed with exit $code. See $Log" }
    return $output
}
function Start-Fixture {
    param([string]$Name,[string[]]$Arguments)
    $null = Invoke-Checked docker (@('run','--detach','--rm','--name',$Name)+$Arguments)
    $owned.Add($Name)
}
function Wait-Postgres {
    param([string]$Name)
    $deadline = [DateTime]::UtcNow.AddSeconds(60)
    do {
        $null = & docker exec $Name pg_isready -U diaries 2>&1
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Milliseconds 250
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "PostgreSQL fixture $Name was not ready within 60 seconds."
}
function Read-TestResults {
    param([string]$Component)
    $reports = @(Get-ChildItem -LiteralPath (Join-Path $repository "$Component/build/test-results/test") -Filter 'TEST-*.xml')
    if ($reports.Count -eq 0) { throw "No $Component test reports." }
    $suites = @($reports | Sort-Object Name | ForEach-Object {
        [xml]$xml = Get-Content -LiteralPath $_.FullName -Raw
        [ordered]@{name=$xml.testsuite.name; tests=[int]$xml.testsuite.tests; failures=[int]$xml.testsuite.failures; errors=[int]$xml.testsuite.errors; skipped=[int]$xml.testsuite.skipped}
    })
    $totals = [ordered]@{tests=0;failures=0;errors=0;skipped=0}
    foreach ($suite in $suites) { foreach ($key in @('tests','failures','errors','skipped')) { $totals[$key]+=$suite[$key] } }
    [IO.File]::WriteAllText((Join-Path $evidence "$Component-tests.json"),(@{totals=$totals;suites=$suites}|ConvertTo-Json -Depth 8))
    if ($totals.tests -eq 0 -or $totals.failures -or $totals.errors -or $totals.skipped) { throw "$Component has failed or skipped tests." }
    return $totals
}
try {
    $null = Invoke-Checked docker @('info','--format','{{.ServerVersion}}') 'docker-version.txt'
    if (!$env:CHROME_BIN) {
        $chromeCandidates = @('C:/Program Files/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Google/Chrome/Application/chrome.exe','C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe')
        $env:CHROME_BIN = $chromeCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
    }
    if (!$env:CHROME_BIN -or !(Test-Path -LiteralPath $env:CHROME_BIN)) { throw 'Install Chrome/Edge or supply CHROME_BIN for headless Angular tests.' }
    Write-Host 'Starting disposable SQL, JPA and MQTT fixtures.'
    Start-Fixture $sqlContainer @('--network','none','--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries','-e','POSTGRES_DB=diaries','-e','POSTGRES_HOST_AUTH_METHOD=trust','postgres:18-alpine')
    Start-Fixture $dbContainer @('--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries','-e','POSTGRES_DB=image_repository_test','-e','POSTGRES_HOST_AUTH_METHOD=trust','-p','127.0.0.1::5432','postgres:18-alpine')
    $brokerBase = Join-Path $repository 'scripts/windows/validation/image-catalogue-test-mosquitto.conf'
    if (!(Test-Path -LiteralPath $brokerBase -PathType Leaf)) { throw "Permanent MQTT fixture config missing: $brokerBase" }
    $brokerConfig = Join-Path $evidence 'fixture-mosquitto.conf'
    Copy-Item -LiteralPath $brokerBase -Destination $brokerConfig
    # This disposable fixture intentionally accepts anonymous clients so the browser-level
    # Angular test and responder MQTT integration tests exercise the same broker. Production
    # authentication/ACL policy is deliberately outside this functional fixture.
    Start-Fixture $brokerContainer @('-p','127.0.0.1::1883','-p','127.0.0.1::9001','--mount',"type=bind,source=$brokerConfig,target=/mosquitto/config/mosquitto.conf,readonly",'--entrypoint','mosquitto','eclipse-mosquitto:2.0.22','-c','/mosquitto/config/mosquitto.conf')
    Wait-Postgres $sqlContainer
    Wait-Postgres $dbContainer
    Write-Host 'Running SQL preflight, schema, postflight and negative cases.'
    & (Join-Path $migration 'tests/run-tests.ps1') -Container $sqlContainer -BackupFile $backup -EvidenceDirectory (Join-Path $evidence 'sql') | Out-File (Join-Path $evidence 'sql-tests.log')
    $result.sql = Get-Content -LiteralPath (Join-Path $evidence 'sql/test-results.json') -Raw | ConvertFrom-Json
    $null = Invoke-Checked docker @('exec',$dbContainer,'createdb','-U','diaries','image_wiring_test')
    $null = Invoke-Checked docker @('cp',$backup,"${dbContainer}:/tmp/baseline.dump")
    $null = Invoke-Checked docker @('exec',$dbContainer,'pg_restore','-U','diaries','-d','image_wiring_test','--no-owner','--no-privileges','/tmp/baseline.dump')
    $null = Invoke-Checked docker @('cp',(Join-Path $migration 'schema.sql'),"${dbContainer}:/tmp/schema.sql")
    foreach ($database in @('image_repository_test','image_wiring_test')) {
        $null = Invoke-Checked docker @('exec',$dbContainer,'psql','-X','-U','diaries','-d',$database,'-v','ON_ERROR_STOP=1','-f','/tmp/schema.sql')
    }

    # The full responder EntityManagerFactory validates the current Fragment mapping, which
    # includes the nullable fragment.image_id reference introduced by 0025. The frozen 0024
    # baseline intentionally predates that migration, so advance only the restored wiring
    # fixture to the current post-0025 schema before running the full-JPA integration tests.
    # image_repository_test remains an Image-only fixture and therefore needs only 0024.
    $null = Invoke-Checked docker @('cp',$imageFragmentMigration,"${dbContainer}:/tmp/image-fragment-migration")
    $null = Invoke-Checked docker @(
        'exec',$dbContainer,'psql','-X','-U','diaries','-d','image_wiring_test','-v','ON_ERROR_STOP=1',
        '-f','/tmp/image-fragment-migration/001-preflight.sql',
        '-f','/tmp/image-fragment-migration/002-add-fragment-image-reference.sql',
        '-f','/tmp/image-fragment-migration/003-postflight.sql'
    ) 'image-fragment-schema.log'

    $dbBinding = (Invoke-Checked docker @('port',$dbContainer,'5432') | Out-String).Trim()
    $brokerBinding = (Invoke-Checked docker @('port',$brokerContainer,'1883') | Out-String).Trim()
    $browserBinding = (Invoke-Checked docker @('port',$brokerContainer,'9001') | Out-String).Trim()
    if ($dbBinding -notmatch '^127\.0\.0\.1:[0-9]+$' -or $brokerBinding -notmatch '^127\.0\.0\.1:[0-9]+$' -or $browserBinding -notmatch '^127\.0\.0\.1:[0-9]+$') { throw 'Fixture bindings must be loopback only.' }
    $env:DIARIES_IMAGE_REPOSITORY_TEST_URL = "jdbc:postgresql://$dbBinding/image_repository_test"
    $env:DIARIES_IMAGE_WIRING_TEST_URL = "jdbc:postgresql://$dbBinding/image_wiring_test"
    $env:DIARIES_IMAGE_MQTT_TEST_URL = "tcp://$brokerBinding"
    $env:DIARIES_BROWSER_TEST_CLIENT = Join-Path $repository 'diaries-client'
    $browserEvidence = Join-Path $evidence 'browser-e2e'
    New-Item -ItemType Directory -Path $browserEvidence -Force | Out-Null
    $env:DIARIES_BROWSER_TEST_EVIDENCE = $browserEvidence
    $env:DIARIES_BROWSER_TEST_MQTT = "ws://$browserBinding"
    Write-Host 'Running responder/web tests and builds with database and MQTT integration enabled.'
    $null = Invoke-Checked (Join-Path $repository 'gradlew.bat') @('-p',$repository,':diaries-responder:test',':diaries-responder:build',':diaries-web:test',':diaries-web:build','--rerun-tasks','--console=plain') 'java-test-build.log'
    $result.responder = Read-TestResults 'diaries-responder'
    $result.web = Read-TestResults 'diaries-web'
    Write-Host 'Running Angular file regressions, complete test suite and production build.'
    $client = Join-Path $repository 'diaries-client'
    $null = Invoke-Checked npm.cmd @('--prefix',$client,'test','--','--watch=false','--browsers=ChromeHeadless','--progress=false') 'client-test.log'
    $clientLog = Get-Content -LiteralPath (Join-Path $evidence 'client-test.log') -Raw
    $success = [regex]::Match($clientLog,'TOTAL: ([0-9]+) SUCCESS')
    if (!$success.Success -or $clientLog -match '([1-9][0-9]*) (skipped|FAILED)') { throw 'Client tests failed, skipped or did not report a passing total.' }
    $result.clientTests = [int]$success.Groups[1].Value
    $null = Invoke-Checked npm.cmd @('--prefix',$client,'run','build','--','--configuration','production') 'client-build.log'
    foreach ($component in @('', 'diaries-responder','diaries-client','diaries-web')) {
        $gitRoot = if ($component) { Join-Path $repository $component } else { $repository }
        $log = if ($component) { "$component-diff-check.txt" } else { 'parent-diff-check.txt' }
        $null = Invoke-Checked git @('-c',"safe.directory=$($gitRoot.Replace('\','/'))",'-C',$gitRoot,'diff','--check') $log
    }
    $result.status = 'PASSED'
    Write-Host 'Phase 9 checks passed. Evidence will be hashed after fixture cleanup.'
} catch {
    $result.status = 'FAILED'
    $result.failure = $_.Exception.Message
    throw
} finally {
    $cleanupFailures = @()
    foreach ($name in $owned) {
        $output = & docker stop $name 2>&1
        if ($LASTEXITCODE -ne 0) { $cleanupFailures += $name }
    }
    foreach ($name in $environmentNames) { [Environment]::SetEnvironmentVariable($name,$savedEnvironment[$name],'Process') }
    $result.cleanupFailures = $cleanupFailures
    if ($cleanupFailures.Count) { $result.status = 'CLEANUP_FAILED' }
    $result.finishedAtUtc = [DateTime]::UtcNow.ToString('o')
    [IO.File]::WriteAllText((Join-Path $evidence 'validation-summary.json'),($result|ConvertTo-Json -Depth 10))
    $hashes = @(Get-ChildItem -LiteralPath $evidence -Recurse -File | Sort-Object FullName | ForEach-Object {
        (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()+'  '+[IO.Path]::GetRelativePath($evidence,$_.FullName).Replace('\','/')
    })
    [IO.File]::WriteAllLines((Join-Path $evidence 'SHA256SUMS.txt'),$hashes)
    if ($cleanupFailures.Count) { throw "Could not stop owned test containers: $($cleanupFailures -join ', ')" }
}
