param(
    [Parameter(Mandatory = $true)]
    [string]$BaseConfig,

    [Parameter(Mandatory = $true)]
    [string]$OutputConfig,

    [Parameter(Mandatory = $true)]
    [string]$FilesDir
)

$ErrorActionPreference = 'Stop'

if ([string]::IsNullOrWhiteSpace($FilesDir)) {
    throw 'DIARIES_FILES_DIR must not be empty.'
}

$basePath = [System.IO.Path]::GetFullPath($BaseConfig)
if (-not (Test-Path -LiteralPath $basePath -PathType Leaf)) {
    throw "Base responder configuration does not exist: $basePath"
}

$config = Get-Content -LiteralPath $basePath -Raw | ConvertFrom-Json
if ($null -eq $config.diaries) {
    throw 'Base responder configuration does not contain a diaries object.'
}
if ([string]::IsNullOrWhiteSpace([string]$config.diaries.root)) {
    throw 'Base responder configuration does not define diaries.root.'
}

# Preserve the developer-owned configuration as the base. Only the mutable
# Files leaf selector is replaced in the generated effective configuration.
if ($null -eq $config.diaries.PSObject.Properties['files']) {
    $config.diaries | Add-Member -NotePropertyName files -NotePropertyValue $FilesDir
} else {
    $config.diaries.files = $FilesDir
}

$outputPath = [System.IO.Path]::GetFullPath($OutputConfig)
$outputDirectory = Split-Path -Parent $outputPath
if (-not (Test-Path -LiteralPath $outputDirectory -PathType Container)) {
    New-Item -ItemType Directory -Path $outputDirectory -Force | Out-Null
}

$json = $config | ConvertTo-Json -Depth 100
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($outputPath, $json + [Environment]::NewLine, $utf8NoBom)

# stdout is intentionally restricted to the non-secret effective physical Files
# root so the batch wrapper can capture and display it safely.
Join-Path -Path ([string]$config.diaries.root) -ChildPath $FilesDir
