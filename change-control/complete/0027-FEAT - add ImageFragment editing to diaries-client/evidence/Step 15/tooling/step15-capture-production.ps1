param(
    [string]$ProjectRoot,
    [Parameter(Mandatory=$true)][ValidateSet('pre-deploy','post-client-disabled','pre-enable','post-enable','rollback-disabled')][string]$Phase,
    [string]$PlutoHost = 'pluto',
    [string]$ProductionProjectDir = '/home/richard/projects/diaries',
    [string]$ExpectedClientImage
)
. (Join-Path $PSScriptRoot 'step15-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot = [System.IO.Path]::GetFullPath($ProjectRoot)
$runDir = Get-CurrentStep15RunDirectory -ProjectRoot $ProjectRoot
$ProductionProjectDir = Assert-SafeRemotePath -Path $ProductionProjectDir
$expectGate = if ($Phase -eq 'post-enable') { 'true' } else { 'false' }
$failures = New-Object System.Collections.Generic.List[string]
$lines = New-Object System.Collections.Generic.List[string]
function Add-Section([string]$title){$lines.Add('');$lines.Add("===== $title =====")}
function Remote([string]$command,[switch]$AllowFailure){
    $r=Invoke-Step15Ssh -HostName $PlutoHost -Command $command -AllowFailure:$AllowFailure
    foreach($line in $r.Lines){$lines.Add([string]$line)}
    return $r
}

$lines.Add("step=15")
$lines.Add("phase=$Phase")
$lines.Add("capturedAtLocal=$((Get-Date).ToString('o'))")
$lines.Add("host=$PlutoHost")
$lines.Add("projectDir=$ProductionProjectDir")
$lines.Add("expectedGate=$expectGate")

Add-Section 'gate'
$gate = Remote "grep -E 'imageFragmentWritesEnabled[^:]*:[[:space:]]*(true|false)' $ProductionProjectDir/config/responder/responder.json"
$gateText = $gate.Lines -join "`n"
$gatePattern = ('"imageFragmentWritesEnabled"\s*:\s*' + [regex]::Escape($expectGate))
if ($gateText -notmatch $gatePattern) { $failures.Add("rendered gate is not $expectGate") }

Add-Section 'compose-validation'
try { Remote "cd $ProductionProjectDir && docker compose --file compose.yaml --env-file .env config --quiet" | Out-Null } catch { $failures.Add($_.Exception.Message); $lines.Add("FAIL: $($_.Exception.Message)") }

Add-Section 'container-images-and-health'
$inspectCommand = @'
cd __PROJECT_DIR__ || exit 1
for service in diaries-client diaries-responder diaries-web diaries-db diaries-mqtt; do
    c=$(docker compose --file compose.yaml --env-file .env ps --all --quiet "$service" | head -n 1)
    if [ -n "$c" ]; then
        docker inspect --format '{{.Name}}|{{.Config.Image}}|{{.Image}}|{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}n/a{{end}}' "$c"
    else
        echo "/$service|MISSING|MISSING|missing|missing"
    fi
done
'@.Replace('__PROJECT_DIR__', $ProductionProjectDir).Trim()
try {
    $inspect = Remote $inspectCommand
    $bad = @($inspect.Lines | Where-Object { $_ -match '\|(missing|unhealthy|exited|dead)(\||$)' })
    if ($bad.Count -gt 0) { $failures.Add('one or more production containers are missing/unhealthy/stopped') }
    if (-not [string]::IsNullOrWhiteSpace($ExpectedClientImage)) {
        $clientLine = @($inspect.Lines | Where-Object { $_ -match '^/diaries-client\|' } | Select-Object -First 1)
        if ($clientLine.Count -eq 0 -or $clientLine[0] -notmatch [regex]::Escape("|$ExpectedClientImage|")) {
            $failures.Add("diaries-client is not running expected image $ExpectedClientImage")
        }
    }
} catch { $failures.Add($_.Exception.Message); $lines.Add("FAIL: $($_.Exception.Message)") }

Add-Section 'database-non-sensitive-inventory'
$dbCommand = @'
cd __PROJECT_DIR__ || exit 1
DB_CONTAINER=$(docker compose --file compose.yaml --env-file .env ps --all --quiet diaries-db | head -n 1)
if [ -z "$DB_CONTAINER" ]; then echo 'database service diaries-db has no container'; exit 1; fi
DB_USER=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$DB_CONTAINER" | sed -n 's/^POSTGRES_USER=//p')
DB_NAME=$(docker inspect --format '{{range .Config.Env}}{{println .}}{{end}}' "$DB_CONTAINER" | sed -n 's/^POSTGRES_DB=//p')
docker exec "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" -Atc "SELECT 'image_rows=' || count(*) FROM image; SELECT 'image_fragment_rows=' || count(*) FROM fragment WHERE type = 'IMAGE'; SELECT 'referenced_image_fragments=' || count(*) FROM fragment WHERE type = 'IMAGE' AND image_id IS NOT NULL; SELECT 'orphan_image_references=' || count(*) FROM fragment f LEFT JOIN image i ON i.id=f.image_id WHERE f.type='IMAGE' AND f.image_id IS NOT NULL AND i.id IS NULL; SELECT 'latest_image_fragment_ids=' || COALESCE(string_agg(id::text, ',' ORDER BY id), '') FROM (SELECT id FROM fragment WHERE type='IMAGE' ORDER BY id DESC LIMIT 10) s;"
'@.Replace('__PROJECT_DIR__', $ProductionProjectDir).Trim()
try {
    $db = Remote $dbCommand
    if (($db.Lines -join "`n") -match 'orphan_image_references=0') { } else { $failures.Add('database inventory did not prove orphan_image_references=0') }
} catch { $failures.Add($_.Exception.Message); $lines.Add("FAIL: $($_.Exception.Message)") }

Add-Section 'files-non-sensitive-inventory'
$filesCommand = @'
cd __PROJECT_DIR__ || exit 1
RESPONDER_CONTAINER=$(docker compose --file compose.yaml --env-file .env ps --all --quiet diaries-responder | head -n 1)
if [ -z "$RESPONDER_CONTAINER" ]; then echo 'responder service diaries-responder has no container'; exit 1; fi
docker exec "$RESPONDER_CONTAINER" sh -lc 'printf "files_total="; find /data/files -type f 2>/dev/null | wc -l; printf "staging_files="; if [ -d /data/files/.image-staging ]; then find /data/files/.image-staging -type f 2>/dev/null | wc -l; else echo 0; fi'
'@.Replace('__PROJECT_DIR__', $ProductionProjectDir).Trim()
try { Remote $filesCommand | Out-Null } catch { $failures.Add($_.Exception.Message); $lines.Add("FAIL: $($_.Exception.Message)") }

Add-Section 'result'
$status = if ($failures.Count -eq 0) { 'PASSED' } else { 'FAILED' }
$lines.Add("status=$status")
foreach($failure in $failures){$lines.Add("FAIL: $failure")}
$out = Join-Path $runDir ("production-$Phase.txt")
if (Test-Path -LiteralPath $out) {
    $historyDir = Join-Path $runDir 'history'
    New-Item -ItemType Directory -Force -Path $historyDir | Out-Null
    $stamp = (Get-Date).ToString('yyyyMMdd-HHmmssfff')
    $archived = Join-Path $historyDir ("production-$Phase-$stamp.txt")
    Move-Item -LiteralPath $out -Destination $archived
    Write-Host "Archived previous $Phase capture: $archived" -ForegroundColor DarkGray
}
Write-Utf8NoBom -Path $out -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
if ($failures.Count -gt 0) { throw "Production capture $Phase FAILED with $($failures.Count) condition(s). See $out" }
Write-Host "Production capture $Phase PASSED: $out" -ForegroundColor Green
