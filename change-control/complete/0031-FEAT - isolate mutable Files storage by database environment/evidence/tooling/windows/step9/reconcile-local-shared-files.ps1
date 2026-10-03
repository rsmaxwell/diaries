param(
    [string]$EvidenceDirectory,
    [string]$SharedFilesDir = 'files'
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir '..\..\..'))
$Timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$FeatureDir = Join-Path $ProjectDir 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$Step9Runtime = Join-Path $FeatureDir 'evidence\Step 9\runtime'

if ([string]::IsNullOrWhiteSpace($EvidenceDirectory)) {
    $EvidenceDirectory = $Step9Runtime
}
$EvidenceDirectory = [System.IO.Path]::GetFullPath($EvidenceDirectory)
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null

if ($SharedFilesDir -ne 'files') {
    throw "Step 9 is defined against the frozen pre-split shared Files selector 'files'; refusing selector '$SharedFilesDir'."
}

$KnownResponderContainers = @('diaries-local-responder', 'diaries-published-smoke-responder')
$ModeByDatabaseContainer = [ordered]@{
    'diaries-development-db'     = 'development-infrastructure'
    'diaries-local-db'           = 'local-docker-build'
    'diaries-published-smoke-db' = 'local-published-smoke'
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
    return @(
        [System.Net.NetworkInformation.IPGlobalProperties]::GetIPGlobalProperties().GetActiveTcpListeners() |
            Where-Object { $_.Port -eq $Port }
    )
}

function Get-RunningContainerNames {
    $output = & docker ps --format '{{.Names}}' 2>&1
    if ($LASTEXITCODE -ne 0) { throw "docker ps failed: $($output -join [Environment]::NewLine)" }
    return @($output | ForEach-Object { [string]$_ } | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
}

function Get-Count {
    param([object]$Counts, [string]$Name)
    if ($null -eq $Counts) { return 0 }
    $property = $Counts.PSObject.Properties[$Name]
    if ($null -eq $property) { return 0 }
    return [int64]$property.Value
}

function Write-JsonNoBom {
    param([Parameter(Mandatory = $true)]$Value, [Parameter(Mandatory = $true)][string]$Path)
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path, (($Value | ConvertTo-Json -Depth 20) + [Environment]::NewLine), $utf8NoBom)
}

$running = Get-RunningContainerNames
foreach ($container in $KnownResponderContainers) {
    if ($running -contains $container) {
        throw "Local responder container '$container' is running. Step 9 must preserve the Step 8 write freeze."
    }
}
if (@(Get-TcpListeners -Port 8081).Count -gt 0) {
    throw 'TCP/8081 is listening. Stop the direct/local responder before Step 9 reconciliation.'
}

$runningDatabases = @()
foreach ($container in $ModeByDatabaseContainer.Keys) {
    if ($running -contains $container) { $runningDatabases += $container }
}
if ($runningDatabases.Count -ne 1) {
    throw "Exactly one local Diaries database container must be running; found $($runningDatabases.Count): $($runningDatabases -join ', ')."
}

$dbContainer = $runningDatabases[0]
$mode = $ModeByDatabaseContainer[$dbContainer]
$modeEnvPath = Join-Path $ProjectDir "config\environments\$mode.env"
$localEnvPath = Join-Path $ProjectDir 'config\environments\local.env'
$modeEnv = Read-DotEnv $modeEnvPath
$localEnv = Read-DotEnv $localEnvPath
$effective = Merge-DotEnv $modeEnv $localEnv

foreach ($key in 'DIARIES_DB_DATA_DIR','DIARIES_FILES_DIR') {
    if (-not $effective.ContainsKey($key) -or [string]::IsNullOrWhiteSpace([string]$effective[$key])) {
        throw "Effective $key is missing."
    }
}

$validator = Join-Path $ProjectDir 'scripts\windows\common\validate-dataset-pair.ps1'
& powershell -NoProfile -ExecutionPolicy Bypass -File $validator -ModeName $mode -ModeEnvironmentFile $modeEnvPath -LocalEnvironmentFile $localEnvPath
if ($LASTEXITCODE -ne 0) { throw 'The normal effective local database/Files target pair failed the 0031 guard.' }

$dbPath = if ([System.IO.Path]::IsPathRooted([string]$effective['DIARIES_DB_DATA_DIR'])) {
    [System.IO.Path]::GetFullPath([string]$effective['DIARIES_DB_DATA_DIR'])
} else {
    [System.IO.Path]::GetFullPath((Join-Path $ProjectDir ([string]$effective['DIARIES_DB_DATA_DIR'])))
}
$datasetName = Split-Path -Leaf $dbPath
if ([string]::IsNullOrWhiteSpace($datasetName)) { throw 'Unable to derive effective local dataset name.' }

