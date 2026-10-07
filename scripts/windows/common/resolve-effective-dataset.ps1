param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('development-infrastructure', 'local-docker-build', 'local-published-smoke')]
    [string]$ModeName,

    [Parameter(Mandatory = $true)]
    [string]$ProjectDir,

    [Parameter(Mandatory = $true)]
    [string]$DatabaseDataDir,

    [Parameter(Mandatory = $true)]
    [string]$FilesDir
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($DatabaseDataDir)) { throw 'Effective DIARIES_DB_DATA_DIR is empty.' }
if ([string]::IsNullOrWhiteSpace($FilesDir)) { throw 'Effective DIARIES_FILES_DIR is empty.' }
if ($FilesDir -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { throw "Invalid DIARIES_FILES_DIR: $FilesDir" }

$projectPath = [System.IO.Path]::GetFullPath($ProjectDir)
$dbPath = if ([System.IO.Path]::IsPathRooted($DatabaseDataDir)) {
    [System.IO.Path]::GetFullPath($DatabaseDataDir)
} else {
    [System.IO.Path]::GetFullPath((Join-Path $projectPath $DatabaseDataDir))
}

$datasetName = Split-Path -Leaf $dbPath
if ([string]::IsNullOrWhiteSpace($datasetName)) { throw "Unable to derive dataset name from DIARIES_DB_DATA_DIR=$DatabaseDataDir" }
if ($datasetName -notmatch '^[A-Za-z0-9][A-Za-z0-9._-]*$') { throw "Derived dataset name '$datasetName' is not filesystem-safe." }

$filesRoot = $null
if ($ModeName -eq 'development-infrastructure') {
    $baseConfig = Join-Path $env:USERPROFILE '.diaries\responder.json'
    if (-not (Test-Path -LiteralPath $baseConfig -PathType Leaf)) {
        throw "Base responder configuration does not exist: $baseConfig"
    }
    $config = Get-Content -LiteralPath $baseConfig -Raw | ConvertFrom-Json
    if ($null -eq $config.diaries -or [string]::IsNullOrWhiteSpace([string]$config.diaries.root)) {
        throw "Base responder configuration does not define diaries.root: $baseConfig"
    }
    $filesRoot = Join-Path ([string]$config.diaries.root) $FilesDir
} else {
    foreach ($name in 'DIARIES_NAS_HOST','DIARIES_NAS_SHARE','DIARIES_NAS_CONTENT_PATH') {
        $value = [Environment]::GetEnvironmentVariable($name)
        if ([string]::IsNullOrWhiteSpace($value)) { throw "$name is required to resolve the physical Files root for $ModeName." }
    }
    $content = $env:DIARIES_NAS_CONTENT_PATH.Replace('/', '\').Trim('\')
    # Host-side Windows tooling may need a different DNS alias from Docker's CIFS
    # volume configuration (for example \nas instead of \nas.localdomain).
    # Keep this override host-only so Compose continues to use DIARIES_NAS_HOST and
    # therefore retains its normal project/volume identity.
    $windowsNasHost = [Environment]::GetEnvironmentVariable('DIARIES_WINDOWS_NAS_HOST')
    if ([string]::IsNullOrWhiteSpace($windowsNasHost)) { $windowsNasHost = $env:DIARIES_NAS_HOST }
    $filesRoot = "\\$windowsNasHost\$($env:DIARIES_NAS_SHARE)\$content\$FilesDir"
}

$sharing = if ($datasetName -eq 'common' -and $FilesDir -eq 'files-development-common') {
    'shared by all three local launch modes through the paired local.env override'
} else {
    "isolated durable dataset selected by $ModeName"
}

# Emit only KEY=VALUE records so a batch caller can import them safely.
"DIARIES_DATASET_NAME=$datasetName"
"DIARIES_EFFECTIVE_DB_DATA_DIR=$dbPath"
"DIARIES_EFFECTIVE_FILES_ROOT=$filesRoot"
"DIARIES_DATASET_SHARING=$sharing"
