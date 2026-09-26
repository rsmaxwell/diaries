[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Container,
    [Parameter(Mandatory)][string]$Database,
    [Parameter(Mandatory)][string]$User,
    [Parameter(Mandatory)][string]$BackupFile,
    [Parameter(Mandatory)][string]$EvidenceDirectory
)
# Applies Phase 2. Use 001-preflight.sql directly for a read-only preview.
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Choose a new evidence directory; existing evidence is preserved.' }
$backup = Get-Item -LiteralPath $BackupFile
if ($backup.PSIsContainer -or $backup.Length -eq 0) { throw 'A nonempty recent database backup is required.' }
$inspection = docker inspect $Container | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or !$inspection[0].State.Running) { throw 'Target database container is not running.' }
$evidence=(New-Item -ItemType Directory -Path $EvidenceDirectory).FullName
$source=(New-Item -ItemType Directory -Path (Join-Path $evidence 'sql')).FullName
foreach ($file in Get-ChildItem -LiteralPath $PSScriptRoot -Filter '*.sql' -File) {
    Copy-Item -LiteralPath $file.FullName -Destination $source
}
$remote='/tmp/diaries-0024-'+[guid]::NewGuid().ToString('N')
function Docker-Checked {
    param([string[]]$Arguments)
    $out = & docker @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($out -join "`n") }
    return $out
}
$null=Docker-Checked @('cp',$source,($Container+':'+$remote))
$null=Docker-Checked @('cp',$backup.FullName,($Container+':'+$remote+'/before.dump'))
$archive=Docker-Checked @('exec',$Container,'pg_restore','--list',($remote+'/before.dump'))
[IO.File]::WriteAllText((Join-Path $evidence 'backup-archive-list.txt'),($archive -join "`n")+"`n",(New-Object Text.UTF8Encoding($false)))
$started=[DateTime]::UtcNow.ToString('o')
$log=& docker exec $Container psql -X -U $User -d $Database -v ON_ERROR_STOP=1 -f ($remote+'/001-preflight.sql') -f ($remote+'/002-add-image-catalogue.sql') -f ($remote+'/003-postflight.sql') 2>&1
$code=$LASTEXITCODE
[IO.File]::WriteAllText((Join-Path $evidence 'preflight-apply-postflight.txt'),($log -join "`n")+"`n",(New-Object Text.UTF8Encoding($false)))
$result=[ordered]@{
    startedAtUtc=$started; completedAtUtc=[DateTime]::UtcNow.ToString('o'); exitCode=$code
    container=$Container; database=$Database; applicationUser=$User
    imageName=$inspection[0].Config.Image; imageId=$inspection[0].Image
    backupFile=$backup.FullName; backupBytes=$backup.Length; backupSha256=(Get-FileHash -LiteralPath $backup.FullName).Hash.ToLowerInvariant()
    sqlDirectory='sql'; log='preflight-apply-postflight.txt'
}
[IO.File]::WriteAllText((Join-Path $evidence 'run-result.json'),($result|ConvertTo-Json -Depth 5)+"`n",(New-Object Text.UTF8Encoding($false)))
[IO.File]::WriteAllText((Join-Path $evidence '.gitattributes'),"* -text whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol`n",(New-Object Text.UTF8Encoding($false)))
$manifest=@(Get-ChildItem -LiteralPath $evidence -File -Recurse -Force | Sort-Object FullName | ForEach-Object {
    (Get-FileHash -LiteralPath $_.FullName).Hash.ToLowerInvariant()+'  '+$_.FullName.Substring($evidence.Length+1).Replace('\','/')
})
[IO.File]::WriteAllText((Join-Path $evidence 'SHA256SUMS.txt'),($manifest -join "`n")+"`n",(New-Object Text.UTF8Encoding($false)))
if ($code -ne 0) { throw "0024 failed (exit $code). Inspect $evidence/preflight-apply-postflight.txt before retrying." }
Write-Output "0024 preflight, apply and postflight passed. Evidence: $evidence"