# Step 9 starts from the same generated/effective direct-development config
# used by Step 4. A second temporary config changes only diaries.files back to
# the frozen pre-split source selector. local.env is not changed.
$prepareBat = Join-Path $ProjectDir 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
$preparePs1 = Join-Path $ProjectDir 'scripts\windows\development-infrastructure\prepare-responder-config.ps1'
$prepareOutput = & $prepareBat 2>&1
$prepareExit = $LASTEXITCODE
$prepareOutput | ForEach-Object { Write-Host ([string]$_) }
if ($prepareExit -ne 0) { throw "Step 4 effective responder configuration preparation failed with exit code $prepareExit." }

$effectiveConfig = Join-Path $ProjectDir 'build\development-infrastructure\responder.effective.json'
if (-not (Test-Path -LiteralPath $effectiveConfig -PathType Leaf)) {
    throw "Expected Step 4 generated responder configuration was not created: $effectiveConfig"
}

$step9BuildDir = Join-Path $ProjectDir 'build\0031-step9'
New-Item -ItemType Directory -Force -Path $step9BuildDir | Out-Null
$step9Config = Join-Path $step9BuildDir 'responder.shared-files.json'
$sharedFilesRoot = (& powershell -NoProfile -ExecutionPolicy Bypass -File $preparePs1 -BaseConfig $effectiveConfig -OutputConfig $step9Config -FilesDir $SharedFilesDir | Select-Object -Last 1)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace([string]$sharedFilesRoot)) {
    throw 'Could not generate the Step 9 temporary shared-Files responder configuration.'
}
$sharedFilesRoot = [string]$sharedFilesRoot
if (-not (Test-Path -LiteralPath $sharedFilesRoot -PathType Container)) {
    throw "Frozen pre-split shared Files root does not exist: $sharedFilesRoot"
}

$runDir = Join-Path $EvidenceDirectory "local-$datasetName-$Timestamp"
$reconciliationDir = Join-Path $runDir 'reconciliation'
New-Item -ItemType Directory -Force -Path $reconciliationDir | Out-Null

$gradle = Join-Path $ProjectDir 'gradlew.bat'
if (-not (Test-Path -LiteralPath $gradle -PathType Leaf)) { throw "Gradle wrapper not found: $gradle" }

Write-Host
Write-Host '0031-FEAT Step 9 - local shared-Files reconciliation'
Write-Host "Launch mode:              $mode"
Write-Host "Effective dataset:        $datasetName"
Write-Host "Effective database data:  $dbPath"
Write-Host "Configured target Files:  $($effective['DIARIES_FILES_DIR'])"
Write-Host "Reconciled source Files:  $SharedFilesDir"
Write-Host "Physical source root:     $sharedFilesRoot"
Write-Host "Evidence:                 $runDir"
Write-Host
Write-Host 'Running existing 0024 reconciliation in DRY-RUN mode only...'

& $gradle ':diaries-responder:migration0024ImageCatalogue' "-PmigrationConfig=$step9Config" "-PmigrationOutput=$reconciliationDir" '-PmigrationMode=dry-run'
if ($LASTEXITCODE -ne 0) { throw "0024 dry-run reconciliation failed with exit code $LASTEXITCODE. Inspect $reconciliationDir" }

$summaryPath = Join-Path $reconciliationDir '0024-summary.json'
$planPath = Join-Path $reconciliationDir '0024-create-plan.json'
$conflictsPath = Join-Path $reconciliationDir '0024-conflicts.csv'
foreach ($path in $summaryPath,$planPath,$conflictsPath) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Expected reconciliation evidence is missing: $path" }
}

$summary = Get-Content -LiteralPath $summaryPath -Raw | ConvertFrom-Json
$plan = Get-Content -LiteralPath $planPath -Raw | ConvertFrom-Json
$conflicts = @(Import-Csv -LiteralPath $conflictsPath)

