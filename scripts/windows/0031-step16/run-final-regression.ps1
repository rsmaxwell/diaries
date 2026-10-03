[CmdletBinding()]
param(
    [string]$PlaybooksSshHost = 'mango',
    [string]$RemotePlaybooksRoot = '/home/richard/playbooks',
    [string]$OutputRoot = '',
    [switch]$SkipClientBuild,
    [switch]$SkipJavaTests
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    throw "0031 Step 16 final regression: $Message"
}

function Find-Python {
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return [pscustomobject]@{ Command = $python.Source; Prefix = @() }
    }
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return [pscustomobject]@{ Command = $py.Source; Prefix = @('-3') }
    }
    Fail 'Python 3 was not found on PATH (python or py -3).'
}

function Invoke-Captured {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$LogFile,
        [string]$WorkingDirectory = ''
    )

    "COMMAND: $Command $($Arguments -join ' ')" | Set-Content -LiteralPath $LogFile -Encoding UTF8
    "WORKING DIRECTORY: $WorkingDirectory" | Add-Content -LiteralPath $LogFile -Encoding UTF8
    "" | Add-Content -LiteralPath $LogFile -Encoding UTF8

    if ($WorkingDirectory) { Push-Location $WorkingDirectory }
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        # Native programs may legitimately write to stderr.  Windows PowerShell 5.1
        # converts redirected native stderr into ErrorRecord objects, so the script-wide
        # ErrorActionPreference=Stop would otherwise abort before LASTEXITCODE can be
        # examined.  Capture the complete output and judge the child by its exit code.
        $ErrorActionPreference = 'Continue'
        & $Command @Arguments 2>&1 | Tee-Object -FilePath $LogFile -Append
        $rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
        if ($WorkingDirectory) { Pop-Location }
    }

    if ($rc -ne 0) {
        Fail "$Label failed with exit code $rc. See $LogFile"
    }
    Write-Host "PASS: $Label"
}


function Quote-ShSingle([string]$Value) {
    if ($Value.Contains("'")) {
        Fail "remote shell value contains an unsupported single quote: $Value"
    }
    return "'" + $Value + "'"
}

