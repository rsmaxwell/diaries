[CmdletBinding()]
param(
    [switch]$ProductionWriteFreezeConfirmed,
    [string]$Step9Run = '',
    [string]$OutputRoot = ''
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    throw "0031 Step 12: $Message"
}

function Read-EnvFile([string]$Path, [hashtable]$Values) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail "Environment file not found: $Path"
    }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        if ($trimmed -notmatch '^([A-Za-z_][A-Za-z0-9_]*)=(.*)$') { continue }
        $key = $matches[1]
        $value = $matches[2].Trim()
        if (($value.StartsWith('"') -and $value.EndsWith('"')) -or ($value.StartsWith("'") -and $value.EndsWith("'"))) {
            if ($value.Length -ge 2) { $value = $value.Substring(1, $value.Length - 2) }
        }
        $Values[$key] = $value
    }
}

function Resolve-Step9Run([string]$Step9RuntimeRoot) {
    if ($Step9Run) {
        $candidate = (Resolve-Path -LiteralPath $Step9Run).Path
        return $candidate
    }
    if (-not (Test-Path -LiteralPath $Step9RuntimeRoot -PathType Container)) {
        Fail "Step 9 runtime evidence directory not found: $Step9RuntimeRoot"
    }
    $matches = Get-ChildItem -LiteralPath $Step9RuntimeRoot -Directory |
        Where-Object { $_.Name -like 'local-common-*' } |
        Sort-Object Name -Descending
    if (-not $matches) {
        Fail "No Step 9 local-common-* baseline found below $Step9RuntimeRoot"
    }
    return $matches[0].FullName
}

function Write-StagingInventory([string]$FilesRoot, [string]$OutputFile) {
    $staging = Join-Path $FilesRoot '.image-staging'
    "relativePath`titemType`tsize`tlastWriteUtc" | Set-Content -LiteralPath $OutputFile -Encoding UTF8
    if (-not (Test-Path -LiteralPath $staging -PathType Container)) { return }

    Get-ChildItem -LiteralPath $staging -Force -Recurse | Sort-Object FullName | ForEach-Object {
        $relative = $_.FullName.Substring($staging.Length).TrimStart([char[]]@('\','/')) -replace '\\','/'
        $kind = if ($_.PSIsContainer) { 'directory' } else { 'file' }
        $size = if ($_.PSIsContainer) { 0 } else { $_.Length }
        $utc = $_.LastWriteTimeUtc.ToString('o')
        "$relative`t$kind`t$size`t$utc" | Add-Content -LiteralPath $OutputFile -Encoding UTF8
    }
}

if (-not $ProductionWriteFreezeConfirmed) {
    Fail 'Refusing to run without -ProductionWriteFreezeConfirmed. Step 12 must remain read-only while production Image/File writes are frozen.'
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..\..\..')).Path
$featureDir = Join-Path $projectRoot 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$step12Dir = Join-Path $featureDir 'evidence\Step 12'
$step9RuntimeRoot = Join-Path $featureDir 'evidence\Step 9\runtime'
$modeEnv = Join-Path $projectRoot 'config\environments\development-infrastructure.env'
$localEnv = Join-Path $projectRoot 'config\environments\local.env'
$prepareConfig = Join-Path $projectRoot 'scripts\windows\development-infrastructure\prepare-responder-config.bat'
$effectiveConfig = Join-Path $projectRoot 'build\development-infrastructure\responder.effective.json'
$gradle = Join-Path $projectRoot 'gradlew.bat'
$comparator = Join-Path $scriptDir 'compare-step9-step12.py'

foreach ($path in @($prepareConfig, $gradle, $comparator)) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Fail "Required file not found: $path" }
}

$effective = @{}
Read-EnvFile $modeEnv $effective
if (Test-Path -LiteralPath $localEnv -PathType Leaf) {
    Read-EnvFile $localEnv $effective
}

$expectedDb = './data/database/common'
$expectedFiles = 'files-development-common'
$dbDataDir = [string]$effective['DIARIES_DB_DATA_DIR']
$filesDir = [string]$effective['DIARIES_FILES_DIR']
if ($dbDataDir -ne $expectedDb -or $filesDir -ne $expectedFiles) {
    Fail "The normal local effective pair is not selected. Expected '$expectedDb' + '$expectedFiles'; found '$dbDataDir' + '$filesDir'."
}

Write-Host "Preparing effective responder configuration for the common local pair..."
& $prepareConfig
if ($LASTEXITCODE -ne 0) { Fail "prepare-responder-config.bat failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $effectiveConfig -PathType Leaf)) {
    Fail "Generated responder configuration not found: $effectiveConfig"
}

$config = Get-Content -LiteralPath $effectiveConfig -Raw | ConvertFrom-Json
if (-not $config.diaries -or -not $config.diaries.root -or -not $config.diaries.files) {
    Fail "Generated responder configuration does not contain diaries.root and diaries.files"
}
if ([string]$config.diaries.files -ne $expectedFiles) {
    Fail "Generated responder configuration selects diaries.files='$($config.diaries.files)' instead of '$expectedFiles'"
}

$filesRoot = Join-Path ([string]$config.diaries.root) ([string]$config.diaries.files)
if (-not (Test-Path -LiteralPath $filesRoot -PathType Container)) {
    Fail "Effective Files root does not exist: $filesRoot"
}
$filesRoot = (Resolve-Path -LiteralPath $filesRoot).Path

$baseline = Resolve-Step9Run $step9RuntimeRoot
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $step12Dir 'runtime'
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$runDir = Join-Path $OutputRoot "local-common-$timestamp"
$reconciliation = Join-Path $runDir 'reconciliation'
New-Item -ItemType Directory -Force -Path $reconciliation | Out-Null

$pair = [ordered]@{
    schemaVersion = 1
    feature = '0031-FEAT'
    step = 12
    dataset = 'local-common'
    modeUsedForReconciliation = 'development-infrastructure direct responder configuration'
    effectiveDbDataDir = $dbDataDir
    effectiveFilesDir = $filesDir
    physicalFilesRoot = $filesRoot
    publicFilesRoute = '/files/...'
    responderConfig = $effectiveConfig
    step9BaselineRun = $baseline
    productionWriteFreezeConfirmed = $true
    capturedAt = (Get-Date).ToUniversalTime().ToString('o')
}
$pair | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $runDir 'PAIR.json') -Encoding UTF8
Write-StagingInventory $filesRoot (Join-Path $runDir 'STAGING-INVENTORY.tsv')

