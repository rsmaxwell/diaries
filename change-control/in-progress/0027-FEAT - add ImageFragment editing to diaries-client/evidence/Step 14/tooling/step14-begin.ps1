param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step14-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$buildRoot = Get-Step14BuildRoot -ProjectRoot $ProjectRoot
$runId = Get-Date -Format 'yyyyMMdd-HHmmss'
$runDir = Join-Path (Join-Path $buildRoot 'runs') $runId
New-Item -ItemType Directory -Path $runDir -Force | Out-Null
Write-Utf8NoBom -Path (Join-Path $buildRoot 'current-run.txt') -Text ($runId + [Environment]::NewLine)
$metadata = New-Object System.Collections.Generic.List[string]
$metadata.Add("runId=$runId")
$metadata.Add("startedLocal=$((Get-Date).ToString('o'))")
$metadata.Add("projectRoot=$ProjectRoot")
foreach ($line in Get-GitIdentityLines -Path $ProjectRoot -Label 'parent') { $metadata.Add($line) }
foreach ($component in @('diaries-client','diaries-responder','diaries-web')) {
    foreach ($line in Get-GitIdentityLines -Path (Join-Path $ProjectRoot $component) -Label $component) { $metadata.Add($line) }
}
Write-Utf8NoBom -Path (Join-Path $runDir 'run-metadata.txt') -Text (($metadata -join [Environment]::NewLine) + [Environment]::NewLine)
Write-Host "Step 14 evidence run created: $runId"
Write-Host "Run directory: $runDir"
Write-Host 'The run directory is under ignored build/; no credentials are copied by Step 14 tooling.'
Write-Output $runDir
