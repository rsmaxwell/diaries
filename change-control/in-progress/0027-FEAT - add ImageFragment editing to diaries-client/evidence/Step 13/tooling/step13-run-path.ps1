param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
Write-Output (Get-CurrentStep13RunDirectory -ProjectRoot $ProjectRoot)
