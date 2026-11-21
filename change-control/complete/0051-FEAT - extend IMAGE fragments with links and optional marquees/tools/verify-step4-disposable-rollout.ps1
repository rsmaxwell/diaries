#Requires -Version 7.0
<#
0051 Step 4: build three identifiable candidate images, check measured legacy
published digests and platform, rehearse gate-disabled rollback/re-upgrade and activation using only
synthetic media, ephemeral containers and the approved frozen DB fixture.
Does not run Compose, publish/deploy images, or mount any NAS/production dataset.
#>
[CmdletBinding()]
param([Parameter(Mandatory)][string]$BackupFile,[string]$ChromeBin)
$ErrorActionPreference='Stop'
$repo=(Resolve-Path (Join-Path $PSScriptRoot '../../../..')).Path
$initialLocation=Get-Location
Set-Location $repo
$feature=Join-Path $repo 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
$base=Join-Path $feature 'evidence/Step 4/private'
New-Item -ItemType Directory -Force -Path $base | Out-Null
$id=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')+'-'+[guid]::NewGuid().ToString('N').Substring(0,8)
$run=Join-Path $base "rollout-$id"
New-Item -ItemType Directory -Path $run | Out-Null
$backup=(Get-Item -LiteralPath $BackupFile -ErrorAction Stop).FullName
$productionImageIds=@{
  responder='sha256:ba88249cd7d64d651f98738d6dec6cee3c8a34bdae58351d5a145dc8db3169c3'
  web='sha256:9dfcd29d85e09f6613f973aab5bde93604147db569db88e049ee35c3cce377f9'
  client='sha256:8d49e621f83f145b98b86cdc25978bb50398c2cb7779203f04299dd92487d0bc'
}
# Immutable repository digests observed on the running pluto containers on
# 2026-11-20 16:34 UTC. Image .Id differs between pluto and local Docker Desktop;
# it is not a stable cross-daemon representation of the published artifact.
$productionRepoDigests=@{
  responder='rsmaxwell/diaries-responder@sha256:d0f9224d759e06cabf26eb19722b3b417b170f7c6e3919c481acbe64db507695'
  client='rsmaxwell/diaries-client@sha256:9b510d4611792bb37907ec45c0400f11cdc7baa7e7dfaecd007a8e7ec9427edd'
  web='rsmaxwell/diaries-web@sha256:063e5296f9b49f40f43bf89cc2d5ce4fcdc63a98efe211a57ae884a30981254b'
}
$images=@{
  legacy=@{
    responder='docker.io/rsmaxwell/diaries-responder:0.0.9-build-84'
    web='docker.io/rsmaxwell/diaries-web:0.0.9-build-8'
    client='docker.io/rsmaxwell/diaries-client:0.0.9-build-77'
  }
  candidate=@{
    responder="diaries-0051-candidate-responder:$id"
    web="diaries-0051-candidate-web:$id"
    client="diaries-0051-candidate-client:$id"
  }
}
$identity=@{legacy=@{};candidate=@{}}
$envKeys=@('STEP4_ROLLOUT_REHEARSAL','STEP4_CANDIDATE_RESPONDER_IMAGE',
 'STEP4_CANDIDATE_WEB_IMAGE','STEP4_CANDIDATE_CLIENT_IMAGE',
 'STEP4_LEGACY_RESPONDER_IMAGE','STEP4_LEGACY_WEB_IMAGE','STEP4_LEGACY_CLIENT_IMAGE','CHROME_BIN','NODE_PATH')
