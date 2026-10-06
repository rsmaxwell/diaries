Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-DiariesProjectRoot {
    param([string]$StartPath = $PSScriptRoot)
    $current = [System.IO.Path]::GetFullPath($StartPath)
    if (Test-Path -LiteralPath $current -PathType Leaf) { $current = Split-Path -Parent $current }
    while ($true) {
        $required = @('diaries-client','diaries-responder','diaries-web','change-control')
        $ok = $true
        foreach ($name in $required) {
            if (-not (Test-Path -LiteralPath (Join-Path $current $name) -PathType Container)) { $ok = $false; break }
        }
        if ($ok) { return $current }
        $parent = Split-Path -Parent $current
        if ([string]::IsNullOrWhiteSpace($parent) -or $parent -eq $current) {
            throw "Could not locate the Diaries project root from $StartPath"
        }
        $current = $parent
    }
}

function Get-Step14BuildRoot {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    Join-Path $ProjectRoot 'build\0027-step14'
}

function Get-CurrentStep14RunDirectory {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot)
    $buildRoot = Get-Step14BuildRoot -ProjectRoot $ProjectRoot
    $marker = Join-Path $buildRoot 'current-run.txt'
    if (-not (Test-Path -LiteralPath $marker -PathType Leaf)) {
        throw "No Step 14 run is active. Run step14-begin.ps1 first: $marker"
    }
    $runId = (Get-Content -LiteralPath $marker -Raw).Trim()
    if ([string]::IsNullOrWhiteSpace($runId)) { throw "Step 14 run marker is empty: $marker" }
    $runDirectory = Join-Path (Join-Path $buildRoot 'runs') $runId
    if (-not (Test-Path -LiteralPath $runDirectory -PathType Container)) {
        throw "Step 14 run directory does not exist: $runDirectory"
    }
    $runDirectory
}

function Write-Utf8NoBom {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Text)
    $parent = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $utf8 = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Text,$utf8)
}

function Require-Command {
    param([Parameter(Mandatory=$true)][string]$Name)
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if ($null -eq $command) { throw "Required command not found: $Name" }
    $command
}

function Invoke-Step14LoggedCommand {
    param(
        [Parameter(Mandatory=$true)][string]$Program,
        [Parameter(Mandatory=$true)][string[]]$Arguments,
        [Parameter(Mandatory=$true)][string]$LogPath,
        [string]$WorkingDirectory
    )
    if ([string]::IsNullOrWhiteSpace($WorkingDirectory)) { $WorkingDirectory = (Get-Location).Path }
    $parent = Split-Path -Parent $LogPath
    if (-not (Test-Path -LiteralPath $parent -PathType Container)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    $code = 0
    Push-Location $WorkingDirectory
    try {
        & $Program @Arguments 2>&1 | Tee-Object -FilePath $LogPath
        $code = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($code -ne 0) { throw "$Program failed with exit $code. See $LogPath" }
}

function Resolve-ChromeBin {
    param([string]$ChromeBin)
    if (-not [string]::IsNullOrWhiteSpace($ChromeBin)) {
        if (-not (Test-Path -LiteralPath $ChromeBin -PathType Leaf)) { throw "Chrome/Edge not found: $ChromeBin" }
        return [System.IO.Path]::GetFullPath($ChromeBin)
    }
    if (-not [string]::IsNullOrWhiteSpace($env:CHROME_BIN) -and (Test-Path -LiteralPath $env:CHROME_BIN -PathType Leaf)) {
        return [System.IO.Path]::GetFullPath($env:CHROME_BIN)
    }
    $candidates = @(
        'C:\Program Files\Google\Chrome\Application\chrome.exe',
        'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
        'C:\Program Files\Microsoft\Edge\Application\msedge.exe',
        'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'
    )
    $found = $candidates | Where-Object { Test-Path -LiteralPath $_ -PathType Leaf } | Select-Object -First 1
    if ([string]::IsNullOrWhiteSpace($found)) { throw 'Chrome/Edge not found. Supply -ChromeBin or set CHROME_BIN.' }
    $found
}

function Resolve-ReaderBackup {
    param([Parameter(Mandatory=$true)][string]$ProjectRoot,[string]$ReaderBackupFile)
    if (-not [string]::IsNullOrWhiteSpace($ReaderBackupFile)) {
        $candidate = if ([System.IO.Path]::IsPathRooted($ReaderBackupFile)) { $ReaderBackupFile } else { Join-Path $ProjectRoot $ReaderBackupFile }
        if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) { throw "Reader backup not found: $candidate" }
        return (Resolve-Path -LiteralPath $candidate).Path
    }
    $default = Get-ChildItem -LiteralPath $ProjectRoot -File -Filter 'diaries-production-*.dump' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if ($null -eq $default) { throw 'No ReaderBackupFile supplied and no diaries-production-*.dump exists at the project root.' }
    $default.FullName
}

function Get-GitIdentityLines {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Label)
    $lines = New-Object System.Collections.Generic.List[string]
    try {
        $commit = (& git -C $Path rev-parse HEAD 2>$null) -join ''
        if ([string]::IsNullOrWhiteSpace($commit)) { $commit = '<unavailable>' }
        $lines.Add("$Label.commit=$commit")
        $status = & git -C $Path status --short 2>$null
        $lines.Add("$Label.status=" + ($(if($status){'dirty'}else{'clean'})))
    } catch {
        $lines.Add("$Label.commit=<unavailable>")
        $lines.Add("$Label.status=<unavailable>")
    }
    $lines
}
