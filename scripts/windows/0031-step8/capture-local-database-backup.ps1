param(
    [string]$EvidenceDirectory
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir '..\..\..'))
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'

if ([string]::IsNullOrWhiteSpace($EvidenceDirectory)) {
    $EvidenceDirectory = Join-Path $ProjectDir "change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 8\runtime"
}
$EvidenceDirectory = [System.IO.Path]::GetFullPath($EvidenceDirectory)
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
$EvidenceFile = Join-Path $EvidenceDirectory "local-database-backup-$Timestamp.txt"

$ModeByDatabaseContainer = [ordered]@{
    'diaries-development-db'    = 'development-infrastructure'
    'diaries-local-db'          = 'local-docker-build'
    'diaries-published-smoke-db'= 'local-published-smoke'
}
$KnownResponderContainers = @('diaries-local-responder', 'diaries-published-smoke-responder')

function Write-Evidence {
    param([string]$Message = '')
    $Message | Tee-Object -FilePath $EvidenceFile -Append
}

function Read-DotEnv {
    param([Parameter(Mandatory = $true)][string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw "Environment file does not exist: $Path" }
    $values = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = [string]$raw
        $trimmed = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trimmed) -or $trimmed.StartsWith('#')) { continue }
        $equals = $line.IndexOf('=')
        if ($equals -lt 1) { continue }
        $key = $line.Substring(0, $equals).Trim()
        $value = $line.Substring($equals + 1).Trim()
        $values[$key] = $value
    }
    return $values
}

function Merge-DotEnv {
    param([hashtable]$Base, [hashtable]$Override)
    $result = @{}
    foreach ($key in $Base.Keys) { $result[$key] = $Base[$key] }
    foreach ($key in $Override.Keys) { $result[$key] = $Override[$key] }
    return $result
}


