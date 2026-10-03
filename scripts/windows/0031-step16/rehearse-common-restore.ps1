[CmdletBinding()]
param(
    [string]$Step8Dump = '',
    [string]$BaseConfig = '',
    [string]$OutputRoot = '',
    [string]$PostgresImage = 'postgres:18-alpine'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ExpectedDumpSha256 = 'd1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7'
$ExpectedImageCount = 85
$DisposablePassword = 'step16-rehearsal-only'

function Fail([string]$Message) {
    throw "0031 Step 16 restore rehearsal: $Message"
}

function Read-DotEnv([string]$Path, [hashtable]$Values) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { Fail "environment file not found: $Path" }
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#') -or $line.IndexOf('=') -lt 1) { continue }
        $parts = $line.Split('=', 2)
        $Values[$parts[0].Trim()] = $parts[1].Trim()
    }
}

function Invoke-Docker([string[]]$Arguments, [switch]$AllowFailure) {
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        # Windows PowerShell 5.1 converts redirected native stderr to ErrorRecord
        # objects.  Native diagnostics are therefore captured under Continue and
        # success/failure is decided from LASTEXITCODE instead.
        $ErrorActionPreference = 'Continue'
        $output = & docker @Arguments 2>&1
        $rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
    }
    if (-not $AllowFailure -and $rc -ne 0) {
        Fail "docker $($Arguments -join ' ') failed with exit code ${rc}: $($output -join [Environment]::NewLine)"
    }
    return [pscustomobject]@{ ExitCode = $rc; Output = @($output) }
}

