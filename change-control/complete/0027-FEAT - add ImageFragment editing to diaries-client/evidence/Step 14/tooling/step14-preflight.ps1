param(
    [string]$ProjectRoot,
    [string]$ReaderBackupFile,
    [string]$ChromeBin,
    [string]$Python = 'python'
)
. (Join-Path $PSScriptRoot 'step14-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep14RunDirectory -ProjectRoot $ProjectRoot
$failures = New-Object System.Collections.Generic.List[string]
$warnings = New-Object System.Collections.Generic.List[string]
$lines = New-Object System.Collections.Generic.List[string]
function Pass([string]$m){$lines.Add("PASS: $m");Write-Host "PASS: $m"}
function Fail([string]$m){$failures.Add($m);$lines.Add("FAIL: $m");Write-Host "FAIL: $m" -ForegroundColor Red}
function Warn([string]$m){$warnings.Add($m);$lines.Add("WARN: $m");Write-Host "WARN: $m" -ForegroundColor Yellow}
$lines.Add("timestamp=$((Get-Date).ToString('o'))")
$lines.Add("projectRoot=$ProjectRoot")

foreach($command in @('docker','node','npm.cmd','git',$Python)) {
    try { $resolved=Require-Command $command; Pass "$command available: $($resolved.Source)" } catch { Fail $_.Exception.Message }
}

try {
    $java = & java -version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'java -version failed' }
    $javaText = $java -join [Environment]::NewLine
    if ($javaText -match '(?m)(?:version\s+"?25\.|openjdk\s+25\.)') { Pass 'Java 25 is active' } else { Fail "Java 25 is required; active java reports: $($java[0])" }
} catch { Fail $_.Exception.Message }

try {
    $serverVersion = (& docker info --format '{{.ServerVersion}}' 2>$null) -join ''
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($serverVersion)) { throw 'Docker Desktop/engine is not available.' }
    Pass "Docker engine available: $serverVersion"
} catch { Fail $_.Exception.Message }


# The disposable reader verification performs `clean` before rebuilding the exact
# responder/web candidate. A direct-development responder launched from the Gradle
# install distribution keeps JARs under build/install open on Windows and makes that
# clean fail late in the run. Detect it here instead.
try {
    $runningInstalledResponders = @(Get-CimInstance Win32_Process -Filter "Name='java.exe'" -ErrorAction Stop |
        Where-Object {
            $_.CommandLine -and
            $_.CommandLine -match 'diaries-responder[\\/]+build[\\/]+install[\\/]+diaries-responder'
        })
    if ($runningInstalledResponders.Count -eq 0) {
        Pass 'no direct-development responder is running from the Gradle install distribution'
    } else {
        $pids = ($runningInstalledResponders | ForEach-Object { $_.ProcessId }) -join ', '
        Fail "direct-development responder is still running from diaries-responder/build/install/diaries-responder (PID(s): $pids); stop it before Step 14 so the reader verifier can clean/rebuild the candidate"
    }
} catch {
    Warn "could not inspect running Java processes for a direct-development responder: $($_.Exception.Message)"
}

$ng = Join-Path $ProjectRoot 'diaries-client\node_modules\.bin\ng.cmd'
if (Test-Path -LiteralPath $ng -PathType Leaf) { Pass 'Angular dependencies are installed' } else { Fail 'diaries-client/node_modules/.bin/ng.cmd is missing; run npm ci in diaries-client' }

try { $resolvedChrome=Resolve-ChromeBin -ChromeBin $ChromeBin; Pass "Chrome/Edge available: $resolvedChrome" } catch { Fail $_.Exception.Message }

