param(
    [Parameter(Mandatory = $true)][string]$BackupFile,
    [Parameter(Mandatory = $true)][string]$DatasetName,
    [Parameter(Mandatory = $true)][string]$DatabaseDataDir,
    [Parameter(Mandatory = $true)][string]$FilesDir,
    [Parameter(Mandatory = $true)][string]$FilesRoot
)

$ErrorActionPreference = 'Stop'
$backupPath = [System.IO.Path]::GetFullPath($BackupFile)
$manifestPath = "$backupPath.dataset.json"

if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    Write-Warning "No Step-7 dataset manifest exists for this legacy database backup: $backupPath"
    Write-Warning "This is a DATABASE-ONLY restore. Verify the matching mutable Files root manually before continuing."
    exit 0
}

$manifest = Get-Content -LiteralPath $manifestPath -Raw | ConvertFrom-Json
if ([string]$manifest.backupType -ne 'database-only' -or [bool]$manifest.completeDatasetBackup) {
    throw "Unexpected backup manifest semantics in $manifestPath"
}

$checks = @(
    @{ Name='logical dataset'; Expected=$DatasetName; Actual=[string]$manifest.logicalDataset },
    @{ Name='database data directory'; Expected=$DatabaseDataDir; Actual=[string]$manifest.effectiveDatabaseDataDir },
    @{ Name='Files selector'; Expected=$FilesDir; Actual=[string]$manifest.effectiveFilesDir },
    @{ Name='physical Files root'; Expected=$FilesRoot; Actual=[string]$manifest.resolvedPhysicalFilesRoot }
)
foreach ($check in $checks) {
    if ($check.Expected -ne $check.Actual) {
        throw "Dataset manifest mismatch for $($check.Name): backup='$($check.Actual)' current='$($check.Expected)'. Refusing restore."
    }
}

Write-Host 'Matched database-only backup manifest:'
Write-Host "  Dataset:    $DatasetName"
Write-Host "  Database:   $DatabaseDataDir"
Write-Host "  Files dir:  $FilesDir"
Write-Host "  Files root: $FilesRoot"
Write-Host '  Files bytes: NOT included in this restore'
