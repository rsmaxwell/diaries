#Requires -Version 5.1
param(
    [string]$EvidenceDirectory = (Join-Path $PSScriptRoot 'deployment/final-run'),
    [switch]$ApplyDocumentation
)
$ErrorActionPreference = 'Stop'
$runner = Join-Path $PSScriptRoot 'deployment/run-deployment.py'
$finaliser = Join-Path $PSScriptRoot 'closeout/finalise-step15.py'

# Preserve, rather than overwrite, an earlier failed/incomplete final-run.
if (Test-Path $EvidenceDirectory) {
    $status = $null
    $resultPath = Join-Path $EvidenceDirectory 'result.json'
    if (Test-Path $resultPath) {
        try { $status = (Get-Content $resultPath -Raw | ConvertFrom-Json).status } catch { }
    }
    if ($status -eq 'PASSED') {
        throw "A PASSED Step 15 deployment evidence directory already exists: $EvidenceDirectory"
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
    $archive = Join-Path (Split-Path $EvidenceDirectory -Parent) ("failed-run-$stamp")
    Write-Host "Archiving previous failed/incomplete run to: $archive"
    Move-Item $EvidenceDirectory $archive
}

Write-Host 'Starting Step 15 controlled deployment validation...'
python $runner $EvidenceDirectory
if ($LASTEXITCODE -ne 0) { throw "Step 15 deployment validation failed; see $EvidenceDirectory\result.json" }

Write-Host 'Deployment validation passed; running Step 15 close-out validation...'
$args = @($finaliser, $EvidenceDirectory)
if ($ApplyDocumentation) { $args += '--apply-docs' }
python @args
if ($LASTEXITCODE -ne 0) { throw 'Step 15 close-out validation failed.' }

Write-Host "Step 15 deployment validation passed."
Write-Host "Evidence: $EvidenceDirectory"
if ($ApplyDocumentation) {
    Write-Host 'Feature README and IMPLEMENTATION-STEPS-0025.md were updated after the verified pass.'
} else {
    Write-Host 'Feature documentation was not modified. Re-run the finaliser with --apply-docs when ready.'
}
