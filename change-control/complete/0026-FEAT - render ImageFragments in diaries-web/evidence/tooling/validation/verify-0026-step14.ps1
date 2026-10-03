#Requires -Version 7.0
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [string]$Python = 'python',
    [switch]$FullResponder,
    [switch]$Client,
    [string]$BackupFile,
    [string]$LocalBuildEnvFile,
    [string]$PublishedSmokeEnvFile,
    [switch]$InspectPublishedImages,
    [switch]$PreflightOnly
)
$ErrorActionPreference = 'Stop'
$arguments = @((Join-Path $PSScriptRoot 'verify-0026-step14.py'), '--evidence', $EvidenceDirectory)
if ($FullResponder) { $arguments += '--full-responder' }
if ($Client) { $arguments += '--client' }
if ($BackupFile) { $arguments += @('--backup', (Resolve-Path -LiteralPath $BackupFile).Path) }
if ($LocalBuildEnvFile) { $arguments += @('--build-env', (Resolve-Path -LiteralPath $LocalBuildEnvFile).Path) }
if ($PublishedSmokeEnvFile) { $arguments += @('--published-env', (Resolve-Path -LiteralPath $PublishedSmokeEnvFile).Path) }
if ($InspectPublishedImages) { $arguments += '--inspect-published' }
if ($PreflightOnly) { $arguments += '--preflight-only' }
& $Python @arguments
if ($LASTEXITCODE -ne 0) { throw 'Step 14 is not complete. Inspect the new evidence directory RESULTS.json and logs.' }
