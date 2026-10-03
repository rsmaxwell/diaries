param(
    [Parameter(Mandatory = $true)]
    [string]$PlaybooksRoot
)

$ErrorActionPreference = 'Stop'
$PlaybooksRoot = (Resolve-Path $PlaybooksRoot).Path
$Patch = Join-Path $PSScriptRoot 'playbooks-0032-step5.patch'
$CopyTasks = Join-Path $PlaybooksRoot 'roles\diaries\tasks\copy.yaml'
if (-not (Test-Path $CopyTasks)) {
    throw "Not a Playbooks root: $PlaybooksRoot"
}

Push-Location $PlaybooksRoot
try {
    $NewTest = 'roles\diaries\tests\verify-production-deployment-contract.py'
    $OldScript = 'roles\diaries\files\sync\scripts\step14-production-deployment.sh'
    $OldTest = 'roles\diaries\tests\verify-0031-step14.py'

    if ((Test-Path $NewTest) -and -not (Test-Path $OldScript) -and -not (Test-Path $OldTest)) {
        Write-Host 'Step 5 source patch appears to be already applied; running validation only.'
    }
    else {
        & git apply --check $Patch
        if ($LASTEXITCODE -ne 0) { throw 'git apply --check failed' }
        & git apply $Patch
        if ($LASTEXITCODE -ne 0) { throw 'git apply failed' }
        Write-Host 'Applied Step 5 Playbooks source patch.'
    }

    & python roles/diaries/tests/verify-production-backup-restore-semantics.py
    if ($LASTEXITCODE -ne 0) { throw 'backup/restore regression failed' }
    & python roles/diaries/tests/verify-production-storage-isolation.py
    if ($LASTEXITCODE -ne 0) { throw 'storage-isolation regression failed' }
    & python roles/diaries/tests/verify-production-deployment-contract.py
    if ($LASTEXITCODE -ne 0) { throw 'production-deployment regression failed' }

    Write-Host ''
    Write-Host 'PASS: Step 5 Playbooks source application and validation completed.'
    Write-Host 'No playbook deployment has been run by this script.'
}
finally {
    Pop-Location
}
