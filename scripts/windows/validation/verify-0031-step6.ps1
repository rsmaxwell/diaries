$ErrorActionPreference = 'Stop'

$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..')).Path
$Guard = Join-Path $ProjectRoot 'scripts\windows\common\validate-dataset-pair.ps1'
$EnvironmentRoot = Join-Path $ProjectRoot 'config\environments'
$TempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ('diaries-0031-step6-' + [guid]::NewGuid().ToString('N'))

function Invoke-GuardCase {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$ModeEnv,
        [Parameter(Mandatory = $true)][string]$LocalEnv,
        [Parameter(Mandatory = $true)][bool]$ExpectSuccess
    )

    # Negative cases deliberately make the child PowerShell process write an
    # error to stderr and return exit code 1. With the suite-level
    # ErrorActionPreference=Stop, Windows PowerShell promotes that stderr to a
    # terminating NativeCommandError before we can inspect $LASTEXITCODE. Run
    # the child with Continue locally, capture both streams, then assert its
    # exit code ourselves.
    $previousErrorActionPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $caseOutput = & powershell -NoProfile -ExecutionPolicy Bypass -File $Guard `
            -ModeName $Mode `
            -ModeEnvironmentFile $ModeEnv `
            -LocalEnvironmentFile $LocalEnv 2>&1
        $exitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $previousErrorActionPreference
    }

    if ($ExpectSuccess -and $exitCode -ne 0) {
        throw "FAIL: $Name should have succeeded but returned $exitCode."
    }
    if (-not $ExpectSuccess -and $exitCode -eq 0) {
        throw "FAIL: $Name should have been rejected but succeeded."
    }

    Write-Host "PASS: $Name"
}

try {
    if (-not (Test-Path -LiteralPath $Guard -PathType Leaf)) {
        throw "Dataset-pair guard not found: $Guard"
    }

    New-Item -ItemType Directory -Path $TempRoot | Out-Null

    $emptyLocal = Join-Path $TempRoot 'local-isolated.env'
    @'
# Deliberately no durable-dataset override.
DIARIES_MQTT_HEALTH_USERNAME=test
'@ | Set-Content -LiteralPath $emptyLocal -Encoding ascii

    $commonLocal = Join-Path $TempRoot 'local-common.env'
    @'
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
'@ | Set-Content -LiteralPath $commonLocal -Encoding ascii

    $modes = @(
        'development-infrastructure',
        'local-docker-build',
        'local-published-smoke'
    )

    foreach ($mode in $modes) {
        $modeEnv = Join-Path $EnvironmentRoot ($mode + '.env')
        Invoke-GuardCase -Name "isolated defaults: $mode" -Mode $mode -ModeEnv $modeEnv -LocalEnv $emptyLocal -ExpectSuccess $true
        Invoke-GuardCase -Name "shared common pair: $mode" -Mode $mode -ModeEnv $modeEnv -LocalEnv $commonLocal -ExpectSuccess $true
    }

    $dbOnly = Join-Path $TempRoot 'local-db-only.env'
    'DIARIES_DB_DATA_DIR=./data/database/common' | Set-Content -LiteralPath $dbOnly -Encoding ascii
    Invoke-GuardCase -Name 'reject DB-only local.env override' -Mode 'local-docker-build' `
        -ModeEnv (Join-Path $EnvironmentRoot 'local-docker-build.env') -LocalEnv $dbOnly -ExpectSuccess $false

    $filesOnly = Join-Path $TempRoot 'local-files-only.env'
    'DIARIES_FILES_DIR=files-development-common' | Set-Content -LiteralPath $filesOnly -Encoding ascii
    Invoke-GuardCase -Name 'reject Files-only local.env override' -Mode 'local-docker-build' `
        -ModeEnv (Join-Path $EnvironmentRoot 'local-docker-build.env') -LocalEnv $filesOnly -ExpectSuccess $false

    $commonWithProductionFiles = Join-Path $TempRoot 'local-common-production-files.env'
    @'
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files
'@ | Set-Content -LiteralPath $commonWithProductionFiles -Encoding ascii
    Invoke-GuardCase -Name 'reject local database with production Files root' -Mode 'local-docker-build' `
        -ModeEnv (Join-Path $EnvironmentRoot 'local-docker-build.env') -LocalEnv $commonWithProductionFiles -ExpectSuccess $false

    $crossedKnownPair = Join-Path $TempRoot 'local-crossed-known-pair.env'
    @'
DIARIES_DB_DATA_DIR=./data/database/local-published-smoke
DIARIES_FILES_DIR=files-development-common
'@ | Set-Content -LiteralPath $crossedKnownPair -Encoding ascii
    Invoke-GuardCase -Name 'reject crossed approved local pair' -Mode 'local-published-smoke' `
        -ModeEnv (Join-Path $EnvironmentRoot 'local-published-smoke.env') -LocalEnv $crossedKnownPair -ExpectSuccess $false

    Write-Host 'PASS: 0031-FEAT Step 6 Windows dataset-pair regression checks'
}
finally {
    if (Test-Path -LiteralPath $TempRoot) {
        Remove-Item -LiteralPath $TempRoot -Recurse -Force
    }
}
