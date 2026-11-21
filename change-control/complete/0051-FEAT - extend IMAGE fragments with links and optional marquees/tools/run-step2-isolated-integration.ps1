#Requires -Version 7.0
<#
0051 Step 2: dedicated, loopback-only PostgreSQL + MQTT integration fixture.
Consumes the previously accepted 0024 frozen PostgreSQL custom-format backup.
Never connects to pluto or modifies an existing container/database.
#>
[CmdletBinding()]
param([Parameter(Mandatory)][string]$BackupFile)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$feature = Join-Path $repository 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$backup = (Get-Item -LiteralPath $BackupFile -ErrorAction Stop).FullName
if (!(Test-Path -LiteralPath $backup -PathType Leaf)) { throw 'BackupFile is not a regular file.' }
$runId = [guid]::NewGuid().ToString('N').Substring(0,12)
$evidence = Join-Path $feature "evidence/Step 2/private/isolated-integration-$runId"
New-Item -ItemType Directory -Path $evidence -Force | Out-Null
$dbContainer = "diaries-0051-db-$runId"
$mqttContainer = "diaries-0051-mqtt-$runId"
$owned = [Collections.Generic.List[string]]::new()
$names = @('DIARIES_IMAGE_WIRING_TEST_URL','DIARIES_IMAGE_MQTT_TEST_URL','DIARIES_IMAGE_REPOSITORY_TEST_URL','DIARIES_BROWSER_TEST_CLIENT')
$saved = @{}
foreach ($name in $names) { $saved[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
$result = [ordered]@{
  feature='0051'; step=2; runId=$runId; status='RUNNING'
  startedUtc=[DateTime]::UtcNow.ToString('o')
  fixture='disposable localhost containers only'; backupSha256=(Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
}
function Invoke-Checked {
    param([string]$Command,[string[]]$Arguments,[string]$LogName='')
    $output = (& $Command @Arguments 2>&1 | Out-String)
    $exitCode = $LASTEXITCODE
    if ($LogName) { [IO.File]::WriteAllText((Join-Path $evidence $LogName), $output) }
    if ($exitCode -ne 0) { throw "$Command exited $exitCode; see $LogName. $($output.Trim())" }
    return $output.Trim()
}
function Wait-Database {
    $deadline = [DateTime]::UtcNow.AddSeconds(90)
    do {
        & docker exec $dbContainer pg_isready -U diaries -d image_wiring_test *> $null
        if ($LASTEXITCODE -eq 0) { return }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $deadline)
    throw "Disposable database did not become ready: $dbContainer"
}
function Copy-IntoFixture {
    param([string]$Local,[string]$Remote)
    $null = Invoke-Checked docker @('cp',$Local,"${dbContainer}:$Remote")
}
function Psql {
    param([string]$File,[string]$LogName)
    return Invoke-Checked docker @('exec',$dbContainer,'psql','-X','-U','diaries','-d','image_wiring_test','-v','ON_ERROR_STOP=1','-f',$File) $LogName
}

try {
    Write-Host "0051 Step 2 disposable integration: $runId"
    Write-Host "Evidence directory: $evidence"
    # Fail closed if the operator supplies a different dump. Validation is
    # repeated inside the script even when the caller has prechecked the file.
    $expectedFixtureSha256 = 'fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86'
    if ($result.backupSha256 -ne $expectedFixtureSha256) {
      throw 'Frozen 0024 fixture backup SHA-256 mismatch; no fixture containers started.'
    }
    $null = Invoke-Checked git @('-C',$repository,'status','--short') 'git-parent-status.log'
    $null = Invoke-Checked git @('-C',$repository,'branch','--show-current') 'git-parent-branch.log'
    $null = Invoke-Checked git @('-C',$repository,'rev-parse','HEAD') 'git-parent-revision.log'
    $null = Invoke-Checked git @('-C',$repository,'submodule','status') 'git-submodule-revisions.log'
    $responderRoot = Join-Path $repository 'diaries-responder'
    $null = Invoke-Checked git @('-C',$responderRoot,'status','--short') 'git-responder-status.log'
    $null = Invoke-Checked git @('-C',$responderRoot,'branch','--show-current') 'git-responder-branch.log'
    $null = Invoke-Checked git @('-C',$responderRoot,'rev-parse','HEAD') 'git-responder-revision.log'
    $null = Invoke-Checked docker @('info','--format','{{.ServerVersion}}') 'docker-version.log'
    $null = Invoke-Checked docker @('run','--detach','--rm','--name',$dbContainer,
      '--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries',
      '-e','POSTGRES_DB=image_wiring_test','-e','POSTGRES_HOST_AUTH_METHOD=trust',
      '-p','127.0.0.1::5432','postgres:18-alpine') 'postgres-container-id.log'
    $owned.Add($dbContainer)
    $brokerConfig = Join-Path $repository 'scripts/windows/validation/image-catalogue-test-mosquitto.conf'
    if (!(Test-Path -LiteralPath $brokerConfig -PathType Leaf)) { throw 'Permanent disposable MQTT test config not found.' }
    $null = Invoke-Checked docker @('run','--detach','--rm','--name',$mqttContainer,
      '-p','127.0.0.1::1883',
      '--mount',"type=bind,source=$brokerConfig,target=/mosquitto/config/mosquitto.conf,readonly",
      '--entrypoint','mosquitto','eclipse-mosquitto:2.0.22',
      '-c','/mosquitto/config/mosquitto.conf') 'mqtt-container-id.log'
    $owned.Add($mqttContainer)
    Wait-Database
    $null = Copy-IntoFixture $backup '/tmp/baseline.dump'
    $null = Invoke-Checked docker @('exec',$dbContainer,'pg_restore','-U','diaries',
      '-d','image_wiring_test','--no-owner','--no-privileges','/tmp/baseline.dump') 'restore.log'

    $schema0024 = Join-Path $repository 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/migration/schema.sql'
    $migration0025 = Join-Path $repository 'change-control/complete/0025-FEAT - add responder ImageFragment persistence and RPC/migration'
    $migration0051 = Join-Path $feature 'migration'
    Copy-IntoFixture $schema0024 '/tmp/0024-schema.sql'
    Copy-IntoFixture $migration0025 '/tmp/0025-migration'
    Copy-IntoFixture $migration0051 '/tmp/0051-migration'
    $null = Psql '/tmp/0024-schema.sql' '0024-schema.log'
    # 0025 preflight sets psql-local variables (preflight_ok, integrity snapshot,
    # database and user). They are not persisted between docker exec calls.
    # Keep all three files in ONE psql process, as in the accepted 0025 test
    # harness. 002 imports 003 internally; the final explicit 003 checks again
    # after COMMIT while the original preflight variables remain available.
    $null = Invoke-Checked docker @('exec',$dbContainer,'psql','-X','-U','diaries',
      '-d','image_wiring_test','-v','ON_ERROR_STOP=1',
      '-f','/tmp/0025-migration/001-preflight.sql',
      '-f','/tmp/0025-migration/002-add-fragment-image-reference.sql',
      '-f','/tmp/0025-migration/003-postflight.sql') '0025-apply-session.log'

    # All existing values: nullable columns are stripped so adding a null field
    # cannot change these row hashes. No actual user data enters the logs.
    $hashQuery = "SELECT t, md5(coalesce(jsonb_agg(jsonb_strip_nulls(row_data) ORDER BY id)::text,'[]')) FROM (SELECT 'diary' AS t,id,to_jsonb(diary) AS row_data FROM diary UNION ALL SELECT 'page',id,to_jsonb(page) FROM page UNION ALL SELECT 'fragment',id,to_jsonb(fragment) FROM fragment UNION ALL SELECT 'marquee',id,to_jsonb(marquee) FROM marquee UNION ALL SELECT 'image',id,to_jsonb(image) FROM image) s GROUP BY t ORDER BY t"
    $before = Invoke-Checked docker @('exec',$dbContainer,'psql','-X','-q','-t','-A','-U','diaries','-d','image_wiring_test','-c',$hashQuery) 'before-migration-hashes.log'
    $null = Psql '/tmp/0051-migration/001-add-image-link-url.sql' '0051-migrate-first.log'
    $null = Psql '/tmp/0051-migration/001-add-image-link-url.sql' '0051-migrate-second.log'
    $null = Psql '/tmp/0051-migration/002-assert-image-link-schema.sql' '0051-schema-assert.log'
    $after = Invoke-Checked docker @('exec',$dbContainer,'psql','-X','-q','-t','-A','-U','diaries','-d','image_wiring_test','-c',$hashQuery) 'after-migration-hashes.log'
    if ($before -ne $after) { throw 'Migration changed existing diary/page/fragment/marquee/image values.' }
    $result.migrationIdempotent=$true
    $result.existingValuesPreserved=$true

    $dbPort = Invoke-Checked docker @('port',$dbContainer,'5432') 'db-port.log'
    $mqttPort = Invoke-Checked docker @('port',$mqttContainer,'1883') 'mqtt-port.log'
    if ($dbPort -notmatch '^127\.0\.0\.1:[0-9]+$' -or $mqttPort -notmatch '^127\.0\.0\.1:[0-9]+$') {
      throw 'Fixture ports are not bound exclusively to 127.0.0.1.'
    }
    $env:DIARIES_IMAGE_WIRING_TEST_URL = "jdbc:postgresql://$dbPort/image_wiring_test"
    $env:DIARIES_IMAGE_MQTT_TEST_URL = "tcp://$mqttPort"
    Remove-Item Env:DIARIES_IMAGE_REPOSITORY_TEST_URL -ErrorAction SilentlyContinue
    Remove-Item Env:DIARIES_BROWSER_TEST_CLIENT -ErrorAction SilentlyContinue

    # Opt-in tests only; the selected legacy baseline checks are not rerun.
    $gradlew = Join-Path $repository 'gradlew.bat'
    $null = Invoke-Checked $gradlew @('-p',$repository,'--no-daemon',
      ':diaries-responder:test','--rerun-tasks','--console=plain',
      '--tests','com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.imageLinkAndOptionalMarqueeRoundTripOverRpc',
      '--tests','com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.liveImageFragmentRpcAndRestartReplay') 'step2-integration-gradle.log'

    $junit = Join-Path $repository 'diaries-responder/build/test-results/test/TEST-com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.xml'
    if (!(Test-Path -LiteralPath $junit)) { throw 'JUnit XML is missing.' }
    Copy-Item -LiteralPath $junit -Destination (Join-Path $evidence 'ImageWiringIntegrationTest.xml')
    [xml]$suite = Get-Content -LiteralPath $junit -Raw
    $tests=[int]$suite.testsuite.tests
    $skipped=[int]$suite.testsuite.skipped
    $failures=[int]$suite.testsuite.failures
    $errors=[int]$suite.testsuite.errors
    if ($tests -ne 2 -or $skipped -ne 0 -or $failures -ne 0 -or $errors -ne 0) {
      throw "JUnit integration gate not met: tests=$tests skipped=$skipped failures=$failures errors=$errors"
    }
    $result.junit=[ordered]@{tests=$tests;skipped=$skipped;failures=$failures;errors=$errors}
    $result.status='PASSED'
    Write-Host 'PASS: Migration twice, schema assertion, unchanged data hashes, and 2 actual PostgreSQL/MQTT integration tests.'
} catch {
    $result.status='FAILED'
    $result.failure=$_.Exception.Message
    Write-Host "FAIL: $($result.failure)"
} finally {
    $cleanupFailures=@()
    foreach ($name in $owned) {
        & docker stop $name *> $null
        if ($LASTEXITCODE -ne 0) { $cleanupFailures += $name }
    }
    foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name,$saved[$name],'Process') }
    if ($cleanupFailures.Count) { $result.status='CLEANUP_FAILED';$result.cleanupFailures=$cleanupFailures }
    $result.finishedUtc=[DateTime]::UtcNow.ToString('o')
    [IO.File]::WriteAllText((Join-Path $evidence 'result.json'),($result | ConvertTo-Json -Depth 8))
    $hashes = @(Get-ChildItem -LiteralPath $evidence -File | Where-Object Name -ne 'SHA256SUMS.txt' | Sort-Object Name | ForEach-Object {
        (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()+'  '+$_.Name
    })
    [IO.File]::WriteAllLines((Join-Path $evidence 'SHA256SUMS.txt'),$hashes)
    Write-Host "Result: $($result.status)"
    Write-Host "Evidence: $evidence"
}
if ($result.status -ne 'PASSED') { exit 1 }