$stagingRoot = Join-Path $sharedFilesRoot '.image-staging'
$stagingInventoryPath = Join-Path $runDir 'STAGING-INVENTORY.tsv'
$stagingRows = @()
if (Test-Path -LiteralPath $stagingRoot -PathType Container) {
    foreach ($file in Get-ChildItem -LiteralPath $stagingRoot -Force -Recurse -File | Sort-Object FullName) {
        $rootPrefix = $sharedFilesRoot.TrimEnd('\')
        $relative = $file.FullName.Substring($rootPrefix.Length).TrimStart('\').Replace('\','/')
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        $stagingRows += [pscustomobject]@{ relativePath = $relative; size = [int64]$file.Length; sha256 = $hash }
    }
}
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
$stagingLines = @("relativePath`tsize`tsha256")
foreach ($row in $stagingRows) { $stagingLines += "$($row.relativePath)`t$($row.size)`t$($row.sha256)" }
[System.IO.File]::WriteAllLines($stagingInventoryPath, $stagingLines, $utf8NoBom)

$counts = $summary.counts
$cataloguedRows = @($plan.baselineRows).Count
$matching = Get-Count $counts 'CATALOGUED_MATCH'
$missing = Get-Count $counts 'DATABASE_ROW_MISSING_FILE'
$untracked = Get-Count $counts 'CREATE_MISSING'
$metadataConflicts = Get-Count $counts 'CATALOGUED_METADATA_CONFLICT'
$unsupported = Get-Count $counts 'UNSUPPORTED'
$untrackedPhysical = $untracked + $unsupported
$stagingMeasure = $stagingRows | Measure-Object -Property size -Sum
$stagingBytes = if ($null -eq $stagingMeasure.Sum) { [int64]0 } else { [int64]$stagingMeasure.Sum }
$requiresReview = ($missing -gt 0 -or $untrackedPhysical -gt 0 -or $metadataConflicts -gt 0 -or $conflicts.Count -gt 0 -or $stagingRows.Count -gt 0)

$gitCommit = 'unknown'
try {
    $candidate = (& git -C $ProjectDir rev-parse HEAD 2>$null | Select-Object -First 1)
    if (-not [string]::IsNullOrWhiteSpace([string]$candidate)) { $gitCommit = ([string]$candidate).Trim() }
} catch { }

$report = [ordered]@{
    schemaVersion = 1
    feature = '0031-FEAT'
    step = 9
    reconciliationType = 'pre-split-read-only'
    createdAt = (Get-Date).ToString('o')
    applicationSourceIdentity = [ordered]@{ gitCommit = $gitCommit }
    launchMode = $mode
    logicalDataset = $datasetName
    databaseContainer = $dbContainer
    effectiveDatabaseDataDir = $dbPath
    configuredTargetFilesDir = [string]$effective['DIARIES_FILES_DIR']
    reconciledSharedFilesDir = $SharedFilesDir
    reconciledSharedFilesRoot = $sharedFilesRoot
    databaseIdentity = [string]$summary.databaseIdentity
    reconciliationOutcome = [string]$summary.outcome
    catalogue = [ordered]@{
        imageRowCount = $cataloguedRows
        matchingPhysicalFiles = $matching
        missingPhysicalFiles = $missing
        untrackedPhysicalFiles = $untrackedPhysical
        untrackedSupportedImageFiles = $untracked
        metadataOrChecksumConflicts = $metadataConflicts
        unsupportedPhysicalFiles = $unsupported
        reconciliationConflictRows = $conflicts.Count
        statusCounts = $counts
    }
    staging = [ordered]@{
        path = $stagingRoot
        fileCount = $stagingRows.Count
        totalBytes = $stagingBytes
        inventoryFile = $stagingInventoryPath
        copiedOrModified = $false
    }
    readOnly = $true
    step10Ready = (-not $requiresReview)
    requiresExplicitDisposition = $requiresReview
    evidence = [ordered]@{
        directory = $runDir
        reconciliationDirectory = $reconciliationDir
        summary = $summaryPath
        plan = $planPath
        conflicts = $conflictsPath
        stagingInventory = $stagingInventoryPath
    }
}
$reportPath = Join-Path $runDir 'STEP9-REPORT.json'
Write-JsonNoBom $report $reportPath

$markdownPath = Join-Path $runDir 'STEP9-REPORT.md'
$decision = if ($requiresReview) { 'REVIEW REQUIRED before Step 10' } else { 'READY for Step 10' }
$md = @"
# 0031-FEAT Step 9 — local reconciliation report

- Dataset: $datasetName
- Launch mode: $mode
- Database identity: $($summary.databaseIdentity)
- Shared Files root: $sharedFilesRoot
- Reconciliation outcome: $($summary.outcome)
- Image rows: $cataloguedRows
- Matching physical files: $matching
- Missing physical files: $missing
- Untracked physical files: $untrackedPhysical
- Untracked supported image files: $untracked
- Unsupported physical files: $unsupported
- Metadata/checksum conflicts: $metadataConflicts
- Reconciliation conflict rows: $($conflicts.Count)
- .image-staging files: $($stagingRows.Count)
- Decision: **$decision**

This run is read-only. It does not apply the 0024 create plan, mutate Image rows,
or change Files bytes. Any non-zero anomaly above requires an explicit Step 9
disposition before Step 10 copies the shared tree.
"@
[System.IO.File]::WriteAllText($markdownPath, $md + [Environment]::NewLine, $utf8NoBom)

Write-Host
Write-Host 'Step 9 local reconciliation captured.'
Write-Host "  Image rows:                  $cataloguedRows"
Write-Host "  Matching physical files:     $matching"
Write-Host "  Missing physical files:      $missing"
Write-Host "  Untracked physical files:     $untrackedPhysical"
Write-Host "  Untracked supported images:  $untracked"
Write-Host "  Unsupported physical files:  $unsupported"
Write-Host "  Metadata/checksum conflicts: $metadataConflicts"
Write-Host "  Conflict rows:               $($conflicts.Count)"
Write-Host "  .image-staging files:        $($stagingRows.Count)"
Write-Host "  Report:                      $reportPath"
if ($requiresReview) {
    Write-Host 'RESULT: REVIEW REQUIRED before Step 10. The script completed successfully but found state requiring explicit disposition.'
} else {
    Write-Host 'RESULT: READY for Step 10 from the local dataset perspective.'
}
Write-Host 'Keep both local and production responder write paths frozen.'
