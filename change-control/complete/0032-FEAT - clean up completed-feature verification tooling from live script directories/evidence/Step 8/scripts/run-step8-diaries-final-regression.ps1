param(
    [string]$ProjectRoot
)

$ErrorActionPreference = 'Stop'

if (-not $ProjectRoot) {
    $ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..\..\..')).Path
}

$Step8Dir = Split-Path -Parent $PSScriptRoot
$Log = Join-Path $Step8Dir 'DIARIES-HOST-REGRESSION.txt'

function Invoke-Checked {
    param(
        [string]$Label,
        [string]$File,
        [string[]]$Arguments
    )

    Write-Host "`n=== $Label ==="
    & $File @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$Label failed with exit code $LASTEXITCODE"
    }
}

Push-Location $ProjectRoot
try {
    Start-Transcript -Path $Log -Force | Out-Null

    Invoke-Checked 'Windows live-script policy' 'python' @('scripts/windows/validation/verify-live-script-policy.py')
    Invoke-Checked 'Dataset-pair/storage regression' 'python' @('scripts/windows/validation/verify-dataset-pair-guard.py')
    Invoke-Checked 'Exact PowerShell dataset-pair guard cases' 'powershell.exe' @('-NoProfile','-ExecutionPolicy','Bypass','-File','scripts/windows/validation/verify-dataset-pair-guard.ps1')
    Invoke-Checked 'Local backup/restore semantics' 'python' @('scripts/windows/validation/verify-local-backup-restore-semantics.py')
    Invoke-Checked 'Direct-development Files configuration' 'python' @('scripts/windows/validation/verify-direct-development-files-config.py')
    Invoke-Checked 'Effective dataset diagnostics' 'python' @('scripts/windows/validation/verify-effective-dataset-diagnostics.py')
    Invoke-Checked 'Local dataset layout' 'python' @('scripts/windows/validation/verify-local-dataset-layout.py')

    Invoke-Checked 'Node ImageFragment HTTP tests' 'node' @('--test','scripts/windows/validation/imagefragment-image-http.test.cjs')
    Invoke-Checked 'Node ImageFragment proxy-routing tests' 'node' @('--test','scripts/windows/validation/imagefragment-proxy-routing.test.cjs')
    Invoke-Checked 'Node retained-snapshot tests' 'node' @('--test','scripts/windows/validation/imagefragment-retained-snapshot.test.cjs')

    Invoke-Checked 'Responder/web Java tests' '.\gradlew.bat' @('test','--no-daemon')
    Invoke-Checked 'Angular production build' 'npm.cmd' @('--prefix','diaries-client','run','build','--','--configuration','production')

    Write-Host "`nPASS: Diaries Step 8 host regression completed successfully."
}
finally {
    try { Stop-Transcript | Out-Null } catch {}
    Pop-Location
}