$before=@{}
foreach($key in $envKeys) {$before[$key]=[Environment]::GetEnvironmentVariable($key,'Process')}
$passed=$false
function Run-Logged([string]$command,[string[]]$arguments,[string]$log) {
  & $command @arguments *> $log
  if($LASTEXITCODE -ne 0) {
    Write-Host "FAIL: $command returned $LASTEXITCODE. Log: $log"
    if(Test-Path -LiteralPath $log) {Get-Content -LiteralPath $log -Tail 65}
    throw "Command failed: $command"
  }
}
function Image-Details([string]$ref) {
  $json=(& docker image inspect $ref | Out-String)
  if($LASTEXITCODE -ne 0) {throw "Image not found: $ref"}
  return @((ConvertFrom-Json -InputObject $json -NoEnumerate))[0]
}
try {
  Write-Host "0051 Step 4 disposable rollout run: $id"
  Write-Host "Evidence directory: $run"
  foreach($name in @('git','docker','node','npm.cmd')) {
    if(!(Get-Command $name -ErrorAction SilentlyContinue)){throw "Required command missing: $name"}
  }
  $fixtureHash=(Get-FileHash -LiteralPath $backup -Algorithm SHA256).Hash.ToLowerInvariant()
  if($fixtureHash -ne 'fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86'){
    throw 'Frozen fixture checksum mismatch; no containers started'
  }
  $null=& docker info --format '{{.ServerVersion}}'
  if($LASTEXITCODE -ne 0){throw 'Docker Desktop engine unavailable'}
  if(!$env:NODE_PATH){$env:NODE_PATH=Join-Path $env:LOCALAPPDATA 'Diaries/0051-browser-smoke/node_modules'}
  & node -e "require.resolve('playwright');require.resolve('./diaries-client/node_modules/mqtt')" 2>&1
  if($LASTEXITCODE -ne 0){throw 'Node Playwright/MQTT dependencies not available'}
  if(!$ChromeBin){
    $ChromeBin=@('C:/Program Files/Google/Chrome/Application/chrome.exe',
      'C:/Program Files/Microsoft/Edge/Application/msedge.exe',
      'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe') |
      Where-Object {Test-Path -LiteralPath $_} | Select-Object -First 1
  }
  if(!$ChromeBin -or !(Test-Path -LiteralPath $ChromeBin)){throw 'Chrome/Edge executable not found'}
  $env:CHROME_BIN=$ChromeBin
  @(
    "capturedUtc=$([DateTime]::UtcNow.ToString('o'))",
    "parentRevision=$(& git -C $repo rev-parse HEAD)",
    '=== parent git status ===',(& git -C $repo status --short),
    '=== git submodule status ===',(& git -C $repo submodule status),
    '=== responder changes ===',(& git -C (Join-Path $repo 'diaries-responder') status --short),
    '=== client changes ===',(& git -C (Join-Path $repo 'diaries-client') status --short),
    '=== web changes ===',(& git -C (Join-Path $repo 'diaries-web') status --short)
  ) | Set-Content (Join-Path $run 'git-source-status.txt')
  Write-Host '=== Published baseline images (verify production repository digests and platform) ==='
  foreach($part in @('responder','web','client')){
    $ref=$images.legacy[$part]
    & docker image inspect $ref *> $null
    if($LASTEXITCODE -ne 0){Run-Logged 'docker' @('pull',$ref) (Join-Path $run "pull-legacy-$part.log")}
    $details=Image-Details $ref
    $expectedDigest=$productionRepoDigests[$part]
    $localDigests=@($details.RepoDigests | ForEach-Object { [string]$_ })
    $platform="$($details.Os)/$($details.Architecture)"
    # Record both IDs and the observed digests, even if verification fails.
    $identity.legacy[$part]=@{
      ref=$ref
      localImageId=$details.Id
      productionImageId=$productionImageIds[$part]
      expectedRepositoryDigest=$expectedDigest
      localRepositoryDigests=$localDigests
      platform=$platform
      created=$details.Created
      verified=$false
    }
    if($platform -cne 'linux/amd64'){
      throw "Legacy $part platform mismatch: expected linux/amd64; got $platform"
    }
    if($localDigests.Count -eq 0 -or -not ($localDigests -ccontains $expectedDigest)){
      throw "Legacy $part repository digest mismatch: expected $expectedDigest; got $($localDigests -join ', ')"
    }
    $identity.legacy[$part].verified=$true
    Write-Host "Verified legacy ${part}: $expectedDigest ($platform); local image ID $($details.Id)"
  }
  # Persist verified baseline identities before starting candidate builds.
  $identity | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run 'baseline-image-identities.json')
  Write-Host '=== Build three candidate Docker images (unique local tags; no push) ==='
  foreach($part in @('responder','web','client')){
    $ref=$images.candidate[$part]
    $dockerfile=switch($part){
      'responder' {'diaries-responder/Dockerfile'}
      'web' {'diaries-web/Dockerfile'}
      'client' {'diaries-client/scripts/files/Dockerfile'}
    }
    $context=if($part -eq 'client'){'diaries-client'}else{'.'}
    $args=@('build','--iidfile',(Join-Path $run "$part.iid"),'-t',$ref,'-f',$dockerfile)
    if($part -eq 'client'){$args+=@('--build-arg',"VERSION=0051-step4-$id")}
    $args+=$context
    Run-Logged 'docker' $args (Join-Path $run "build-$part.log")
    $details=Image-Details $ref
    $identity.candidate[$part]=@{ref=$ref;id=$details.Id;repoDigests=@($details.RepoDigests)}
    Write-Host "Candidate ${part}: $($details.Id)"
  }
  $identity | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run 'image-identities.json')
  Write-Host '=== Hash JARs inside actual candidate Docker images ==='
  $jars=@{}
  foreach($part in @('responder','web')) {
    $jarPath=if($part -eq 'responder'){'/opt/diaries/diaries-responder.jar'}else{'/opt/diaries-web/diaries-web.jar'}
    $hashText=(& docker run --rm --entrypoint sha256sum $images.candidate[$part] $jarPath | Out-String)
    if($LASTEXITCODE -ne 0){throw "Cannot checksum $part JAR from built candidate image"}
    $hash=($hashText.Trim() -split '\s+')[0]
    if($hash -notmatch '^[a-f0-9]{64}$'){throw "Bad $part JAR checksum"}
    $jars[$part]=@{image=$images.candidate[$part];path=$jarPath;sha256=$hash}
  }
  $jars | ConvertTo-Json -Depth 4 | Set-Content (Join-Path $run 'jar-hashes.json')
  $env:STEP4_ROLLOUT_REHEARSAL='1'
  foreach($kind in @('candidate','legacy')){
    foreach($part in @('responder','web','client')){
      [Environment]::SetEnvironmentVariable("STEP4_$($kind.ToUpperInvariant())_$($part.ToUpperInvariant())_IMAGE",$images[$kind][$part],'Process')
    }
  }
  $runner=Join-Path $feature 'tests/step3-isolated-reader-smoke.cjs'
  $output=Join-Path $run 'disposable'
  Write-Host '=== Run disposable gate, preactivation rollback, re-upgrade and activation ==='
  & node $runner $backup $output *> (Join-Path $run 'rollout.log')
  if($LASTEXITCODE -ne 0){
    Get-Content (Join-Path $run 'rollout.log') -Tail 100
    throw 'Disposable rollout runner failed'
  }
  $summary=Get-Content (Join-Path $output 'evidence/summary.json') -Raw | ConvertFrom-Json
  $rehearsal=Get-Content (Join-Path $output 'evidence/step4-rollout-receipt.json') -Raw | ConvertFrom-Json
  if($summary.status -ne 'PASSED' -or $summary.acceptanceMode -ne 'rollout-preactivation' -or
      @($summary.cleanupFailures).Count -ne 0 -or $rehearsal.status -ne 'PASSED' -or
      !$rehearsal.afterActivation.linkPersisted -or $rehearsal.afterActivation.olderBinariesRestarted){
    throw 'Rollout receipt or disposable cleanup invalid'
  }
  $passed=$true
  Write-Host 'PASS: Disposable preactivation rollback, re-upgrade and forward-only activation'
} catch {
  Write-Host "FAIL: $($_.Exception.Message)"
} finally {
  foreach($key in $envKeys){[Environment]::SetEnvironmentVariable($key,$before[$key],'Process')}
  @{
    feature='0051';step=4;runId=$id;status=$(if($passed){'PASSED'}else{'FAILED'});
    legacy=$identity.legacy;candidate=$identity.candidate;
    productionModified=$false;legacyBinariesRestartedAfterNewFormatWrite=$false;
    finishedUtc=[DateTime]::UtcNow.ToString('o')
  } | ConvertTo-Json -Depth 8 | Set-Content (Join-Path $run 'result.json')
  $hashes=Get-ChildItem -LiteralPath $run -Recurse -File |
    Where-Object {$_.Name -ne 'SHA256SUMS.txt'} | Sort-Object FullName |
    ForEach-Object {
      $rel=[IO.Path]::GetRelativePath($run,$_.FullName).Replace('\','/')
      '{0}  {1}' -f (Get-FileHash $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant(),$rel
    }
  [IO.File]::WriteAllLines((Join-Path $run 'SHA256SUMS.txt'),@($hashes))
  Write-Host "Evidence: $run"
  Set-Location $initialLocation
}
if(!$passed){throw '0051 Step 4 disposable rollout rehearsal FAILED'}