function Invoke-RemoteCaptured {
    param(
        [Parameter(Mandatory = $true)][string]$Label,
        [Parameter(Mandatory = $true)][string]$RemoteCommand,
        [Parameter(Mandatory = $true)][string]$LogFile,
        [Parameter(Mandatory = $true)][string]$SshCommand
    )

    Invoke-Captured -Label $Label -Command $SshCommand `
        -Arguments @($PlaybooksSshHost, $RemoteCommand) -LogFile $LogFile
}

function Invoke-PairValidation {
    param(
        [Parameter(Mandatory = $true)][string]$Mode,
        [Parameter(Mandatory = $true)][string]$ModeFile,
        [Parameter(Mandatory = $true)][string]$LocalFile,
        [Parameter(Mandatory = $true)][bool]$ExpectSuccess,
        [Parameter(Mandatory = $true)][string]$LogFile
    )

    $validator = Join-Path $projectRoot 'scripts\windows\common\validate-dataset-pair.ps1'
    $savedErrorActionPreference = $ErrorActionPreference
    try {
        # A non-zero exit is the expected result for the negative fixture.  Do not let
        # Windows PowerShell turn the child's stderr into a terminating NativeCommandError
        # before we can test LASTEXITCODE.
        $ErrorActionPreference = 'Continue'
        & powershell -NoProfile -ExecutionPolicy Bypass -File $validator `
            -ModeName $Mode -ModeEnvironmentFile $ModeFile -LocalEnvironmentFile $LocalFile `
            *> $LogFile
        $rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedErrorActionPreference
    }

    if ($ExpectSuccess -and $rc -ne 0) {
        Fail "dataset-pair validation unexpectedly failed for $Mode. See $LogFile"
    }
    if ((-not $ExpectSuccess) -and $rc -eq 0) {
        Fail "dataset-pair validation unexpectedly accepted the one-sided override for $Mode. See $LogFile"
    }
}

function Parse-DotEnv([string]$Path) {
    $values = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = $raw.Trim()
        if (-not $line -or $line.StartsWith('#') -or $line.IndexOf('=') -lt 1) { continue }
        $parts = $line.Split('=', 2)
        $values[$parts[0].Trim()] = $parts[1].Trim()
    }
    return $values
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $scriptDir '..\..\..')).Path
$featureDir = Join-Path $projectRoot 'change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment'
$step16Dir = Join-Path $featureDir 'evidence\Step 16'
$timestamp = Get-Date -Format 'yyyyMMdd-HHmmss'
if (-not $OutputRoot) {
    $OutputRoot = Join-Path $step16Dir 'runtime'
}
New-Item -ItemType Directory -Force -Path $OutputRoot | Out-Null
$runDir = Join-Path $OutputRoot "final-regression-$timestamp"
New-Item -ItemType Directory -Force -Path $runDir | Out-Null

$python = Find-Python
$ssh = Get-Command ssh -ErrorAction SilentlyContinue
if (-not $ssh) {
    Fail 'OpenSSH client (ssh) was not found on PATH. Step 16 verifies the Playbooks repository remotely on mango.'
}
if (-not $PlaybooksSshHost) { Fail 'PlaybooksSshHost must not be empty.' }
if (-not $RemotePlaybooksRoot) { Fail 'RemotePlaybooksRoot must not be empty.' }

$quotedRemoteRoot = Quote-ShSingle $RemotePlaybooksRoot
$remotePreflight = "test -d $quotedRemoteRoot && test -f $quotedRemoteRoot/roles/diaries/tests/verify-0031-step14.py && printf 'OK\n'"
Invoke-RemoteCaptured -Label 'Playbooks SSH/repository preflight' -RemoteCommand $remotePreflight `
    -LogFile (Join-Path $runDir 'playbooks-ssh-preflight.txt') -SshCommand $ssh.Source

$summary = Join-Path $runDir 'FINAL-REGRESSION-SUMMARY.txt'
"0031-FEAT Step 16 final regression" | Set-Content -LiteralPath $summary -Encoding UTF8
"Captured: $((Get-Date).ToUniversalTime().ToString('o'))" | Add-Content -LiteralPath $summary -Encoding UTF8
"Diaries root: $projectRoot" | Add-Content -LiteralPath $summary -Encoding UTF8
"Playbooks SSH host: $PlaybooksSshHost" | Add-Content -LiteralPath $summary -Encoding UTF8
"Playbooks remote root: $RemotePlaybooksRoot" | Add-Content -LiteralPath $summary -Encoding UTF8
"" | Add-Content -LiteralPath $summary -Encoding UTF8

# 1. Portable 0031 source/contract regression checks.
$diariesChecks = @(
    'verify-0031-step3.py',
    'verify-0031-step4.py',
    'verify-0031-step6.py',
    'verify-0031-step7.py',
    'verify-0031-step8.py',
    'verify-0031-step9.py',
    'verify-0031-step10.py',
    'verify-0031-step11.py',
    'verify-0031-step13.py',
    'verify-0031-step16.py'
)
foreach ($check in $diariesChecks) {
    $path = Join-Path $projectRoot "scripts\windows\validation\$check"
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { Fail "missing Diaries validation: $path" }
    $args = @(); $args += $python.Prefix; $args += @($path)
    Invoke-Captured -Label "Diaries $check" -Command $python.Command -Arguments $args `
        -LogFile (Join-Path $runDir ("diaries-" + $check.Replace('.py','.txt'))) -WorkingDirectory $projectRoot
}

$playbookChecks = @(
    'verify-0031-storage-isolation.py',
    'verify-0031-backup-semantics.py',
    'verify-0031-step8.py',
    'verify-0031-step9.py',
    'verify-0031-step13.py',
    'verify-0031-step14.py'
)
foreach ($check in $playbookChecks) {
    $remotePath = "roles/diaries/tests/$check"
    $remoteCommand = "cd $quotedRemoteRoot && python3 " + (Quote-ShSingle $remotePath)
    Invoke-RemoteCaptured -Label "Playbooks $check on $PlaybooksSshHost" -RemoteCommand $remoteCommand `
        -LogFile (Join-Path $runDir ("playbooks-" + $check.Replace('.py','.txt'))) -SshCommand $ssh.Source
}

# Capture the exact remote Playbooks Git state as additional release-candidate identity.
$remoteGit = "cd $quotedRemoteRoot && printf 'HEAD: ' && git rev-parse HEAD && printf '%s\n' 'STATUS:' && git status --short"
Invoke-RemoteCaptured -Label "Playbooks Git identity on $PlaybooksSshHost" -RemoteCommand $remoteGit `
    -LogFile (Join-Path $runDir 'PLAYBOOKS-GIT-IDENTITY.txt') -SshCommand $ssh.Source

# 2. Explicit precedence/paired-override regression using temporary local.env files.
$temp = Join-Path $runDir 'precedence-fixtures'
New-Item -ItemType Directory -Force -Path $temp | Out-Null
$emptyLocal = Join-Path $temp 'local-empty.env'
$commonLocal = Join-Path $temp 'local-common.env'
$dbOnlyLocal = Join-Path $temp 'local-db-only.env'
"# intentionally empty Step 16 override" | Set-Content -LiteralPath $emptyLocal -Encoding ASCII
@(
    'DIARIES_DB_DATA_DIR=./data/database/common',
    'DIARIES_FILES_DIR=files-development-common'
) | Set-Content -LiteralPath $commonLocal -Encoding ASCII
'DIARIES_DB_DATA_DIR=./data/database/common' | Set-Content -LiteralPath $dbOnlyLocal -Encoding ASCII

$modes = @('development-infrastructure','local-docker-build','local-published-smoke')
$map = @('# 0031 Step 16 final effective path map', '', '| Mode | Isolated committed database | Isolated committed Files | Test common database | Test common Files |', '| --- | --- | --- | --- | --- |')
foreach ($mode in $modes) {
    $modeFile = Join-Path $projectRoot "config\environments\$mode.env"
    $env = Parse-DotEnv $modeFile
    Invoke-PairValidation -Mode $mode -ModeFile $modeFile -LocalFile $emptyLocal -ExpectSuccess $true `
        -LogFile (Join-Path $runDir "pair-$mode-isolated.txt")
    Invoke-PairValidation -Mode $mode -ModeFile $modeFile -LocalFile $commonLocal -ExpectSuccess $true `
        -LogFile (Join-Path $runDir "pair-$mode-common.txt")
    Invoke-PairValidation -Mode $mode -ModeFile $modeFile -LocalFile $dbOnlyLocal -ExpectSuccess $false `
        -LogFile (Join-Path $runDir "pair-$mode-one-sided-rejected.txt")
    $map += "| $mode | $($env['DIARIES_DB_DATA_DIR']) | $($env['DIARIES_FILES_DIR']) | ./data/database/common | files-development-common |"
}
$map += ''
$map += 'The common rows above are a temporary Step 16 precedence fixture. They do not modify the developer-owned ignored `config/environments/local.env`.'
$map | Set-Content -LiteralPath (Join-Path $runDir 'FINAL-EFFECTIVE-PATH-MAP.md') -Encoding UTF8

