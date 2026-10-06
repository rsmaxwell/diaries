param([string]$ProjectRoot)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot=[System.IO.Path]::GetFullPath($ProjectRoot)
$failures=New-Object System.Collections.Generic.List[string]
$warnings=New-Object System.Collections.Generic.List[string]
$lines=New-Object System.Collections.Generic.List[string]
function Pass([string]$m){$lines.Add("PASS: $m");Write-Host "PASS: $m"}
function Fail([string]$m){$failures.Add($m);$lines.Add("FAIL: $m");Write-Host "FAIL: $m" -ForegroundColor Red}
function Warn([string]$m){$warnings.Add($m);$lines.Add("WARN: $m");Write-Host "WARN: $m" -ForegroundColor Yellow}

$lines.Add("timestamp=$((Get-Date).ToString('o'))")
$lines.Add("projectRoot=$ProjectRoot")

foreach($container in @('diaries-development-db','diaries-development-mqtt')){
    $state=& docker inspect $container --format '{{.State.Status}}|{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}' 2>$null
    if($LASTEXITCODE -ne 0){Fail "$container is not available. Start development-infrastructure.";continue}
    if($state -match '^running\|(healthy|none)$'){Pass "$container state is $state"}else{Fail "$container state is $state"}
}

$localEnv=Join-Path $ProjectRoot 'config\environments\local.env'
if(Test-Path -LiteralPath $localEnv -PathType Leaf){Pass 'config/environments/local.env exists'}else{Fail 'config/environments/local.env is missing'}

$ng=Join-Path $ProjectRoot 'diaries-client\node_modules\.bin\ng.cmd'
if(Test-Path -LiteralPath $ng -PathType Leaf){Pass 'Angular dependencies are installed'}else{Fail 'diaries-client/node_modules/.bin/ng.cmd is missing; run npm ci'}

$aclPath=Join-Path $ProjectRoot 'config\mosquitto\aclfile.txt'
if(Test-Path -LiteralPath $aclPath -PathType Leaf){
    $acl=Get-Content -LiteralPath $aclPath -Raw
    $clientBlock=[regex]::Match($acl,'(?ms)^user diaries-client\s*(.*?)(?=^user |\z)').Groups[1].Value
    if($clientBlock -match '(?m)^topic read diaries/images/\+\s*$'){Pass 'diaries-client ACL can read diaries/images/+'}else{Fail 'diaries-client ACL is missing topic read diaries/images/+'}
}else{Fail 'config/mosquitto/aclfile.txt is missing'}

try{
    $clientConfig=Get-ClientMqttConfig -ProjectRoot $ProjectRoot
    if([string]$clientConfig.username -eq 'diaries-client'){Pass 'client MQTT identity is diaries-client'}else{Warn "client MQTT identity is $($clientConfig.username), not diaries-client; confirm ACL deliberately"}
    if([string]::IsNullOrWhiteSpace([string]$clientConfig.password)){Fail 'client MQTT password is empty'}else{Pass 'client MQTT password is configured (value not printed)'}
}catch{Fail $_.Exception.Message}

try{
    $filesRoot=Get-EffectiveFilesRoot -ProjectRoot $ProjectRoot
    if(Test-Path -LiteralPath $filesRoot -PathType Container){Pass "effective Files root exists: $filesRoot"}else{Fail "effective Files root does not exist: $filesRoot"}
}catch{Fail $_.Exception.Message}

try{
    $count=(Invoke-Step13Sql -Sql "select count(*) from fragment where type='IMAGE';" | Select-Object -Last 1).Trim()
    if([int]$count -gt 0){Pass "development dataset contains $count IMAGE Fragment(s) for Phase A"}else{Warn 'development dataset contains no IMAGE Fragment. Create a disposable fixture with the gate enabled, then restart the responder with the gate disabled before Phase A.'}
}catch{Fail $_.Exception.Message}

try{
    $runDir=Get-CurrentStep13RunDirectory -ProjectRoot $ProjectRoot
    $outputPath=Join-Path $runDir 'preflight.txt'
    Write-Utf8NoBom -Path $outputPath -Text (($lines -join [Environment]::NewLine)+[Environment]::NewLine)
    Pass "preflight evidence written to $outputPath"
}catch{Warn 'No active Step 13 run yet; run step13-begin.ps1 before live capture.'}

if($warnings.Count -gt 0){Write-Host "Warnings: $($warnings.Count)" -ForegroundColor Yellow}
if($failures.Count -gt 0){Write-Host "Preflight FAILED with $($failures.Count) error(s)." -ForegroundColor Red; exit 1}
Write-Host 'Step 13 preflight passed.' -ForegroundColor Green
