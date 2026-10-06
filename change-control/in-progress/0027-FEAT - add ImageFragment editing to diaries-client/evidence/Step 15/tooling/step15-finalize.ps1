param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step15-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep15RunDirectory -ProjectRoot $ProjectRoot
$failures = New-Object System.Collections.Generic.List[string]

function Require-TextFile([string]$name,[string[]]$mustContain) {
    $path = Join-Path $runDir $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $failures.Add("missing required evidence: $name"); return }
    $text = Get-Content -LiteralPath $path -Raw
    foreach($needle in $mustContain) {
        if ($text -notmatch $needle) { $failures.Add("$name does not contain required evidence matching: $needle") }
    }
}

try {
    $step14 = Get-Content -LiteralPath (Join-Path $runDir 'step14-final-summary.json') -Raw | ConvertFrom-Json
    if ([string]$step14.status -ne 'PASSED') { $failures.Add('Step 14 prerequisite is not PASSED') }
} catch { $failures.Add('Step 14 prerequisite summary is missing or invalid') }

Require-TextFile 'preflight.txt' @('PASS: Step 14 closure prerequisite is PASSED','PASS: production responder authoring gate is currently false')
Require-TextFile 'production-pre-deploy.txt' @('expectedGate=false','status=PASSED')
Require-TextFile 'production-post-client-disabled.txt' @('expectedGate=false','status=PASSED')
Require-TextFile 'production-pre-enable.txt' @('expectedGate=false','status=PASSED')
Require-TextFile 'production-post-enable.txt' @('expectedGate=true','status=PASSED')

foreach($name in @('CHECKLIST.md','MANUAL-EVIDENCE.md')) {
    $path = Join-Path $runDir $name
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { $failures.Add("missing run-local $name"); continue }
    $text = Get-Content -LiteralPath $path -Raw
    if ($text -match '(?m)^\s*- \[ \]') { $failures.Add("$name still contains unchecked acceptance items") }
    if ($text -match '________________') { $failures.Add("$name still contains unfilled placeholders") }
}

$summary = [ordered]@{
    step = 15
    runId = Split-Path -Leaf $runDir
    checkedAtLocal = (Get-Date).ToString('o')
    status = $(if($failures.Count -eq 0){'PASSED'}else{'FAILED'})
    finalGate = 'true'
    rollbackEvidenceRequired = $false
    failures = @($failures)
}
$out = Join-Path $runDir 'step15-final-summary.json'
Write-Utf8NoBom -Path $out -Text (($summary | ConvertTo-Json -Depth 6)+[Environment]::NewLine)
if ($failures.Count -gt 0) {
    foreach($failure in $failures){Write-Host "FAIL: $failure" -ForegroundColor Red}
    throw "Step 15 cannot close; $($failures.Count) condition(s) are not satisfied. See $out"
}
Write-Host "Step 15 closure gate PASSED: $out" -ForegroundColor Green