# 3. Application regression on the exact Diaries candidate.
if (-not $SkipJavaTests) {
    $gradle = Join-Path $projectRoot 'gradlew.bat'
    if (-not (Test-Path -LiteralPath $gradle -PathType Leaf)) { Fail "Gradle wrapper not found: $gradle" }
    Invoke-Captured -Label 'full Java responder/web test suite' -Command $gradle `
        -Arguments @('test','--console=plain') -LogFile (Join-Path $runDir 'gradle-test.txt') -WorkingDirectory $projectRoot
}
else {
    'SKIPPED by -SkipJavaTests' | Set-Content -LiteralPath (Join-Path $runDir 'gradle-test.txt') -Encoding ASCII
}

if (-not $SkipClientBuild) {
    $npm = Get-Command npm -ErrorAction SilentlyContinue
    if (-not $npm) { Fail 'npm was not found on PATH; use -SkipClientBuild only when the omission is explicitly reviewed.' }
    $client = Join-Path $projectRoot 'diaries-client'
    Invoke-Captured -Label 'Angular client production build' -Command $npm.Source `
        -Arguments @('run','build') -LogFile (Join-Path $runDir 'client-build.txt') -WorkingDirectory $client
}
else {
    'SKIPPED by -SkipClientBuild' | Set-Content -LiteralPath (Join-Path $runDir 'client-build.txt') -Encoding ASCII
}

