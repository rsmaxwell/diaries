param(
    [Parameter(Mandatory = $true)][string]$BackupFile,
    [Parameter(Mandatory = $true)][string]$BackupFormat,
    [Parameter(Mandatory = $true)][string]$ModeName,
    [Parameter(Mandatory = $true)][string]$DatasetName,
    [Parameter(Mandatory = $true)][string]$DatabaseDataDir,
    [Parameter(Mandatory = $true)][string]$DatabaseName,
    [Parameter(Mandatory = $true)][string]$FilesDir,
    [Parameter(Mandatory = $true)][string]$FilesRoot,
    [Parameter(Mandatory = $true)][string]$ProjectDir,
    [string]$ImageRowCount = 'unknown'
)

$ErrorActionPreference = 'Stop'
$backupPath = [System.IO.Path]::GetFullPath($BackupFile)
if (-not (Test-Path -LiteralPath $backupPath -PathType Leaf)) { throw "Backup file does not exist: $backupPath" }

$gitCommit = 'unknown'
try {
    $candidate = (& git -C $ProjectDir rev-parse HEAD 2>$null | Select-Object -First 1)
    if (-not [string]::IsNullOrWhiteSpace($candidate)) { $gitCommit = $candidate.Trim() }
} catch { }

$cataloguedCount = $ImageRowCount
if ($cataloguedCount -notmatch '^\d+$') { $cataloguedCount = 'unknown' }

$manifest = [ordered]@{
    schemaVersion = 1
    backupType = 'database-only'
    completeDatasetBackup = $false
    createdAt = (Get-Date).ToString('o')
    launchMode = $ModeName
    logicalDataset = $DatasetName
    effectiveDatabaseDataDir = $DatabaseDataDir
    databaseName = $DatabaseName
    databaseBackupFile = [System.IO.Path]::GetFileName($backupPath)
    databaseBackupFormat = $BackupFormat
    effectiveFilesDir = $FilesDir
    resolvedPhysicalFilesRoot = $FilesRoot
    applicationSourceIdentity = [ordered]@{ gitCommit = $gitCommit }
    imageRowCount = $cataloguedCount
    cataloguedFileCount = $cataloguedCount
    filesSnapshot = $null
    note = 'Database-only backup. No mutable Files bytes are included. Restore only with the matching Files root/snapshot.'
}

$manifestPath = "$backupPath.dataset.json"
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, (($manifest | ConvertTo-Json -Depth 10) + [Environment]::NewLine), $utf8NoBom)
Write-Output $manifestPath
