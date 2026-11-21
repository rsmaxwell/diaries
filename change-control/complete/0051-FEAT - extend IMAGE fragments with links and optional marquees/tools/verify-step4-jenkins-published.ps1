#Requires -Version 7.0
<#
0051 published image selection and isolated rollback rehearsal.
Uses the image names consumed by local-published-smoke, but deliberately NEVER
runs its normal Compose up/down: that mode has writable NAS Files and a
persistent PostgreSQL directory. The accepted 0051 disposable harness instead
runs the exact Jenkins-published immutable Docker image digests with a frozen
DB fixture and synthetic Files. No local application image builds.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*$')][string]$ResponderTag,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*$')][string]$ClientTag,
    [Parameter(Mandatory)][ValidatePattern('^[A-Za-z0-9_][A-Za-z0-9_.-]*$')][string]$WebTag,
    [string]$BackupFile,
    [switch]$RunRehearsal
)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$feature=Join-Path $repo 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$now=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$id=$now+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$run=Join-Path $feature "evidence/Step 4/private/published-$id"
New-Item -ItemType Directory -Force -Path $run | Out-Null
$oldLocation=Get-Location
$tracked=@('STEP4_ROLLOUT_REHEARSAL','STEP4_CANDIDATE_RESPONDER_IMAGE','STEP4_CANDIDATE_WEB_IMAGE',
 'STEP4_CANDIDATE_CLIENT_IMAGE','STEP4_LEGACY_RESPONDER_IMAGE','STEP4_LEGACY_WEB_IMAGE',
 'STEP4_LEGACY_CLIENT_IMAGE','DIARIES_RESPONDER_IMAGE_TAG','DIARIES_CLIENT_IMAGE_TAG',
 'DIARIES_WEB_IMAGE_TAG','DIARIES_IMAGE_TAG','NODE_PATH','CHROME_BIN')
$original=@{}
foreach($name in $tracked){$original[$name]=[Environment]::GetEnvironmentVariable($name,'Process')}
$passed=$false
$receipt=@{ feature='0051';step=4;runId=$id;status='NOT_RUN';publishedImageSelection=@{};
  rehearsalExecuted=$false;productionModified=$false;normalComposeStarted=$false;startedUtc=[DateTime]::UtcNow.ToString('o') }