# 4. Source identity for the exact candidate tested. Avoid generated/build trees and secrets.
$diariesIdentityFiles = @(
    'compose.local-docker-build.yaml',
    'compose.local-published-smoke.yaml',
    'config/environments/development-infrastructure.env',
    'config/environments/local-docker-build.env',
    'config/environments/local-published-smoke.env',
    'config/environments/local.env.example',
    'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java',
    'diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/ListFiles.java',
    'scripts/windows/common/validate-dataset-pair.ps1',
    'scripts/windows/development-infrastructure/prepare-responder-config.bat',
    'scripts/windows/development-infrastructure/prepare-responder-config.ps1',
    'scripts/windows/0031-step16/run-final-regression.ps1',
    'scripts/windows/0031-step16/rehearse-common-restore.ps1',
    'scripts/windows/validation/verify-0031-step16.py'
)
$diaryHashLines = foreach ($rel in $diariesIdentityFiles) {
    $file = Join-Path $projectRoot $rel
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { Fail "source identity file missing: $rel" }
    $h = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant()
    "$h  $($rel.Replace('\\','/'))"
}
$diaryHashLines | Set-Content -LiteralPath (Join-Path $runDir 'SOURCE-SHA256SUMS-DIARIES.txt') -Encoding ASCII

$playbookIdentityFiles = @(
    'roles/diaries/templates/.env.j2',
    'roles/diaries/templates/compose.yaml.j2',
    'roles/diaries/tasks/main.yaml',
    'roles/diaries/README.md',
    'roles/diaries/files/sync/scripts/README.md',
    'roles/diaries/tests/verify-0031-storage-isolation.py',
    'roles/diaries/tests/verify-0031-step14.py'
)
$remoteHashArgs = ($playbookIdentityFiles | ForEach-Object { Quote-ShSingle $_ }) -join ' '
$remoteHashCommand = "cd $quotedRemoteRoot && sha256sum -- $remoteHashArgs"
$savedErrorActionPreference = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    $playbookHashOutput = & $ssh.Source $PlaybooksSshHost $remoteHashCommand 2>&1
    $playbookHashRc = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $savedErrorActionPreference
}
if ($playbookHashRc -ne 0) {
    $playbookHashOutput | Set-Content -LiteralPath (Join-Path $runDir 'SOURCE-SHA256SUMS-PLAYBOOKS.txt') -Encoding UTF8
    Fail "remote Playbooks source identity failed with exit code $playbookHashRc"
}
$playbookHashOutput | Set-Content -LiteralPath (Join-Path $runDir 'SOURCE-SHA256SUMS-PLAYBOOKS.txt') -Encoding ASCII

"PASS: exact-candidate source/contract regression" | Add-Content -LiteralPath $summary -Encoding UTF8
"PASS: isolated/default, common paired override and one-sided rejection regression" | Add-Content -LiteralPath $summary -Encoding UTF8
if ($SkipJavaTests) { "REVIEW REQUIRED: Java tests skipped" | Add-Content -LiteralPath $summary -Encoding UTF8 } else { "PASS: full Java responder/web tests" | Add-Content -LiteralPath $summary -Encoding UTF8 }
if ($SkipClientBuild) { "REVIEW REQUIRED: Angular client build skipped" | Add-Content -LiteralPath $summary -Encoding UTF8 } else { "PASS: Angular client build" | Add-Content -LiteralPath $summary -Encoding UTF8 }
"" | Add-Content -LiteralPath $summary -Encoding UTF8
"This run is not by itself the Step 16 close-out: a successful disposable common-dataset restore/reconciliation rehearsal is also required." | Add-Content -LiteralPath $summary -Encoding UTF8
"Evidence: $runDir" | Add-Content -LiteralPath $summary -Encoding UTF8

$latest = Join-Path $step16Dir 'LATEST-FINAL-REGRESSION.txt'
$runDir | Set-Content -LiteralPath $latest -Encoding ASCII

Write-Host ''
Write-Host 'PASS: 0031-FEAT Step 16 final source/application regression completed.'
Write-Host "Evidence: $runDir"
Write-Host 'Next: run rehearse-common-restore.bat and preserve that evidence before closing 0031.'