function Get-TcpListeners {
    param([Parameter(Mandatory = $true)][int]$Port)
    try {
        return @(
            [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() |
                Where-Object { $_.Port -eq $Port }
        )
    } catch {
        throw "Unable to query TCP/$Port listeners using the .NET network-information API: $($_.Exception.Message)"
    }
}

function Get-RunningContainerNames {
    $output = & docker ps --format '{{.Names}}' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "docker ps failed: $($output -join [Environment]::NewLine)" }
    return @($output | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

Write-Evidence '0031-FEAT Step 8 - local pre-migration database backup'
Write-Evidence "Captured: $(Get-Date -Format o)"
Write-Evidence "Host: $env:COMPUTERNAME"
Write-Evidence "Project: $ProjectDir"
Write-Evidence

$running = Get-RunningContainerNames
foreach ($container in $KnownResponderContainers) {
    if ($running -contains $container) {
        throw "Local responder container '$container' is running. Run freeze-local-writes.bat before taking the Step 8 backup."
    }
}
$listeners = @(Get-TcpListeners -Port 8081)
if ($listeners.Count -gt 0) {
    throw 'TCP/8081 is listening. Stop the direct/local responder and rerun the Step 8 write freeze before backing up.'
}

$runningDatabases = @()
foreach ($container in $ModeByDatabaseContainer.Keys) {
    if ($running -contains $container) { $runningDatabases += $container }
}
if ($runningDatabases.Count -ne 1) {
    throw "Exactly one local Diaries database container must be running; found $($runningDatabases.Count): $($runningDatabases -join ', '). Start only the local mode whose effective dataset is being backed up."
}

$dbContainer = $runningDatabases[0]
$mode = $ModeByDatabaseContainer[$dbContainer]
$modeEnvPath = Join-Path $ProjectDir "config\environments\$mode.env"
$localEnvPath = Join-Path $ProjectDir 'config\environments\local.env'
$modeEnv = Read-DotEnv $modeEnvPath
$localEnv = Read-DotEnv $localEnvPath
$effective = Merge-DotEnv $modeEnv $localEnv

if (-not $effective.ContainsKey('DIARIES_DB_DATA_DIR') -or [string]::IsNullOrWhiteSpace([string]$effective['DIARIES_DB_DATA_DIR'])) {
    throw 'Effective DIARIES_DB_DATA_DIR is missing.'
}
if (-not $effective.ContainsKey('DIARIES_FILES_DIR') -or [string]::IsNullOrWhiteSpace([string]$effective['DIARIES_FILES_DIR'])) {
    throw 'Effective DIARIES_FILES_DIR is missing.'
}

$validator = Join-Path $ProjectDir 'scripts\windows\common\validate-dataset-pair.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $validator -ModeName $mode -ModeEnvironmentFile $modeEnvPath -LocalEnvironmentFile $localEnvPath
if ($LASTEXITCODE -ne 0) { throw 'Effective local database/Files pair failed the 0031 guard.' }

$dbPath = if ([System.IO.Path]::IsPathRooted([string]$effective['DIARIES_DB_DATA_DIR'])) {
    [System.IO.Path]::GetFullPath([string]$effective['DIARIES_DB_DATA_DIR'])
} else {
    [System.IO.Path]::GetFullPath((Join-Path $ProjectDir ([string]$effective['DIARIES_DB_DATA_DIR'])))
}
$datasetName = Split-Path -Leaf $dbPath
if ([string]::IsNullOrWhiteSpace($datasetName)) { throw 'Unable to derive the effective local dataset name.' }

# The Step 8 source tree is the frozen pre-split shared directory named "files".
# This is intentionally distinct from the Step 2/3 target selector now present in
# local.env (normally files-development-common).
$dockerModeDefaults = Read-DotEnv (Join-Path $ProjectDir 'config\environments\local-docker-build.env')
$nasEffective = Merge-DotEnv $dockerModeDefaults $localEnv
foreach ($key in 'DIARIES_NAS_HOST','DIARIES_NAS_SHARE','DIARIES_NAS_CONTENT_PATH') {
    if (-not $nasEffective.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$nasEffective[$key])) {
        throw "$key is required to record the frozen pre-migration shared Files root."
    }
}
$contentPath = ([string]$nasEffective['DIARIES_NAS_CONTENT_PATH']).Replace('/', '\').Trim('\')
$sharedFilesRoot = "\\$($nasEffective['DIARIES_NAS_HOST'])\$($nasEffective['DIARIES_NAS_SHARE'])\$contentPath\files"

$backupName = "diaries-$datasetName-step8-premigration-$Timestamp.dump"
$backupScript = Join-Path $ProjectDir "scripts\windows\$mode\backup-db-to-binary.bat"
if (-not (Test-Path -LiteralPath $backupScript -PathType Leaf)) { throw "Backup script not found: $backupScript" }

Write-Evidence "Running database container: $dbContainer"
Write-Evidence "Launch mode: $mode"
Write-Evidence "Effective dataset: $datasetName"
Write-Evidence "Effective database data: $dbPath"
Write-Evidence "Configured target Files selector: $($effective['DIARIES_FILES_DIR'])"
Write-Evidence "Pre-migration shared Files selector: files"
Write-Evidence "Pre-migration shared Files root: $sharedFilesRoot"
Write-Evidence 'Mutable-write check: PASS (no known local responder and no TCP/8081 listener).'
Write-Evidence

$backupOutput = & $backupScript $backupName 2>&1
$backupExit = $LASTEXITCODE
$backupOutput | ForEach-Object { Write-Evidence ([string]$_) }
if ($backupExit -ne 0) { throw "Database backup script failed with exit code $backupExit." }

$backupFile = Join-Path $ProjectDir "data\database-backups\$datasetName\$backupName"
$sidecarFile = "$backupFile.dataset.json"
if (-not (Test-Path -LiteralPath $backupFile -PathType Leaf)) { throw "Expected database backup was not created: $backupFile" }
if (-not (Test-Path -LiteralPath $sidecarFile -PathType Leaf)) { throw "Expected Step 7 sidecar was not created: $sidecarFile" }

$backupHash = (Get-FileHash -LiteralPath $backupFile -Algorithm SHA256).Hash.ToLowerInvariant()
$sidecarHash = (Get-FileHash -LiteralPath $sidecarFile -Algorithm SHA256).Hash.ToLowerInvariant()
$manifest = Get-Content -LiteralPath $sidecarFile -Raw | ConvertFrom-Json

$gitCommit = 'unknown'
try {
    $candidate = (& git -C $ProjectDir rev-parse HEAD 2>$null | Select-Object -First 1)
    if (-not [string]::IsNullOrWhiteSpace($candidate)) { $gitCommit = $candidate.Trim() }
} catch { }

$step8Manifest = [ordered]@{
    schemaVersion = 1
    captureType = '0031-step8-local-pre-migration-database'
    createdAt = (Get-Date).ToString('o')
    host = $env:COMPUTERNAME
    launchMode = $mode
    logicalDataset = $datasetName
    effectiveDatabaseDataDir = $dbPath
    configuredTargetFilesDir = [string]$effective['DIARIES_FILES_DIR']
    preMigrationSharedFilesDir = 'files'
    preMigrationSharedFilesRoot = $sharedFilesRoot
    databaseBackupFile = $backupFile
    databaseBackupSha256 = $backupHash
    databaseSidecarFile = $sidecarFile
    databaseSidecarSha256 = $sidecarHash
    imageRowCount = [string]$manifest.imageRowCount
    applicationSourceIdentity = [ordered]@{ gitCommit = $gitCommit }
    writeFreeze = [ordered]@{
        knownDockerRespondersStopped = $true
        tcp8081ListenerAbsent = $true
    }
    note = 'The Step-7 sidecar records the currently configured target Files selector. Step 8 separately records the pre-migration shared Files root whose snapshot must be preserved with this database backup for rollback.'
}
$step8ManifestPath = Join-Path $EvidenceDirectory "local-database-backup-$datasetName-$Timestamp.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($step8ManifestPath, (($step8Manifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine), $utf8NoBom)

Write-Evidence
Write-Evidence 'PASS: local pre-migration database backup captured and hashed.'
Write-Evidence "Database backup: $backupFile"
Write-Evidence "Database SHA-256: $backupHash"
Write-Evidence "Step-7 sidecar: $sidecarFile"
Write-Evidence "Step-8 manifest: $step8ManifestPath"
if ($datasetName -eq 'common') {
    Write-Evidence 'Dataset sharing: this one backup represents all three local launch modes when local.env selects the common dataset.'
}
Write-Evidence 'The shared Files bytes are NOT captured by this script; run capture-shared-files-snapshot.bat only after production writes are also frozen.'