function Assert-Success([string]$description) {
    if($LASTEXITCODE -ne 0){throw "$description failed (exit $LASTEXITCODE)"}
}
function Inspect-Image([string]$image) {
    $json=(& docker image inspect $image --format '{{json .}}' 2>&1 | Out-String).Trim()
    Assert-Success "Inspect $image"
    return ($json | ConvertFrom-Json)
}
function Pull-And-Pin([string]$component,[string]$ref) {
    $log=Join-Path $run "pull-$component.log"
    & docker pull --platform linux/amd64 $ref *> $log
    if($LASTEXITCODE -ne 0) {
        Get-Content -LiteralPath $log -Tail 35
        throw "Cannot pull $ref (see $log)"
    }
    $image=Inspect-Image $ref
    $platform="{0}/{1}" -f $image.Os,$image.Architecture
    if($platform -cne 'linux/amd64'){throw "Unexpected $component platform: $platform"}
    $repoName='rsmaxwell/diaries-'+$component
    $digests=@($image.RepoDigests | ForEach-Object {([string]$_) -replace '^docker\.io/',''})
    $matching=@($digests | Where-Object {$_ -cmatch ('^'+[regex]::Escape($repoName)+'@sha256:[0-9a-f]{64}$')})
    if($matching.Count -ne 1){throw "Expected one immutable $component repository digest for $ref; found $($matching.Count)"}
    return @{tagReference=$ref;immutableReference=$matching[0];localImageId=$image.Id;
      platform=$platform;created=$image.Created;repositoryDigests=$digests}
}
try {
    Set-Location $repo
    Write-Host "0051 Step 4 Jenkins-published image selection: $id"
    Write-Host "Evidence: $run"
    foreach($program in @('git','docker','node')) {
        if(!(Get-Command $program -ErrorAction SilentlyContinue)){throw "Required program missing: $program"}
    }
    & docker info --format '{{.ServerVersion}}' *> (Join-Path $run 'docker-version.txt')
    Assert-Success 'Docker Desktop connection'
    $receipt.sourceRevisions=@{}
    foreach($name in @('parent','diaries-responder','diaries-client','diaries-web')){
        $dir=if($name -eq 'parent'){$repo}else{Join-Path $repo $name}
        $hash=(& git -C $dir rev-parse HEAD | Out-String).Trim()
        Assert-Success "Git revision for $name"
        $receipt.sourceRevisions[$name]=$hash
        & git -C $dir status --short *> (Join-Path $run "git-status-$name.txt")
        Assert-Success "Git status for $name"
    }
    & git -C $repo submodule status *> (Join-Path $run 'pinned-submodules.txt')
    Assert-Success 'Pinned Git submodule status'
    # Check the exact existing local-published-smoke IMAGE selection without
    # ever starting its NAS-backed stack or writing an expanded config with secrets.
    $env:DIARIES_IMAGE_TAG=''
    $env:DIARIES_RESPONDER_IMAGE_TAG=$ResponderTag
    $env:DIARIES_WEB_IMAGE_TAG=$WebTag
    $env:DIARIES_CLIENT_IMAGE_TAG=$ClientTag
    $compose=Join-Path $repo 'compose.local-published-smoke.yaml'
    $mode=Join-Path $repo 'config/environments/local-published-smoke.env'
    $local=Join-Path $repo 'config/environments/local.env'
    foreach($p in @($compose,$mode,$local)){if(!(Test-Path -LiteralPath $p)){throw "Required local-published-smoke config missing: $p"}}
    $composeImages=@(& docker compose -f $compose --env-file $mode --env-file $local config --images 2>&1 | ForEach-Object {([string]$_).Trim()})
    Assert-Success 'local-published-smoke Compose image selection'
    $tags=@{responder=$ResponderTag;client=$ClientTag;web=$WebTag}
    foreach($part in @('responder','client','web')) {
        $expected='rsmaxwell/diaries-'+$part+':'+$tags[$part]
        if(-not (@($composeImages) -contains $expected)){
            throw "local-published-smoke does not select required $part image $expected; found: $($composeImages -join ', ')"
        }
    }
    $receipt.composeImageSelection=@($composeImages)
    Write-Host 'PASS: Existing local-published-smoke Compose resolves the three selected tags (config only; no Compose up)'
    $receipt.publishedImageSelection=@{}
    foreach($part in @('responder','web','client')){
        $ref='docker.io/rsmaxwell/diaries-'+$part+':'+$tags[$part]
        $identity=Pull-And-Pin $part $ref
        $receipt.publishedImageSelection[$part]=$identity
        Write-Host ("Jenkins-published {0}: {1}" -f $part,$identity.immutableReference)
    }
    $legacy=@{
      responder='rsmaxwell/diaries-responder@sha256:d0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695'
      web='rsmaxwell/diaries-web@sha256:063e5296f9b49f40f43bf89cc2d5ce4fcdc63a98efe211a57ae884a30981254b'
      client='rsmaxwell/diaries-client@sha256:9b510d4611792bb37907ec45c0400f11cdc7baa7e7dfaecd007a8e7ec9427edd'
    }
    $receipt.legacyImageSelection=@{}
    if($RunRehearsal) {
        if(!$BackupFile) {throw 'BackupFile required when -RunRehearsal is specified'}
        $backup=(Get-Item -LiteralPath $BackupFile -ErrorAction Stop).FullName
        $hash=(Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
        if($hash -cne 'fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86'){
          throw 'Frozen 0024 database fixture checksum mismatch; rehearsal not started'
        }
        $receipt.backupSha256=$hash
        foreach($part in @('responder','web','client')) {
            $ref=$legacy[$part]
            $log=Join-Path $run "pull-legacy-$part.log"
            & docker pull --platform linux/amd64 $ref *> $log
            if($LASTEXITCODE -ne 0){throw "Cannot fetch legacy $part digest; see $log"}
            $image=Inspect-Image $ref
            if("$($image.Os)/$($image.Architecture)" -cne 'linux/amd64') {throw "Legacy $part platform mismatch"}
            $actual=@($image.RepoDigests | ForEach-Object {([string]$_) -replace '^docker\.io/',''})
            if(-not ($actual -ccontains $ref)){throw "Legacy $part repository digest mismatch"}
            $receipt.legacyImageSelection[$part]=@{immutableReference=$ref;localImageId=$image.Id;created=$image.Created}
        }
        foreach($part in @('responder','web','client')){
            if($legacy[$part] -ceq $receipt.publishedImageSelection[$part].immutableReference){
                throw "Candidate $part image is identical to the legacy baseline; select the actual new Jenkins build"
            }
        }
        if(!$env:NODE_PATH){$env:NODE_PATH=Join-Path $env:LOCALAPPDATA 'Diaries/0051-browser-smoke/node_modules'}
        & node -e "require.resolve('playwright');require.resolve('./diaries-client/node_modules/mqtt')" *> (Join-Path $run 'node-modules.txt')
        Assert-Success 'Node Playwright and MQTT dependencies'
        if(!$env:CHROME_BIN){
            $env:CHROME_BIN=@('C:/Program Files/Google/Chrome/Application/chrome.exe',
              'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
              'C:/Program Files (x86)/Google/Chrome/Application/chrome.exe',
              'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe') |
              Where-Object {Test-Path -LiteralPath $_} | Select-Object -First 1
        }
        if(!$env:CHROME_BIN){throw 'Chrome/Edge unavailable'}
        $env:STEP4_ROLLOUT_REHEARSAL='1'
        foreach($part in @('responder','web','client')) {
            [Environment]::SetEnvironmentVariable('STEP4_CANDIDATE_'+$part.ToUpperInvariant()+'_IMAGE',
              $receipt.publishedImageSelection[$part].immutableReference,'Process')
            [Environment]::SetEnvironmentVariable('STEP4_LEGACY_'+$part.ToUpperInvariant()+'_IMAGE',
              $legacy[$part],'Process')
        }
        $receipt.rehearsalExecuted=$true
        $output=Join-Path $run 'disposable'
        $runner=Join-Path $feature 'tests/step3-isolated-reader-smoke.cjs'
        Write-Host '=== Disposable published-image gate, rollback, re-upgrade and activation ==='
        & node $runner $backup $output *> (Join-Path $run 'rehearsal.log')
        if($LASTEXITCODE -ne 0){
            Get-Content -LiteralPath (Join-Path $run 'rehearsal.log') -Tail 90
            throw 'Published-image disposable rehearsal failed'
        }
        $summary=Get-Content -LiteralPath (Join-Path $output 'evidence/summary.json') -Raw | ConvertFrom-Json
        $detail=Get-Content -LiteralPath (Join-Path $output 'evidence/step4-rollout-receipt.json') -Raw | ConvertFrom-Json
        if($summary.status -ne 'PASSED' -or $summary.acceptanceMode -ne 'rollout-preactivation' -or
           @($summary.cleanupFailures).Count -ne 0 -or $detail.status -ne 'PASSED' -or
           !$detail.afterActivation.linkPersisted -or $detail.afterActivation.olderBinariesRestarted){
            throw 'Published-image rehearsal or disposable cleanup receipt invalid'
        }
        $receipt.rehearsalResult='PASSED'
        Write-Host 'PASS: Published-image rollback before extension writes; re-upgrade and forward-only activation'
    } else {
        Write-Host 'PASS: Published image selection and immutable digest pinning. No containers started.'
        Write-Host 'To run the isolated migration/rollback check, repeat with -BackupFile and -RunRehearsal.'
    }
    $receipt.status='PASSED'
    $passed=$true
} catch {
    $receipt.status='FAILED'
    $receipt.error=$_.Exception.Message
    Write-Host "FAIL: $($receipt.error)"
} finally {
    $receipt.finishedUtc=[DateTime]::UtcNow.ToString('o')
    $receipt | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath (Join-Path $run 'result.json')
    foreach($key in $tracked){[Environment]::SetEnvironmentVariable($key,$original[$key],'Process')}
    Set-Location $oldLocation
    $checksums=Get-ChildItem -LiteralPath $run -Recurse -File |
       Where-Object {$_.Name -ne 'SHA256SUMS.txt'} | Sort-Object FullName | ForEach-Object {
           $relative=[IO.Path]::GetRelativePath($run,$_.FullName).Replace('\','/')
           '{0}  {1}' -f (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(),$relative
       }
    [IO.File]::WriteAllLines((Join-Path $run 'SHA256SUMS.txt'),@($checksums))
    Write-Host "Evidence: $run"
}
if(!$passed){throw '0051 Step 4 Jenkins-published image verification FAILED'}