try {
    $backup=Resolve-ReaderBackup -ProjectRoot $ProjectRoot -ReaderBackupFile $ReaderBackupFile
    $hash=(Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
    Pass "reader backup available: $backup (sha256=$hash)"
} catch { Fail $_.Exception.Message }

$integratedVerifier = Join-Path $ProjectRoot 'scripts\windows\validation\test-image-catalogue.ps1'
$brokerFixture = Join-Path $ProjectRoot 'scripts\windows\validation\image-catalogue-test-mosquitto.conf'
if (Test-Path -LiteralPath $integratedVerifier -PathType Leaf) { Pass 'permanent integrated SQL/JPA/MQTT/client/responder/web regression runner is present' } else { Fail "integrated regression runner missing: $integratedVerifier" }
if (Test-Path -LiteralPath $brokerFixture -PathType Leaf) { Pass 'permanent integrated-regression Mosquitto fixture is present' } else { Fail "permanent MQTT fixture missing: $brokerFixture" }

$javaImage = if ($env:STEP13_JAVA_IMAGE) { $env:STEP13_JAVA_IMAGE } else { 'diaries-responder:local' }
& docker image inspect $javaImage *> $null
if ($LASTEXITCODE -eq 0) { Pass "Java 25 disposable-reader runtime image is available: $javaImage" } else { Fail "Reader verifier runtime image is missing: $javaImage. Build local-docker-build first or set STEP13_JAVA_IMAGE to an existing Java 25 runtime image." }

$readerVerifier = Join-Path $ProjectRoot 'scripts\windows\validation\verify-imagefragment-reader.ps1'
if (Test-Path -LiteralPath $readerVerifier -PathType Leaf) { Pass '0026 disposable ImageFragment reader verifier is present' } else { Fail "reader verifier missing: $readerVerifier" }

$reportChecker = Join-Path $PSScriptRoot 'check-step14-test-reports.py'
if (Test-Path -LiteralPath $reportChecker -PathType Leaf) { Pass 'Step 14 JUnit report checker is present' } else { Fail "report checker missing: $reportChecker" }

try {
    & node -e "require.resolve('playwright')" 2>$null
    if ($LASTEXITCODE -eq 0) { Pass 'Playwright is available to Node' }
    else {
        $localPlaywright = Join-Path $ProjectRoot 'diaries-client\node_modules\playwright'
        if (Test-Path -LiteralPath $localPlaywright -PathType Container) { Pass 'Playwright is available in diaries-client/node_modules' }
        else { Fail 'Playwright is required by the disposable reader verifier but is not resolvable.' }
    }
} catch { Fail 'Playwright prerequisite check failed.' }

try {
    & $Python -c 'from PIL import Image' 2>$null
    if ($LASTEXITCODE -eq 0) { Pass 'Python Pillow is available for reader fixture Images' } else { Fail 'Python Pillow is required by the disposable reader verifier.' }
} catch { Fail 'Python Pillow prerequisite check failed.' }

$gateConfig = Join-Path $ProjectRoot 'diaries-responder\src\main\java\com\rsmaxwell\diaries\responder\config\Config.java'
if (Test-Path -LiteralPath $gateConfig -PathType Leaf) {
    $gateSource=Get-Content -LiteralPath $gateConfig -Raw
    if ($gateSource -match 'Boolean\.TRUE\.equals\(imageFragmentWritesEnabled\)') { Pass 'responder gate defaults false when omitted/null' }
    else { Fail 'could not prove responder imageFragmentWritesEnabled defaults false' }
} else { Fail "missing responder Config.java: $gateConfig" }

$step13Readme = Join-Path $ProjectRoot 'change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 13\README.md'
if (Test-Path -LiteralPath $step13Readme -PathType Leaf) {
    $step13=Get-Content -LiteralPath $step13Readme -Raw
    if ($step13 -match '(?i)status:\s*(complete|closed)') { Pass 'Step 13 source record appears closed' }
    else { Warn 'Step 13 source record does not yet say complete/closed. Step 14 tooling may run, but Step 14 must not be closed before Step 13.' }
} else { Warn 'Step 13 README not found; manually verify the Step 13 prerequisite.' }

Write-Utf8NoBom -Path (Join-Path $runDir 'preflight.txt') -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
if($warnings.Count -gt 0){Write-Host "Warnings: $($warnings.Count)" -ForegroundColor Yellow}
if($failures.Count -gt 0){throw "Step 14 preflight FAILED with $($failures.Count) error(s). See $(Join-Path $runDir 'preflight.txt')"}
Write-Host 'Step 14 preflight passed.' -ForegroundColor Green