function Test-LocalResponderStopped {
    $known = @('diaries-local-responder','diaries-published-smoke-responder')
    $psResult = Invoke-Docker -Arguments @('ps','--format','{{.Names}}')
    $running = @($psResult.Output)
    foreach ($name in $known) {
        if ($running -contains $name) { Fail "local responder container '$name' is running. Stop local responders before the read-only restore rehearsal." }
    }
    $listeners = [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners()
    if ($listeners | Where-Object { $_.Port -eq 8081 }) {
        Fail 'TCP/8081 is listening, normally indicating the direct Windows responder is active. Stop it before the restore rehearsal.'
    }
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..\..\..')).Path
$featureDir = Join-Path $projectRoot 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$step16Dir = Join-Path $featureDir 'evidence\Step 16'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $OutputRoot) { $OutputRoot = Join-Path $step16Dir 'runtime' }
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$runDir = Join-Path $OutputRoot "restore-rehearsal-$timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null
$reconciliation = Join-Path $runDir 'reconciliation'
New-Item -ItemType Directory -Force -Path $reconciliation | Out-Null

if (-not $Step8Dump) {
    $Step8Dump = Join-Path $projectRoot 'data\database-backups\common\diaries-common-step8-premigration-20261002-142614.dump'
}
if (-not (Test-Path -LiteralPath $Step8Dump -PathType Leaf)) {
    Fail "Step 8 common database backup not found: $Step8Dump. Pass -Step8Dump with the preserved Step 8 dump path."
}
$Step8Dump = (Resolve-Path -LiteralPath $Step8Dump).Path
$dumpSha = (Get-FileHash -LiteralPath $Step8Dump -Algorithm SHA256).Hash.ToLowerInvariant()
if ($dumpSha -ne $ExpectedDumpSha256) {
    Fail "Step 8 dump SHA-256 mismatch. Expected $ExpectedDumpSha256 but found $dumpSha."
}

if (-not $BaseConfig) { $BaseConfig = Join-Path $env:USERPROFILE '.diaries\responder.json' }
if (-not (Test-Path -LiteralPath $BaseConfig -PathType Leaf)) { Fail "developer responder config not found: $BaseConfig" }
$BaseConfig = (Resolve-Path -LiteralPath $BaseConfig).Path

$effective = @{}
Read-DotEnv (Join-Path $projectRoot 'config\environments\development-infrastructure.env') $effective
$localEnv = Join-Path $projectRoot 'config\environments\local.env'
if (-not (Test-Path -LiteralPath $localEnv -PathType Leaf)) {
    Fail "the ignored local.env is required for this rehearsal and must select the normal common pair: $localEnv"
}
Read-DotEnv $localEnv $effective
if ([string]$effective['DIARIES_DB_DATA_DIR'] -ne './data/database/common' -or [string]$effective['DIARIES_FILES_DIR'] -ne 'files-development-common') {
    Fail "normal common pair is not selected. Expected ./data/database/common + files-development-common; found '$($effective['DIARIES_DB_DATA_DIR'])' + '$($effective['DIARIES_FILES_DIR'])'."
}

# Reuse the same fail-fast pair validator as supported local launch tooling.
$validator = Join-Path $projectRoot 'scripts\windows\common\validate-dataset-pair.ps1'
$savedErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & powershell -NoProfile -ExecutionPolicy Bypass -File $validator `
        -ModeName development-infrastructure `
        -ModeEnvironmentFile (Join-Path $projectRoot 'config\environments\development-infrastructure.env') `
        -LocalEnvironmentFile $localEnv *> (Join-Path $runDir 'PAIR-VALIDATION.txt')
    $pairExit = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $savedErrorActionPreference
}
if ($pairExit -ne 0) { Fail 'effective common pair failed the shared dataset-pair validator.' }

Test-LocalResponderStopped

$base = Get-Content -LiteralPath $BaseConfig -Raw | ConvertFrom-Json
if (-not $base.diaries -or [string]::IsNullOrWhiteSpace([string]$base.diaries.root)) { Fail 'base responder config does not define diaries.root.' }
if (-not $base.db -or -not $base.db.jdbc) { Fail 'base responder config does not define db.jdbc.' }
$filesRoot = Join-Path ([string]$base.diaries.root) 'files-development-common'
if (-not (Test-Path -LiteralPath $filesRoot -PathType Container)) { Fail "common Files root does not exist: $filesRoot" }
$filesRoot = (Resolve-Path -LiteralPath $filesRoot).Path

$container = "diaries-0031-step16-restore-$timestamp"
$configFile = Join-Path $runDir 'REHEARSAL-CONFIG.json'
$containerStarted = $false
try {
    $run = Invoke-Docker -Arguments @(
        'run','-d','--rm','--name',$container,
        '-e','POSTGRES_DB=diaries',
        '-e','POSTGRES_USER=diaries',
        '-e',"POSTGRES_PASSWORD=$DisposablePassword",
        '-p','127.0.0.1::5432',
        $PostgresImage
    )
    $containerStarted = $true
    $run.Output | Set-Content -LiteralPath (Join-Path $runDir 'DOCKER-CONTAINER.txt') -Encoding ASCII

    $ready = $false
    for ($i = 0; $i -lt 60; $i++) {
        Start-Sleep -Seconds 1
        $probe = Invoke-Docker -Arguments @('exec',$container,'pg_isready','-U','diaries','-d','diaries') -AllowFailure
        if ($probe.ExitCode -eq 0) { $ready = $true; break }
    }
    if (-not $ready) { Fail 'disposable PostgreSQL did not become ready.' }

    $portResult = Invoke-Docker -Arguments @('port',$container,'5432/tcp')
    $portLine = [string]($portResult.Output | Select-Object -First 1)
    if ($portLine -notmatch ':(\d+)\s*$') { Fail "cannot parse disposable PostgreSQL host port from '$portLine'." }
    $hostPort = [int]$matches[1]

    Invoke-Docker -Arguments @('cp',$Step8Dump,"${container}:/tmp/step8.dump") | Out-Null
    $restore = Invoke-Docker -Arguments @('exec',$container,'pg_restore','-U','diaries','-d','diaries','--no-owner','--no-privileges','/tmp/step8.dump')
    $restore.Output | Set-Content -LiteralPath (Join-Path $runDir 'PG-RESTORE.txt') -Encoding UTF8

    $minimal = [ordered]@{
        db = [ordered]@{
            jdbc = [ordered]@{
                dbms = [string]$base.db.jdbc.dbms
                driver = [string]$base.db.jdbc.driver
            }
            additionalConnectionProperties = [ordered]@{
                'hibernate.hbm2ddl.auto' = 'validate'
                'jakarta.persistence.schema-generation.database.action' = 'none'
            }
            host = '127.0.0.1'
            port = $hostPort
            database = 'diaries'
            admin = [ordered]@{ username = 'diaries'; password = $DisposablePassword }
            users = @([ordered]@{ username = 'diaries'; password = $DisposablePassword })
        }
        diaries = [ordered]@{
            root = [string]$base.diaries.root
            files = 'files-development-common'
        }
    }
    $minimal | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $configFile -Encoding UTF8

    $gradle = Join-Path $projectRoot 'gradlew.bat'
    Push-Location $projectRoot
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        # Gradle/SLF4J may write informational diagnostics to stderr even when the
        # task succeeds.  Capture them as evidence and judge Gradle by LASTEXITCODE.
        $ErrorActionPreference = 'Continue'
        & $gradle ':diaries-responder:migration0024ImageCatalogue' `
            "-PmigrationConfig=$configFile" `
            "-PmigrationOutput=$reconciliation" `
            '-PmigrationMode=dry-run' `
            '--console=plain' 2>&1 | Tee-Object -FilePath (Join-Path $runDir 'RECONCILIATION-CONSOLE.txt')
        $gradleExit = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        Pop-Location
    }
    if ($gradleExit -ne 0) { Fail "0024 read-only reconciliation against restored Step 8 database failed with exit code $gradleExit." }

    $summaryPath = Join-Path $reconciliation '0024-summary.json'
    $conflictsPath = Join-Path $reconciliation '0024-conflicts.csv'
    if (-not (Test-Path -LiteralPath $summaryPath -PathType Leaf)) { Fail 'reconciliation summary was not produced.' }
    if (-not (Test-Path -LiteralPath $conflictsPath -PathType Leaf)) { Fail 'reconciliation conflicts CSV was not produced.' }
    $summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
    if ([string]$summary.outcome -ne 'DRY_RUN_COMPLETE') { Fail "unexpected reconciliation outcome: $($summary.outcome)" }
    $matchCount = 0
    if ($summary.counts.PSObject.Properties['CATALOGUED_MATCH']) { $matchCount = [int]$summary.counts.CATALOGUED_MATCH }
    if ($matchCount -ne $ExpectedImageCount) { Fail "restored Step 8 database expected $ExpectedImageCount CATALOGUED_MATCH rows; found $matchCount." }
    $badStatuses = @()
    foreach ($property in $summary.counts.PSObject.Properties) {
        if ($property.Name -notin @('CATALOGUED_MATCH','DIRECTORY','UNSUPPORTED') -and [int64]$property.Value -ne 0) {
            $badStatuses += "$($property.Name)=$($property.Value)"
        }
    }
    if ($badStatuses.Count -gt 0) { Fail "reconciliation contains unsafe statuses: $($badStatuses -join ', ')" }
    $conflictLines = @(Get-Content -LiteralPath $conflictsPath)
    if ($conflictLines.Count -gt 1) { Fail "reconciliation conflicts CSV contains $($conflictLines.Count - 1) data rows." }

    $result = [ordered]@{
        schemaVersion = 1
        feature = '0031-FEAT'
        step = 16
        status = 'PASSED'
        rehearsal = 'disposable restore of Step 8 local common PostgreSQL backup plus read-only 0024 reconciliation'
        capturedAt = (Get-Date).ToUniversalTime().ToString('o')
        step8Dump = $Step8Dump
        step8DumpSha256 = $dumpSha
        expectedStep8DumpSha256 = $ExpectedDumpSha256
        effectiveDbDataDir = './data/database/common'
        effectiveFilesDir = 'files-development-common'
        physicalFilesRoot = $filesRoot
        restoredDatabase = 'disposable Docker PostgreSQL; live local database not modified'
        reconciliationOutcome = [string]$summary.outcome
        reconciliationCounts = $summary.counts
        expectedCatalogueMatches = $ExpectedImageCount
        conflicts = 0
        publicFilesRoute = '/files/... unchanged; no browser namespace is derived from physical selector'
    }
    $result | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $runDir 'RESTORE-REHEARSAL-SUMMARY.json') -Encoding UTF8

    # Do not preserve even the disposable password in permanent evidence.
    Remove-Item -LiteralPath $configFile -Force

    $latest = Join-Path $step16Dir 'LATEST-RESTORE-REHEARSAL.txt'
    $runDir | Set-Content -LiteralPath $latest -Encoding ASCII

    Write-Host ''
    Write-Host 'PASS: Step 16 disposable common-dataset restore/reconciliation rehearsal succeeded.'
    Write-Host "Step 8 backup: $Step8Dump"
    Write-Host "Files root: $filesRoot"
    Write-Host "Evidence: $runDir"
}
finally {
    if (Test-Path -LiteralPath $configFile -PathType Leaf) {
        Remove-Item -LiteralPath $configFile -Force -ErrorAction SilentlyContinue
    }
    if ($containerStarted) {
        Invoke-Docker -Arguments @('rm','-f',$container) -AllowFailure | Out-Null
    }
}