Write-Host "Running read-only 0024 reconciliation against:"
Write-Host "  database dataset : $dbDataDir"
Write-Host "  Files selector   : $filesDir"
Write-Host "  physical root    : $filesRoot"
Write-Host "  Step 9 baseline  : $baseline"
Write-Host "  evidence         : $runDir"

$log = Join-Path $runDir 'reconciliation-console.txt'
$gradleArgs = @(
    ':diaries-responder:migration0024ImageCatalogue',
    "-PmigrationConfig=$effectiveConfig",
    "-PmigrationOutput=$reconciliation",
    '-PmigrationMode=dry-run',
    '--console=plain'
)

Push-Location $projectRoot
try {
    & $gradle @gradleArgs 2>&1 | Tee-Object -FilePath $log
    $gradleExit = $LASTEXITCODE
}
finally {
    Pop-Location
}
if ($gradleExit -ne 0) {
    Fail "0024 dry-run reconciliation failed with exit code $gradleExit. Evidence remains in $runDir"
}

foreach ($required in @('0024-summary.json','0024-file-inventory.csv','0024-conflicts.csv','SHA256SUMS.txt')) {
    if (-not (Test-Path -LiteralPath (Join-Path $reconciliation $required) -PathType Leaf)) {
        Fail "Reconciliation succeeded without required evidence file: $required"
    }
}

$reportPrefix = Join-Path $runDir 'STEP12-REPORT'
$pythonCommand = Get-Command python -ErrorAction SilentlyContinue
$pythonArgsPrefix = @()
if (-not $pythonCommand) {
    $pythonCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pythonCommand) { $pythonArgsPrefix = @('-3') }
}
if (-not $pythonCommand) { Fail 'Python 3 was not found on PATH (python or py -3).' }

$compareArgs = @()
$compareArgs += $pythonArgsPrefix
$compareArgs += @(
    $comparator,
    '--dataset', 'local-common',
    '--baseline', $baseline,
    '--current', $runDir,
    '--expected-db-data-dir', $expectedDb,
    '--expected-files-dir', $expectedFiles,
    '--expect-files-root', 'changed',
    '--output-prefix', $reportPrefix
)
& $pythonCommand.Source @compareArgs
$compareExit = $LASTEXITCODE
if ($compareExit -ne 0) {
    Fail "Step 12 comparison with Step 9 failed. Review $reportPrefix.json and $reportPrefix.md"
}

$latest = Join-Path $step12Dir 'LATEST-LOCAL-COMMON.txt'
$runDir | Set-Content -LiteralPath $latest -Encoding ASCII

Write-Host ""
Write-Host "PASS: Step 12 local-common reconciliation matches the Step 9 semantic baseline."
Write-Host "Evidence: $runDir"
Write-Host "Next: run the Step 12 production reconciliation on pluto, then preserve/copy its evidence for close-out."
