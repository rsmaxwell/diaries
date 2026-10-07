param(
    [string]$ProjectRoot,
    [string]$Step14Summary,
    [string]$RunId
)
. (Join-Path $PSScriptRoot 'step15-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$step14 = Find-PassedStep14Summary -ProjectRoot $ProjectRoot -Step14Summary $Step14Summary
if ([string]::IsNullOrWhiteSpace($RunId)) { $RunId = (Get-Date).ToString('yyyyMMdd-HHmmss') }
if ($RunId -notmatch '^[A-Za-z0-9._-]+$') { throw "Unsafe RunId: $RunId" }

$buildRoot = Get-Step15BuildRoot -ProjectRoot $ProjectRoot
$runDir = Join-Path (Join-Path $buildRoot 'runs') $RunId
if (Test-Path -LiteralPath $runDir) { throw "Step 15 run already exists: $runDir" }
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
New-Item -ItemType Directory -Path $buildRoot -Force | Out-Null
Write-Utf8NoBom -Path (Join-Path $buildRoot 'current-run.txt') -Text ($RunId + [Environment]::NewLine)
Copy-Item -LiteralPath $step14 -Destination (Join-Path $runDir 'step14-final-summary.json')

$evidenceRoot = Join-Path $ProjectRoot 'change-control\in-progress\0027-FEAT - add ImageFragment editing to diaries-client\evidence\Step 15'
Copy-Item -LiteralPath (Join-Path $evidenceRoot 'CHECKLIST.md') -Destination (Join-Path $runDir 'CHECKLIST.md')
Copy-Item -LiteralPath (Join-Path $evidenceRoot 'MANUAL-EVIDENCE.md') -Destination (Join-Path $runDir 'MANUAL-EVIDENCE.md')

$lines = New-Object System.Collections.Generic.List[string]
$lines.Add("step=15")
$lines.Add("runId=$RunId")
$lines.Add("startedAtLocal=$((Get-Date).ToString('o'))")
$lines.Add("projectRoot=$ProjectRoot")
$lines.Add("step14Summary=$step14")
foreach ($pair in @(
    @{ Label='diaries'; Path=$ProjectRoot },
    @{ Label='client'; Path=(Join-Path $ProjectRoot 'diaries-client') },
    @{ Label='responder'; Path=(Join-Path $ProjectRoot 'diaries-responder') },
    @{ Label='web'; Path=(Join-Path $ProjectRoot 'diaries-web') }
)) {
    foreach ($line in Get-GitIdentityLines -Path $pair.Path -Label $pair.Label) { $lines.Add($line) }
}
Write-Utf8NoBom -Path (Join-Path $runDir 'begin.txt') -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
Write-Host "Step 15 run created: $runDir" -ForegroundColor Green
Write-Host "Step 14 prerequisite: PASSED ($step14)"
Write-Host 'No production action has been performed.'
