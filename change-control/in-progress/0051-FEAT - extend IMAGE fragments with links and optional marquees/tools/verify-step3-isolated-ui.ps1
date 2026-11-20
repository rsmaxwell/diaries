#Requires -Version 7.0
<#
0051 Step 3 isolated cross-component browser smoke. Feature-specific historical tooling.
Requires only the accepted frozen .dump, Docker Desktop, JDK/Gradle, Node,
Chrome/Edge + Playwright; synthetic images generated with browser Canvas.
Uses NO existing DB, NAS, or Compose stack.
Runs the proven 0026 disposable reader harness adapted for 0051.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$BackupFile,
    [string]$ChromeBin
)

$ErrorActionPreference = 'Stop'
$repository = (Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$feature = Join-Path $repository 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$backup = (Get-Item -LiteralPath $BackupFile -ErrorAction Stop).FullName
$expectedBackup = 'fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86'
if (!(Test-Path -LiteralPath $backup -PathType Leaf)) { throw 'Frozen backup is not a regular file.' }
$actualBackup = (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
if ($actualBackup -ne $expectedBackup) { throw 'Frozen 0024 fixture SHA-256 mismatch. No containers started.' }
foreach ($tool in @('docker','node','git')) {
    if (!(Get-Command $tool -ErrorAction SilentlyContinue)) { throw "Required command missing: $tool" }
}
$nodeModules = Join-Path $repository 'diaries-client/node_modules'
if (!(Test-Path -LiteralPath (Join-Path $nodeModules 'mqtt'))) { throw 'diaries-client/node_modules/mqtt missing; run npm ci in diaries-client first.' }
if (!(Test-Path -LiteralPath (Join-Path $nodeModules 'playwright'))) {
    & node -e "require.resolve('playwright')" 2>$null
    if ($LASTEXITCODE -ne 0) { throw 'Node Playwright missing. Install in your test environment first.' }
}
if (!$ChromeBin -and $env:CHROME_BIN) { $ChromeBin = $env:CHROME_BIN }
if (!$ChromeBin) {
    $ChromeBin = @('C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
      'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe') |
      Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
}
if (!$ChromeBin -or !(Test-Path -LiteralPath $ChromeBin)) { throw 'Chrome or Edge not found. Supply -ChromeBin.' }
$null = & docker info --format '{{.ServerVersion}}' 2>&1
if ($LASTEXITCODE -ne 0) { throw 'Docker Desktop engine unavailable. No containers started.' }

$runId = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ') + '-' + [guid]::NewGuid().ToString('N').Substring(0,8)
$base = Join-Path $feature 'evidence/Step 3/private'
New-Item -ItemType Directory -Path $base -Force | Out-Null
$run = Join-Path $base "integrated-$runId"
$buildLog = Join-Path $base "candidate-build-$runId.log"
$oldChrome = $env:CHROME_BIN
$oldRuntime = $env:STEP13_JAVA_IMAGE
$passed = $false
try {
    Write-Host "0051 Step 3 integrated smoke ID: $runId"
    Write-Host "Evidence: $run"
    # Use a clean Java 25 runtime; do not overwrite the persistent local-development
    # image/tag or mount any NAS volume. Pulling this immutable-tag base is allowed.
    $runtime = 'eclipse-temurin:25-jre-alpine'
    & docker image inspect $runtime *> $null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Fetching disposable Java runtime image: $runtime"
        & docker pull $runtime
        if ($LASTEXITCODE -ne 0) { throw 'Unable to pull Java runtime image.' }
    }
    $gradlew = Join-Path $repository 'gradlew.bat'
    Write-Host '=== Build responder/web candidate fat JARs (no deployment) ==='
    $gradleOutput = (& $gradlew -p $repository --no-daemon --console=plain `
      :diaries-responder:clean :diaries-web:clean `
      :diaries-responder:shadowJar :diaries-web:shadowJar 2>&1 | Out-String)
    $gradleExit = $LASTEXITCODE
    [IO.File]::WriteAllText($buildLog,$gradleOutput)
    if ($gradleExit -ne 0) { throw "Candidate Gradle build failed ($gradleExit). See $buildLog" }
    $env:CHROME_BIN = $ChromeBin
    $env:STEP13_JAVA_IMAGE = $runtime
    Write-Host '=== Disposable PostgreSQL/MQTT/responder/web + browser smoke ==='
    $runner = Join-Path $feature 'tests/step3-isolated-reader-smoke.cjs'
    & node $runner $backup $run
    $nodeExit=$LASTEXITCODE
    if (!(Test-Path -LiteralPath (Join-Path $run 'evidence/summary.json'))) {
        throw "Smoke runner produced no summary (exit $nodeExit); inspect $run"
    }
    $summary = Get-Content -LiteralPath (Join-Path $run 'evidence/summary.json') -Raw | ConvertFrom-Json
    if ($nodeExit -ne 0 -or $summary.status -ne 'PASSED' -or @($summary.cleanupFailures).Count -ne 0) {
        throw "Integrated smoke failed (exit $nodeExit, status $($summary.status)); inspect $run"
    }
    $passed = $true
    Write-Host 'PASS: 0051 integrated public reader smoke and container cleanup'
} catch {
    Write-Host "FAIL: $($_.Exception.Message)"
} finally {
    if (Test-Path -LiteralPath (Join-Path $run 'evidence') -PathType Container) {
        Copy-Item -LiteralPath $buildLog -Destination (Join-Path $run 'evidence/candidate-build.log') -ErrorAction SilentlyContinue
        $evidencePath = Join-Path $run 'evidence'
        $checksums = Get-ChildItem -LiteralPath $evidencePath -Recurse -File |
          Where-Object { $_.Name -ne 'SHA256SUMS.txt' } | Sort-Object FullName | ForEach-Object {
            $relative = [IO.Path]::GetRelativePath($evidencePath,$_.FullName).Replace('\','/')
            '{0}  {1}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(),$relative
          }
        [IO.File]::WriteAllLines((Join-Path $evidencePath 'SHA256SUMS.txt'),@($checksums))
        Remove-Item -LiteralPath $buildLog -Force -ErrorAction SilentlyContinue
    }
    $env:CHROME_BIN=$oldChrome
    $env:STEP13_JAVA_IMAGE=$oldRuntime
    Write-Host "Step 3 evidence: $run"
}
if (!$passed) { exit 1 }
