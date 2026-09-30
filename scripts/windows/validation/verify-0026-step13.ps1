#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BackupFile,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [string]$ChromeBin,
    [string]$Python = 'python'
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../..')).Path
$backup = (Get-Item -LiteralPath $BackupFile).FullName
if (!(Test-Path -LiteralPath $backup -PathType Leaf)) { throw 'BackupFile must be a regular pg_dump SQL/custom-format backup.' }
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'EvidenceDirectory must not already exist.' }
$evidencePath = if ([IO.Path]::IsPathRooted($EvidenceDirectory)) { [IO.Path]::GetFullPath($EvidenceDirectory) } else { [IO.Path]::GetFullPath((Join-Path (Get-Location).Path $EvidenceDirectory)) }

function Require-Command([string]$Name) {
    if (!(Get-Command $Name -ErrorAction SilentlyContinue)) { throw "Required command not found: $Name" }
}
Require-Command docker
Require-Command node
Require-Command $Python

& $Python -c 'from PIL import Image, ImageDraw' 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Python Pillow is missing for '$Python'. Install Pillow before Step 13."
}

$clientNodeModules = Join-Path $repository 'diaries-client/node_modules'
if (!(Test-Path -LiteralPath (Join-Path $clientNodeModules 'mqtt'))) {
    throw 'diaries-client/node_modules/mqtt is missing. Run npm install in diaries-client first.'
}
if (!(Test-Path -LiteralPath (Join-Path $clientNodeModules 'playwright'))) {
    & node -e "require.resolve('playwright')" 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw 'Playwright is missing. Install it or expose it through NODE_PATH before Step 13.'
    }
}

if (!$ChromeBin -and $env:CHROME_BIN) {
    $ChromeBin = $env:CHROME_BIN
}
if (!$ChromeBin) {
    $ChromeBin = @(
        'C:/Program Files/Google/Chrome/Application/chrome.exe',
        'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
        'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
        'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'
    ) | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (!$ChromeBin -or !(Test-Path -LiteralPath $ChromeBin)) {
    throw 'Chrome/Edge not found. Supply -ChromeBin or set CHROME_BIN.'
}

$null = & docker info --format '{{.ServerVersion}}'
if ($LASTEXITCODE -ne 0) { throw 'Docker is not available.' }

$javaImage = if ($env:STEP13_JAVA_IMAGE) { $env:STEP13_JAVA_IMAGE } else { 'diaries-responder:local' }
$null = & docker image inspect $javaImage 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Java 25 fixture image '$javaImage' is not available. Build local-docker-build first or set STEP13_JAVA_IMAGE."
}

$tempLog = Join-Path ([IO.Path]::GetTempPath()) ("0026-step13-build-{0}.log" -f [guid]::NewGuid().ToString('N'))
$previousChrome = $env:CHROME_BIN
$previousPython = $env:STEP13_PYTHON
try {
    Write-Host 'Testing Step 13 retained-snapshot barrier and failure diagnostics...'
    & node (Join-Path $PSScriptRoot 'step13-retained-snapshot.test.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Step 13 retained-snapshot regression tests failed.' }

    Write-Host 'Testing Step 13 public Image HTTP preflight and failure diagnostics...'
    & node (Join-Path $PSScriptRoot 'step13-image-http.test.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Step 13 Image HTTP preflight regression tests failed.' }

    Write-Host 'Testing Step 13 restart-safe responder/web reverse-proxy routing...'
    & node (Join-Path $PSScriptRoot 'step13-proxy-routing.test.cjs')
    if ($LASTEXITCODE -ne 0) { throw 'Step 13 restart-safe routing regression tests failed.' }

    Write-Host 'Building the exact responder/web candidate JARs for Step 13...'
    & (Join-Path $repository 'gradlew.bat') -p $repository `
        :diaries-responder:clean :diaries-web:clean `
        :diaries-responder:shadowJar :diaries-web:shadowJar `
        --rerun-tasks --console=plain 2>&1 | Tee-Object -FilePath $tempLog
    if ($LASTEXITCODE -ne 0) { throw 'Candidate responder/web build failed.' }

    $env:CHROME_BIN = $ChromeBin
    $env:STEP13_PYTHON = $Python
    Write-Host 'Running fully disposable 0026 Step 13 cross-component verification...'
    & node (Join-Path $PSScriptRoot 'smoke-imagefragment-reader.cjs') $backup $evidencePath
    if ($LASTEXITCODE -ne 0) { throw 'Step 13 cross-component runner failed. Inspect the evidence directory.' }

    $summary = Get-Content -LiteralPath (Join-Path $evidencePath 'evidence/summary.json') -Raw | ConvertFrom-Json
    if ($summary.status -ne 'PASSED') { throw "Step 13 summary status is $($summary.status)." }
    if ($summary.cleanupFailures.Count -ne 0) { throw 'Step 13 reported cleanup failures.' }

    Write-Host "Step 13 PASSED. Evidence: $evidencePath"
} finally {
    if (Test-Path -LiteralPath (Join-Path $evidencePath 'evidence') -PathType Container) {
        if (Test-Path -LiteralPath $tempLog -PathType Leaf) {
            Copy-Item -LiteralPath $tempLog -Destination (Join-Path $evidencePath 'evidence/candidate-build.log') -Force
        }
        $hashFile = Join-Path $evidencePath 'evidence/SHA256SUMS.txt'
        $hashes = Get-ChildItem -LiteralPath (Join-Path $evidencePath 'evidence') -Recurse -File |
            Where-Object { $_.FullName -ne $hashFile } |
            Sort-Object FullName |
            ForEach-Object {
                $relative = [IO.Path]::GetRelativePath((Join-Path $evidencePath 'evidence'), $_.FullName).Replace('\','/')
                '{0}  {1}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(), $relative
            }
        [IO.File]::WriteAllLines($hashFile, $hashes)
    }
    $env:CHROME_BIN = $previousChrome
    $env:STEP13_PYTHON = $previousPython
    Remove-Item -LiteralPath $tempLog -Force -ErrorAction SilentlyContinue
}
