param(
    [string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$PlaybooksRoot,
    [string]$PlaybooksHost,
    [string]$PlutoHost = 'pluto',
    [string]$ProductionProjectDir = '/home/richard/projects/diaries'
)
. (Join-Path $PSScriptRoot 'step15-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep15RunDirectory -ProjectRoot $ProjectRoot
$ProductionProjectDir = Assert-SafeRemotePath -Path $ProductionProjectDir
$failures = New-Object System.Collections.Generic.List[string]
$lines = New-Object System.Collections.Generic.List[string]
function Pass([string]$m){$lines.Add("PASS: $m");Write-Host "PASS: $m"}
function Fail([string]$m){$failures.Add($m);$lines.Add("FAIL: $m");Write-Host "FAIL: $m" -ForegroundColor Red}

$lines.Add("timestamp=$((Get-Date).ToString('o'))")
$step14Path = Join-Path $runDir 'step14-final-summary.json'
try {
    $s14 = Get-Content -LiteralPath $step14Path -Raw | ConvertFrom-Json
    if ([string]$s14.status -eq 'PASSED') { Pass "Step 14 closure prerequisite is PASSED (runId=$($s14.runId))" } else { Fail 'Step 14 closure prerequisite is not PASSED' }
} catch { Fail "Cannot read Step 14 summary: $($_.Exception.Message)" }

$remotePlaybooks = -not [string]::IsNullOrWhiteSpace($PlaybooksHost)
try {
    if ($remotePlaybooks) {
        $root = Assert-SafeRemotePath -Path $PlaybooksRoot
        $role = "$root/roles/diaries"
        $defaults = (Invoke-Step15Ssh -HostName $PlaybooksHost -Command "cat -- $role/defaults/main.yaml").Lines -join "`n"
        $main = (Invoke-Step15Ssh -HostName $PlaybooksHost -Command "cat -- $role/tasks/main.yaml").Lines -join "`n"
        $template = (Invoke-Step15Ssh -HostName $PlaybooksHost -Command "cat -- $role/templates/config/responder/responder.json.j2").Lines -join "`n"
        $copy = (Invoke-Step15Ssh -HostName $PlaybooksHost -Command "cat -- $role/tasks/copy.yaml").Lines -join "`n"
        $commit = (Invoke-Step15Ssh -HostName $PlaybooksHost -Command "git -C $root rev-parse HEAD").Lines -join ''
        $lines.Add("playbooks.commit=$commit")
    } else {
        $root = [System.IO.Path]::GetFullPath($PlaybooksRoot)
        $role = Join-Path $root 'roles\diaries'
        if (-not (Test-Path -LiteralPath $role -PathType Container)) { throw "PlaybooksRoot does not contain roles/diaries: $root" }
        $defaults = Get-Content -LiteralPath (Join-Path $role 'defaults\main.yaml') -Raw
        $main = Get-Content -LiteralPath (Join-Path $role 'tasks\main.yaml') -Raw
        $template = Get-Content -LiteralPath (Join-Path $role 'templates\config\responder\responder.json.j2') -Raw
        $copy = Get-Content -LiteralPath (Join-Path $role 'tasks\copy.yaml') -Raw
        foreach ($line in Get-GitIdentityLines -Path $root -Label 'playbooks') { $lines.Add($line) }
    }

    if ($defaults -match '(?m)^diaries_image_fragment_writes_enabled:\s*false\s*$') { Pass 'Playbooks authoring gate default is fail-closed' } else { Fail 'Playbooks authoring gate default is not explicitly false' }
    if ($template -match '"imageFragmentWritesEnabled"\s*:\s*\{\{\s*diaries_image_fragment_writes_enabled\s*\|\s*bool\s*\|\s*lower\s*\}\}') { Pass 'responder template renders the controlled authoring-gate variable' } else { Fail 'responder template does not render diaries_image_fragment_writes_enabled' }
    if ($main -match 'diaries_image_fragment_writes_enabled is boolean') { Pass 'Playbooks rejects non-boolean gate values' } else { Fail 'Playbooks does not validate the gate as a boolean' }
    if ($copy -match 'Validate rendered ImageFragment authoring gate') { Pass 'Playbooks validates the rendered responder gate' } else { Fail 'Playbooks does not validate the rendered responder gate' }
} catch { Fail $_.Exception.Message }

try {
    $ssh = Get-Command ssh -ErrorAction Stop
    Pass "ssh available: $($ssh.Source)"
    $project = Invoke-Step15Ssh -HostName $PlutoHost -Command "test -f $ProductionProjectDir/compose.yaml -a -f $ProductionProjectDir/.env -a -f $ProductionProjectDir/config/responder/responder.json && echo OK"
    if (($project.Lines -join '') -match 'OK') { Pass "production project is readable on ${PlutoHost}:$ProductionProjectDir" } else { Fail 'production project files were not confirmed' }
    $gate = Invoke-Step15Ssh -HostName $PlutoHost -Command "grep -E 'imageFragmentWritesEnabled[^:]*:[[:space:]]*(true|false)' $ProductionProjectDir/config/responder/responder.json" -AllowFailure
    $gateText = $gate.Lines -join "`n"
    if ($gate.ExitCode -eq 0 -and $gateText -match '"imageFragmentWritesEnabled"\s*:\s*false') { Pass 'production responder authoring gate is currently false' } else { Fail 'production responder authoring gate is not false; stop before any Step 15 deployment' }
    $health = Invoke-Step15Ssh -HostName $PlutoHost -Command "cd $ProductionProjectDir && docker compose --file compose.yaml --env-file .env ps --format json"
    if ($health.Lines.Count -gt 0) { Pass 'production Compose status is readable' } else { Fail 'production Compose returned no service status' }
} catch { Fail $_.Exception.Message }

$out = Join-Path $runDir 'preflight.txt'
Write-Utf8NoBom -Path $out -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
if ($failures.Count -gt 0) { throw "Step 15 preflight FAILED with $($failures.Count) condition(s). See $out" }
Write-Host "Step 15 preflight PASSED: $out" -ForegroundColor Green
Write-Host 'The gate remains false. No authoring enablement was performed.'
