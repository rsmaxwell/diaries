param(
    [Parameter(Mandatory=$true)][string]$Label,
    [long[]]$FragmentIds=@(),
    [long[]]$ImageIds=@(),
    [string]$ProjectRoot
)
. (Join-Path $PSScriptRoot 'step13-common.ps1')
if ([string]::IsNullOrWhiteSpace($ProjectRoot)) { $ProjectRoot = Find-DiariesProjectRoot }
$ProjectRoot=[System.IO.Path]::GetFullPath($ProjectRoot)
$runDir=Get-CurrentStep13RunDirectory -ProjectRoot $ProjectRoot
$safeLabel=($Label -replace '[^A-Za-z0-9._-]','-').Trim('-')
if([string]::IsNullOrWhiteSpace($safeLabel)){throw 'Label must contain at least one safe character.'}
$outDir=Join-Path $runDir $safeLabel
New-Item -ItemType Directory -Path $outDir -Force | Out-Null
Write-Utf8NoBom -Path (Join-Path $outDir 'timestamp.txt') -Text ((Get-Date).ToString('o')+[Environment]::NewLine)

# Database state: all IMAGE Fragments and all Images. Text is represented by length/hash, not copied verbatim.
$fragmentSql=@"
select id,version,page_id,type,image_id,year,month,day,sequence,
       length(text) as text_length,md5(text) as text_md5,
       lock_user_id,(lock_session_id is not null) as has_lock_session
from fragment
where type='IMAGE'
order by id;
"@
$imageSql=@"
select id,version,relative_path,mime_type,original_filename,width,height,checksum,caption,alt_text
from image
order by id;
"@
Write-Utf8NoBom -Path (Join-Path $outDir 'database-image-fragments.txt') -Text (((Invoke-Step13Sql -Sql $fragmentSql) -join [Environment]::NewLine)+[Environment]::NewLine)
Write-Utf8NoBom -Path (Join-Path $outDir 'database-images.txt') -Text (((Invoke-Step13Sql -Sql $imageSql) -join [Environment]::NewLine)+[Environment]::NewLine)

$clientConfig=Get-ClientMqttConfig -ProjectRoot $ProjectRoot
$retained=New-Object System.Collections.Generic.List[string]
foreach($id in $FragmentIds){
    $topic="diaries/fragments/$id"
    $retained.Add("### $topic")
    $retained.Add((Capture-RetainedTopic -Topic $topic -ClientConfig $clientConfig))
    $retained.Add('')
}
foreach($id in $ImageIds){
    $topic="diaries/images/$id"
    $retained.Add("### $topic")
    $retained.Add((Capture-RetainedTopic -Topic $topic -ClientConfig $clientConfig))
    $retained.Add('')
}
if($FragmentIds.Count -eq 0 -and $ImageIds.Count -eq 0){
    $retained.Add('<no explicit Fragment/Image IDs supplied; retained exact-topic capture skipped>')
}
Write-Utf8NoBom -Path (Join-Path $outDir 'retained-topics.txt') -Text (($retained -join [Environment]::NewLine)+[Environment]::NewLine)

$filesRoot=Get-EffectiveFilesRoot -ProjectRoot $ProjectRoot
$fileLines=New-Object System.Collections.Generic.List[string]
$fileLines.Add("effectiveFilesRoot=$filesRoot")
foreach($id in $ImageIds){
    $rows=Invoke-Step13Sql -Sql ("select id,relative_path from image where id="+$id+";")
    $data=$rows | Where-Object {$_ -match '^\d+\|'} | Select-Object -First 1
    if($null -eq $data){$fileLines.Add("imageId=$id databaseRow=<absent>");continue}
    $parts=$data -split '\|',2
    $relative=$parts[1]
    $physical=Join-Path $filesRoot ($relative -replace '/','\')
    if(Test-Path -LiteralPath $physical -PathType Leaf){
        $item=Get-Item -LiteralPath $physical
        $hash=(Get-FileHash -LiteralPath $physical -Algorithm SHA256).Hash.ToLowerInvariant()
        $fileLines.Add("imageId=$id relativePath=$relative exists=true length=$($item.Length) sha256=$hash")
    }else{$fileLines.Add("imageId=$id relativePath=$relative exists=false")}
}
if($ImageIds.Count -eq 0){
    $count=(Get-ChildItem -LiteralPath $filesRoot -File -Recurse -ErrorAction Stop | Measure-Object).Count
    $fileLines.Add("fileCount=$count")
}
Write-Utf8NoBom -Path (Join-Path $outDir 'files-state.txt') -Text (($fileLines -join [Environment]::NewLine)+[Environment]::NewLine)

$containerState=& docker ps --filter 'name=diaries-development-' --format '{{.Names}}|{{.Status}}'
Write-Utf8NoBom -Path (Join-Path $outDir 'containers.txt') -Text (($containerState -join [Environment]::NewLine)+[Environment]::NewLine)
Write-Host "Captured Step 13 state: $outDir"
Write-Output $outDir
