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
$backup = Resolve-ReaderBackup -ProjectRoot $ProjectRoot -ReaderBackupFile $ReaderBackupFile
$chrome = Resolve-ChromeBin -ChromeBin $ChromeBin
$summary = [ordered]@{
    step = 14
    startedAtLocal = (Get-Date).ToString('o')
    status = 'RUNNING'
    readerBackup = [System.IO.Path]::GetFileName($backup)
    readerBackupSha256 = (Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
    clientTests = $null
    responderTests = $null
    webTests = $null
    integratedRegression = $false
    clientBuild = $false
    javaTestBuild = $false
    requiredReports = $false
    readerCrossComponent = $false
    composeLocalDockerBuild = $false
    composeLocalPublishedSmoke = $false
    diffChecks = $false
}
$summaryPath = Join-Path $runDir 'regression-summary.json'
$previousChrome = $env:CHROME_BIN
try {
    $env:CHROME_BIN = $chrome
    Write-Host 'Running Step 14 preflight...'
    & (Join-Path $PSScriptRoot 'step14-preflight.ps1') -ProjectRoot $ProjectRoot -ReaderBackupFile $backup -ChromeBin $chrome -Python $Python

    Write-Host 'Running the permanent full SQL/JPA/MQTT + responder/web + Angular regression gate in disposable fixtures...'
    $integratedOut = Join-Path $runDir 'integrated-regression'
    & (Join-Path $ProjectRoot 'scripts\windows\validation\test-image-catalogue.ps1') -BackupFile $backup -EvidenceDirectory $integratedOut 2>&1 | Tee-Object -FilePath (Join-Path $runDir 'integrated-regression.log')
    $integratedSummaryPath = Join-Path $integratedOut 'validation-summary.json'
    if (-not (Test-Path -LiteralPath $integratedSummaryPath -PathType Leaf)) { throw "Integrated regression summary missing: $integratedSummaryPath" }
    $integratedSummary = Get-Content -LiteralPath $integratedSummaryPath -Raw | ConvertFrom-Json
    if ($integratedSummary.status -ne 'PASSED') { throw "Integrated regression status is $($integratedSummary.status)." }
    if ($null -ne $integratedSummary.cleanupFailures -and $integratedSummary.cleanupFailures.Count -ne 0) { throw 'Integrated regression reported cleanup failures.' }
    $summary.clientTests = [int]$integratedSummary.clientTests
    $summary.responderTests = [int]$integratedSummary.responder.tests
    $summary.webTests = [int]$integratedSummary.web.tests
    $summary.integratedRegression = $true
    $summary.clientBuild = $true
    $summary.javaTestBuild = $true

    Write-Host 'Checking that required named responder/web regression contracts executed and were not skipped...'
    Invoke-Step14LoggedCommand -Program $Python -Arguments @((Join-Path $PSScriptRoot 'check-step14-test-reports.py'),'--project-root',$ProjectRoot,'--output',(Join-Path $runDir 'test-report-check.json')) -LogPath (Join-Path $runDir 'test-report-check.log') -WorkingDirectory $ProjectRoot
    $summary.requiredReports = $true

    Write-Host 'Running disposable cross-component ImageFragment reader/browser verification against the current source candidate...'
    $readerOut = Join-Path $runDir 'reader-cross-component'
    & (Join-Path $ProjectRoot 'scripts\windows\validation\verify-imagefragment-reader.ps1') -BackupFile $backup -EvidenceDirectory $readerOut -ChromeBin $chrome -Python $Python 2>&1 | Tee-Object -FilePath (Join-Path $runDir 'reader-cross-component.log')
    $readerSummaryPath = Join-Path $readerOut 'evidence\summary.json'
    if (-not (Test-Path -LiteralPath $readerSummaryPath -PathType Leaf)) { throw "Reader summary missing: $readerSummaryPath" }
    $readerSummary = Get-Content -LiteralPath $readerSummaryPath -Raw | ConvertFrom-Json
    if ($readerSummary.status -ne 'PASSED') { throw "Reader summary status is $($readerSummary.status)." }
    if ($null -ne $readerSummary.cleanupFailures -and $readerSummary.cleanupFailures.Count -ne 0) { throw 'Reader verification reported cleanup failures.' }
    $summary.readerCrossComponent = $true

    Write-Host 'Rendering local-docker-build Compose configuration (quiet; no secrets written)...'
    Invoke-Step14LoggedCommand -Program 'docker' -Arguments @('compose','--env-file',(Join-Path $ProjectRoot 'config\environments\local-docker-build.env'),'--env-file',(Join-Path $ProjectRoot 'config\environments\local.env'),'-f',(Join-Path $ProjectRoot 'compose.local-docker-build.yaml'),'config','--quiet') -LogPath (Join-Path $runDir 'compose-local-docker-build.txt') -WorkingDirectory $ProjectRoot
    $summary.composeLocalDockerBuild = $true

    Write-Host 'Rendering local-published-smoke Compose configuration (quiet; no secrets written)...'
    Invoke-Step14LoggedCommand -Program 'docker' -Arguments @('compose','--env-file',(Join-Path $ProjectRoot 'config\environments\local-published-smoke.env'),'--env-file',(Join-Path $ProjectRoot 'config\environments\local.env'),'-f',(Join-Path $ProjectRoot 'compose.local-published-smoke.yaml'),'config','--quiet') -LogPath (Join-Path $runDir 'compose-local-published-smoke.txt') -WorkingDirectory $ProjectRoot
    $summary.composeLocalPublishedSmoke = $true

    Write-Host 'Running git diff --check hygiene on parent and component repositories...'
    foreach($item in @(
        @{Path=$ProjectRoot;Name='parent'},
        @{Path=(Join-Path $ProjectRoot 'diaries-client');Name='diaries-client'},
        @{Path=(Join-Path $ProjectRoot 'diaries-responder');Name='diaries-responder'},
        @{Path=(Join-Path $ProjectRoot 'diaries-web');Name='diaries-web'}
    )) {
        Invoke-Step14LoggedCommand -Program 'git' -Arguments @('-c',"safe.directory=$($item.Path.Replace('\','/'))",'-C',$item.Path,'diff','--check') -LogPath (Join-Path $runDir ("{0}-diff-check.txt" -f $item.Name)) -WorkingDirectory $ProjectRoot
    }
    $summary.diffChecks = $true

    Write-Host 'Capturing source/config SHA-256 inventory...'
    $hashRoots = @(
        'diaries-client\src','diaries-client\public\assets','diaries-client\package.json','diaries-client\package-lock.json',
        'diaries-responder\src','diaries-responder\build.gradle',
        'diaries-web\src','diaries-web\config','diaries-web\build.gradle',
        'config\mosquitto\aclfile.txt','compose.local-docker-build.yaml','compose.local-published-smoke.yaml',
        'scripts\windows\validation\test-image-catalogue.ps1','scripts\windows\validation\image-catalogue-test-mosquitto.conf',
        'scripts\windows\validation\verify-imagefragment-reader.ps1','scripts\windows\validation\smoke-imagefragment-reader.cjs',
        'change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 14\tooling'
    )
    $hashLines = New-Object System.Collections.Generic.List[string]
    foreach($relative in $hashRoots) {
        $path=Join-Path $ProjectRoot $relative
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
            $hashLines.Add("$hash  $($relative.Replace('\','/'))")
        } elseif (Test-Path -LiteralPath $path -PathType Container) {
            Get-ChildItem -LiteralPath $path -Recurse -File | Sort-Object FullName | ForEach-Object {
                $rel=[System.IO.Path]::GetRelativePath($ProjectRoot,$_.FullName).Replace('\','/')
                $hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
                $hashLines.Add("$hash  $rel")
            }
        }
    }
    Write-Utf8NoBom -Path (Join-Path $runDir 'source-files.sha256') -Text (($hashLines -join [Environment]::NewLine)+[Environment]::NewLine)

    $summary.status = 'PASSED'
    Write-Host 'Step 14 full regression PASSED. Run the rollout rehearsal before closing Step 14.' -ForegroundColor Green
} catch {
    $summary.status = 'FAILED'
    $summary.failure = $_.Exception.Message
    Write-Host "Step 14 regression FAILED: $($_.Exception.Message)" -ForegroundColor Red
    throw
} finally {
    $summary.finishedAtLocal = (Get-Date).ToString('o')
    Write-Utf8NoBom -Path $summaryPath -Text (($summary | ConvertTo-Json -Depth 8)+[Environment]::NewLine)
    $env:CHROME_BIN = $previousChrome
}
