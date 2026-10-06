param(
    [string]$ProjectRoot,
    [Parameter(Mandatory=$true)][string]$PlaybooksRoot,
    [string]$PlaybooksHost
)
. (Join-Path $PSScriptRoot 'step14-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep14RunDirectory -ProjectRoot $ProjectRoot
$remoteMode = -not [string]::IsNullOrWhiteSpace($PlaybooksHost)
if (-not $remoteMode) { $PlaybooksRoot = [System.IO.Path]::GetFullPath($PlaybooksRoot) }
$failures = New-Object System.Collections.Generic.List[string]
$lines = New-Object System.Collections.Generic.List[string]
function Pass([string]$m){$lines.Add("PASS: $m");Write-Host "PASS: $m"}
function Fail([string]$m){$failures.Add($m);$lines.Add("FAIL: $m");Write-Host "FAIL: $m" -ForegroundColor Red}
function Assert-SafeRemotePath([string]$value) {
    if ($value -notmatch '^/[A-Za-z0-9._/-]+$') {
        throw "Remote Playbooks path contains unsupported shell characters: $value"
    }
    return $value.TrimEnd('/')
}
function Invoke-RemoteLines([string]$command) {
    $result = & ssh $PlaybooksHost $command 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Remote command failed on $PlaybooksHost (exit $LASTEXITCODE): $command" }
    return @($result)
}
function Test-SourceLeaf([string]$path) {
    if ($remoteMode) {
        & ssh $PlaybooksHost "test -f $path" 2>$null
        return ($LASTEXITCODE -eq 0)
    }
    return (Test-Path -LiteralPath $path -PathType Leaf)
}
function Read-SourceText([string]$path) {
    if ($remoteMode) { return ((Invoke-RemoteLines "cat -- $path") -join "`n") }
    return (Get-Content -LiteralPath $path -Raw)
}

$lines.Add("timestamp=$((Get-Date).ToString('o'))")
$lines.Add("diariesRoot=$ProjectRoot")
$lines.Add("playbooksRoot=$PlaybooksRoot")
$lines.Add("playbooksHost=$(if($remoteMode){$PlaybooksHost}else{'<local>'})")

if ($remoteMode) {
    $ssh = Get-Command ssh -ErrorAction SilentlyContinue
    if ($null -eq $ssh) { throw 'ssh is required for remote Playbooks rehearsal but was not found on PATH' }
    $PlaybooksRoot = Assert-SafeRemotePath $PlaybooksRoot
    $remoteRole = "$PlaybooksRoot/roles/diaries"
    & ssh $PlaybooksHost "test -d $remoteRole" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Remote PlaybooksRoot does not contain roles/diaries: ${PlaybooksHost}:$PlaybooksRoot" }
    $commit = (Invoke-RemoteLines "git -C $PlaybooksRoot rev-parse HEAD") -join ''
    $status = Invoke-RemoteLines "git -C $PlaybooksRoot status --short"
    $lines.Add("playbooks.commit=$(if([string]::IsNullOrWhiteSpace($commit)){'<unavailable>'}else{$commit})")
    $lines.Add("playbooks.status=$(if($status.Count -gt 0){'dirty'}else{'clean'})")
} else {
    foreach ($line in Get-GitIdentityLines -Path $PlaybooksRoot -Label 'playbooks') { $lines.Add($line) }
    $role = Join-Path $PlaybooksRoot 'roles\diaries'
    if (-not (Test-Path -LiteralPath $role -PathType Container)) { throw "PlaybooksRoot does not contain roles/diaries: $PlaybooksRoot" }
}

if ($remoteMode) {
    $role = ($PlaybooksRoot.TrimEnd('/') + '/roles/diaries')
    $paths = @{
        responder = "$role/templates/config/responder/responder.json.j2"
        defaults = "$role/defaults/main.yaml"
        compose = "$role/templates/compose.yaml.j2"
        start = "$role/templates/scripts/start.sh.j2"
        stop = "$role/templates/scripts/stop.sh.j2"
    }
} else {
    $role = Join-Path $PlaybooksRoot 'roles\diaries'
    $paths = @{
        responder = Join-Path $role 'templates\config\responder\responder.json.j2'
        defaults = Join-Path $role 'defaults\main.yaml'
        compose = Join-Path $role 'templates\compose.yaml.j2'
        start = Join-Path $role 'templates\scripts\start.sh.j2'
        stop = Join-Path $role 'templates\scripts\stop.sh.j2'
    }
}

foreach($entry in $paths.GetEnumerator()) {
    if(Test-SourceLeaf $entry.Value){Pass "$($entry.Key) source exists: $($entry.Value)"}else{Fail "$($entry.Key) source missing: $($entry.Value)"}
}

if($failures.Count -eq 0){
    $responder=Read-SourceText $paths.responder
    $defaults=Read-SourceText $paths.defaults
    $compose=Read-SourceText $paths.compose
    $start=Read-SourceText $paths.start
    $stop=Read-SourceText $paths.stop

    $defaultGateFalse = $defaults -match '(?m)^diaries_image_fragment_writes_enabled:\s*false\s*$'
    $templateUsesGate = $responder -match '"imageFragmentWritesEnabled"\s*:\s*\{\{\s*diaries_image_fragment_writes_enabled\s*\|\s*bool\s*\|\s*lower\s*\}\}'
    if($defaultGateFalse -and $templateUsesGate){Pass 'production responder template keeps ImageFragment authoring disabled by fail-closed default'}else{Fail 'production responder template is not controlled by a fail-closed diaries_image_fragment_writes_enabled default'}
    if($defaults -match '(?m)^diaries_web_files_path:\s*["'']?files["'']?\s*$'){Pass 'production web Files path defaults to files'}else{Fail 'production diaries_web_files_path is not the expected files route'}
    if($compose -match 'DIARIES_FILES_DIR' -and $compose -match 'target:\s*/data/files' -and $compose -match 'diaries-client' -and $compose -match 'diaries-responder' -and $compose -match 'diaries-web'){Pass 'production Compose template carries the explicit Files selector and all three application surfaces'}else{Fail 'production Compose template is missing the expected Files selector or application services'}

    $validatePos=$start.IndexOf('docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" config --quiet')
    $pullPos=$start.IndexOf('docker compose --file "${COMPOSE_FILE}" --env-file "${ENV_FILE}" pull')
    $upPos=$start.IndexOf('up --detach --remove-orphans --wait')
    $routePos=$start.IndexOf('Activating Diaries routes in shared Nginx')
    if($validatePos -ge 0 -and $pullPos -gt $validatePos -and $upPos -gt $pullPos){Pass 'production start validates Compose, then pulls, then starts/waits'}else{Fail 'production start order is not validate -> pull -> up --wait'}
    if($routePos -gt $upPos){Pass 'shared Nginx route activation occurs only after application start/health wait'}else{Fail 'shared Nginx route activation does not follow application health wait'}

    $deactivatePos=$stop.IndexOf('Deactivating Diaries routes in shared Nginx')
    $downPos=$stop.IndexOf('down --remove-orphans')
    if($deactivatePos -ge 0 -and $downPos -gt $deactivatePos){Pass 'production stop deactivates shared route before stopping application services'}else{Fail 'production stop order is not route-deactivate -> compose down'}
}

$plan = @(
    '',
    'REHEARSED STEP 15 ORDER (NO PRODUCTION ACTION PERFORMED):',
    '1. Confirm the deployed responder capability is present and healthy with imageFragmentWritesEnabled=false.',
    '2. Confirm the deployed 0026 reader is healthy and ImageFragment-capable.',
    '3. Deploy the compatible 0027 client while the responder gate remains false.',
    '4. Run disabled-gate production smoke checks for legacy MARQUEE editing, IMAGE viewing/ordinary editing, and expected 403 Image-reference authoring.',
    '5. Capture pre-enable responder/MQTT/database/Files evidence.',
    '6. STOP: Step 14 does not change the gate. Deliberate gate enablement belongs to Step 15 only.'
)
foreach($item in $plan){$lines.Add($item);Write-Host $item}

$output=Join-Path $runDir 'rollout-rehearsal.txt'
Write-Utf8NoBom -Path $output -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
if($failures.Count -gt 0){Write-Host "Rollout rehearsal FAILED with $($failures.Count) error(s)." -ForegroundColor Red;exit 1}
Write-Host "Step 14 rollout rehearsal PASSED: $output" -ForegroundColor Green
