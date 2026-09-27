[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Container,
    [Parameter(Mandatory)][string]$Database,
    [Parameter(Mandatory)][string]$User,
    [Parameter(Mandatory)][string]$BackupFile,
    [Parameter(Mandatory)][string]$EvidenceDirectory,
    [switch]$AllowExistingReferences
)
# Applies Step 2. Use 001-preflight.sql directly for a read-only preview.
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
$remote='/tmp/diaries-0025-'+[guid]::NewGuid().ToString('N')
function Docker-Captured {
    param([string[]]$Arguments)
    $dockerCommand = Get-Command docker -CommandType Application -ErrorAction Stop | Select-Object -First 1
    # Windows PowerShell 5.1 turns redirected native stderr (including psql
    # NOTICE messages) into ErrorRecords. Capture them without aborting the
    # process, then use its exit code as the authoritative success indicator.
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $out = & $dockerCommand.Source @Arguments 2>&1
    $code = $LASTEXITCODE
    return [pscustomobject]@{ Output = @($out); ExitCode = $code }
}
function Docker-Checked {
    param([string[]]$Arguments)
    $captured = Docker-Captured $Arguments
    if ($captured.ExitCode -ne 0) { throw ($captured.Output -join "`n") }
    return $captured.Output
}
$null=Docker-Checked @('cp',$source,($Container+':'+$remote))
$null=Docker-Checked @('cp',$backup.FullName,($Container+':'+$remote+'/before.dump'))
$archive=Docker-Checked @('exec',$Container,'pg_restore','--list',($remote+'/before.dump'))
[IO.File]::WriteAllText((Join-Path $evidence 'backup-archive-list.txt'),($archive -join "`n")+"`n",(New-Object Text.UTF8Encoding($false)))
$started=[DateTime]::UtcNow.ToString('o')
$allowReferences=$AllowExistingReferences.IsPresent.ToString().ToLowerInvariant()
$captured = Docker-Captured @('exec',$Container,'psql','-X','-U',$User,'-d',$Database,'-v','ON_ERROR_STOP=1','-v',"allow_existing_references=$allowReferences",'-f',($remote+'/001-preflight.sql'),'-f',($remote+'/002-add-fragment-image-reference.sql'),'-f',($remote+'/003-postflight.sql'))
$log = $captured.Output
$code = $captured.ExitCode
[IO.File]::WriteAllText((Join-Path $evidence 'preflight-apply-postflight.txt'),($log -join "`n")+"`n",(New-Object Text.UTF8Encoding($false)))
$result=[ordered]@{
    startedAtUtc=$started; completedAtUtc=[DateTime]::UtcNow.ToString('o'); exitCode=$code
    container=$Container; database=$Database; applicationUser=$User; allowExistingReferences=$AllowExistingReferences.IsPresent
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
if ($code -ne 0) { throw "0025 failed (exit $code). Inspect $evidence/preflight-apply-postflight.txt before retrying." }
Write-Output "0025 preflight, apply and postflight passed. Evidence: $evidence"

