param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step14-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep14RunDirectory -ProjectRoot $ProjectRoot
$failures = New-Object System.Collections.Generic.List[string]

function Require-PassedJson {
    param([Parameter(Mandatory=$true)][string]$Path,[Parameter(Mandatory=$true)][string]$Label)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { $failures.Add("$Label is missing: $Path"); return $null }
    try { $value = Get-Content -LiteralPath $Path -Raw | ConvertFrom-Json }
    catch { $failures.Add("$Label is not valid JSON: $Path"); return $null }
    if ([string]$value.status -ne 'PASSED') { $failures.Add("$Label status is '$($value.status)', not PASSED") }
    return $value
}

$regression = Require-PassedJson -Path (Join-Path $runDir 'regression-summary.json') -Label 'regression summary'
$reports = Require-PassedJson -Path (Join-Path $runDir 'test-report-check.json') -Label 'required JUnit report check'
$reader = Require-PassedJson -Path (Join-Path $runDir 'reader-cross-component\evidence\summary.json') -Label 'reader cross-component summary'

$rehearsalPath = Join-Path $runDir 'rollout-rehearsal.txt'
if (-not (Test-Path -LiteralPath $rehearsalPath -PathType Leaf)) {
    $failures.Add("rollout rehearsal is missing: $rehearsalPath")
} else {
    $rehearsal = Get-Content -LiteralPath $rehearsalPath -Raw
    if ($rehearsal -match '(?m)^FAIL:') { $failures.Add('rollout rehearsal contains one or more FAIL lines') }
    if ($rehearsal -notmatch 'production responder template keeps ImageFragment authoring disabled') { $failures.Add('rollout rehearsal did not prove the production authoring gate remains disabled') }
    if ($rehearsal -notmatch 'STOP: Step 14 does not change the gate') { $failures.Add('rollout rehearsal does not contain the explicit Step 14 stop-before-enable boundary') }
}

foreach($required in @('preflight.txt','source-files.sha256')) {
    if (-not (Test-Path -LiteralPath (Join-Path $runDir $required) -PathType Leaf)) { $failures.Add("required evidence missing: $required") }
}

$step13Readme = Join-Path $ProjectRoot 'change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 13\README.md'
if (-not (Test-Path -LiteralPath $step13Readme -PathType Leaf)) {
    $failures.Add('Step 13 README is missing')
} else {
    $step13 = Get-Content -LiteralPath $step13Readme -Raw
    if ($step13 -notmatch '(?i)status:\s*(complete|closed)') { $failures.Add('Step 13 source record is not yet marked complete/closed') }
}

$summary = [ordered]@{
    step = 14
    runId = Split-Path -Leaf $runDir
    checkedAtLocal = (Get-Date).ToString('o')
    status = $(if($failures.Count -eq 0){'PASSED'}else{'FAILED'})
    clientTests = $(if($null -ne $regression){$regression.clientTests}else{$null})
    responderTests = $(if($null -ne $regression){$regression.responderTests}else{$null})
    webTests = $(if($null -ne $regression){$regression.webTests}else{$null})
    readerStatus = $(if($null -ne $reader){$reader.status}else{$null})
    failures = @($failures)
}
$out = Join-Path $runDir 'step14-final-summary.json'
Write-Utf8NoBom -Path $out -Text (($summary | ConvertTo-Json -Depth 8)+[Environment]::NewLine)
if($failures.Count -gt 0){
    foreach($failure in $failures){Write-Host "FAIL: $failure" -ForegroundColor Red}
    throw "Step 14 cannot close; $($failures.Count) closure condition(s) are not satisfied. See $out"
}
Write-Host "Step 14 closure gate PASSED: $out" -ForegroundColor Green
