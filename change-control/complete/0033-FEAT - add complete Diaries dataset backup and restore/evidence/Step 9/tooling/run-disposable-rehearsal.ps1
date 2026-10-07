#Requires -Version 5.1
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SourceBackup,

    [string]$DatasetName = '0033-step9-rehearsal',
    [string]$FilesDir = 'files-0033-step9-rehearsal',
    [string]$EvidenceDirectory,
    [switch]$ResetDisposable
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version 2.0

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$FeatureDir = [System.IO.Path]::GetFullPath((Join-Path $ScriptDir '..\..\..'))
$ProjectDir = [System.IO.Path]::GetFullPath((Join-Path $FeatureDir '..\..\..'))
$ModeName = 'local-docker-build'
$ModeEnv = Join-Path $ProjectDir 'config\environments\local-docker-build.env'
$LocalEnv = Join-Path $ProjectDir 'config\environments\local.env'
$ComposeFile = Join-Path $ProjectDir 'compose.local-docker-build.yaml'
$BackupScript = Join-Path $ProjectDir 'scripts\windows\common\backup-dataset.ps1'
$BackupWrapper = Join-Path $ProjectDir 'scripts\windows\local-docker-build\backup-dataset.bat'
$RestoreWrapper = Join-Path $ProjectDir 'scripts\windows\local-docker-build\restore-dataset.bat'
$ManifestHelper = Join-Path $ProjectDir 'scripts\windows\common\complete-dataset-manifest.py'
$NegativeHelper = Join-Path $ScriptDir 'verify-negative-backup-cases.py'

function Require([bool]$Condition, [string]$Message) {
    if (-not $Condition) { throw $Message }
}

function Read-DotEnv([string]$Path) {
    $values = @{}
    foreach ($raw in Get-Content -LiteralPath $Path) {
        $line = [string]$raw
        $trim = $line.Trim()
        if ([string]::IsNullOrWhiteSpace($trim) -or $trim.StartsWith('#')) { continue }
        $eq = $line.IndexOf('=')
        if ($eq -lt 1) { continue }
        $key = $line.Substring(0,$eq).Trim()
        $value = $line.Substring($eq+1).Trim()
        if ($key) { $values[$key] = $value }
    }
    return $values
}

function Merge-DotEnv([hashtable]$First, [hashtable]$Second) {
    $result = @{}
    foreach ($key in $First.Keys) { $result[$key] = $First[$key] }
    foreach ($key in $Second.Keys) { $result[$key] = $Second[$key] }
    return $result
}

function Set-DotEnvValue([string]$Path, [string]$Name, [string]$Value) {
    $lines = @(Get-Content -LiteralPath $Path)
    $seen = $false
    for ($i=0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match ("^\s*" + [regex]::Escape($Name) + "\s*=")) {
            $lines[$i] = "$Name=$Value"
            $seen = $true
        }
    }
    if (-not $seen) { $lines += "$Name=$Value" }
    [System.IO.File]::WriteAllLines($Path, $lines, (New-Object System.Text.UTF8Encoding($false)))
}

function Set-DisposablePairInLocalEnv([string]$Path, [string]$DatabaseValue, [string]$FilesValue) {
    Set-DotEnvValue -Path $Path -Name 'DIARIES_DB_DATA_DIR' -Value $DatabaseValue
    Set-DotEnvValue -Path $Path -Name 'DIARIES_FILES_DIR' -Value $FilesValue
}

function Test-WindowsSharePath([string]$Path) {
    # Probe with robocopy, not just Test-Path: the Step 3-7 Windows engines use robocopy for
    # durable Files capture/staging, and Windows may have different SMB credential/session
    # behaviour for a hostname alias. The probe creates only a uniquely named temporary child.
    $token = [Guid]::NewGuid().ToString('N')
    $source = Join-Path ([System.IO.Path]::GetTempPath()) "0033-step9-smb-probe-$token"
    $destination = Join-Path $Path ".0033-step9-smb-probe-$token"
    try {
        New-Item -ItemType Directory -Path $source -Force | Out-Null
        [System.IO.File]::WriteAllText((Join-Path $source 'probe.txt'),"0033 step9 SMB probe`n",(New-Object System.Text.UTF8Encoding($false)))
        $saved = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            & robocopy.exe $source $destination /MIR /COPY:DAT /DCOPY:DAT /R:0 /W:0 /NP /NDL /NFL *> $null
            $code = $LASTEXITCODE
        } finally { $ErrorActionPreference = $saved }
        return ($code -lt 8)
    } catch {
        return $false
    } finally {
        try { if (Test-Path -LiteralPath $destination) { Remove-Item -LiteralPath $destination -Recurse -Force -ErrorAction SilentlyContinue } } catch { }
        try { if (Test-Path -LiteralPath $source) { Remove-Item -LiteralPath $source -Recurse -Force -ErrorAction SilentlyContinue } } catch { }
    }
}

function Resolve-WindowsNasHost([string]$ConfiguredHost, [string]$Share, [string]$ContentPath) {
    $candidates = New-Object System.Collections.Generic.List[string]
    if (-not [string]::IsNullOrWhiteSpace($ConfiguredHost)) { [void]$candidates.Add($ConfiguredHost) }
    if ($ConfiguredHost -match '^([^.]+)\.') {
        $short = $Matches[1]
        if (-not $candidates.Contains($short)) { [void]$candidates.Add($short) }
    }
    foreach ($candidate in $candidates) {
        $probe = "\\$candidate\$Share\$ContentPath"
        if (Test-WindowsSharePath -Path $probe) {
            Write-Host "PASS: Windows NAS access available through $probe"
            return $candidate
        }
        Write-Host "INFO: Windows NAS access unavailable through $probe"
    }
    throw "Windows cannot access the NAS Files parent through the configured host '$ConfiguredHost' or its short-host alias. Establish Windows SMB credentials first."
}

function Remove-DisposablePath([string]$Path, [string]$Label) {
    if (Test-Path -LiteralPath $Path) {
        Write-Host "Resetting previous disposable ${Label}: ${Path}"
        Remove-Item -LiteralPath $Path -Recurse -Force -ErrorAction Stop
    }
}

function Import-ProcessEnv([hashtable]$Values) {
    foreach ($key in $Values.Keys) { [Environment]::SetEnvironmentVariable([string]$key,[string]$Values[$key],'Process') }
}

function Get-PythonCommand {
    $python = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($null -ne $python) { return [pscustomobject]@{File=$python.Source; Prefix=@()} }
    $py = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($null -ne $py) { return [pscustomobject]@{File=$py.Source; Prefix=@('-3')} }
    throw 'Python 3 is required.'
}

function Invoke-NativeCapture([string]$File, [string[]]$Arguments) {
    $saved = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $output = @(& $File @Arguments 2>&1 | ForEach-Object { [string]$_ })
        $code = $LASTEXITCODE
    } finally { $ErrorActionPreference = $saved }
    [pscustomobject]@{ExitCode=$code; Output=$output}
}

function Invoke-Checked([string]$File, [string[]]$Arguments, [string]$Label) {
    $result = Invoke-NativeCapture -File $File -Arguments $Arguments
    foreach ($line in $result.Output) { Write-Host $line }
    if ($result.ExitCode -ne 0) { throw "$Label failed with exit code $($result.ExitCode)." }
    return $result
}

function Invoke-ExpectFailure([scriptblock]$Action, [string]$Label) {
    $failed = $false
    try { & $Action } catch { $failed=$true; Write-Host "PASS: expected rejection - $Label"; Write-Host "  $($_.Exception.Message)" }
    if (-not $failed -and $LASTEXITCODE -ne 0) { $failed=$true; Write-Host "PASS: expected rejection - $Label (exit $LASTEXITCODE)" }
    if (-not $failed) { throw "Negative case unexpectedly succeeded: $Label" }
}

function Get-ComposeArgs { @('compose','--env-file',$ModeEnv,'--env-file',$LocalEnv,'-f',$ComposeFile) }

function Invoke-Docker([string[]]$Arguments, [switch]$AllowFailure) {
    $result = Invoke-NativeCapture -File 'docker.exe' -Arguments $Arguments
    if (-not $AllowFailure -and $result.ExitCode -ne 0) { throw "docker $($Arguments -join ' ') failed:`n$($result.Output -join [Environment]::NewLine)" }
    return $result
}

function Get-ContainerState([string]$Name) {
    $r = Invoke-Docker -Arguments @('inspect','--format','{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}',$Name) -AllowFailure
    if ($r.ExitCode -ne 0 -or $r.Output.Count -eq 0) { return 'absent' }
    return ([string]$r.Output[-1]).Trim()
}

function Wait-Container([string]$Name, [int]$Seconds=180) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $deadline) {
        $state = Get-ContainerState -Name $Name
        if ($state -in @('healthy','running')) { return }
        if ($state -in @('unhealthy','exited','dead')) { throw "Container $Name entered state $state" }
        Start-Sleep -Seconds 2
    }
    throw "Timed out waiting for container $Name"
}

function Invoke-DbScalar([string]$Sql) {
    $r = Invoke-Docker -Arguments @('exec','diaries-local-db','psql','--no-psqlrc','-At','--username',$env:DIARIES_DB_USERNAME,'--dbname',$env:DIARIES_DB_NAME,'--set','ON_ERROR_STOP=1','--command',$Sql)
    if ($r.ExitCode -ne 0) { throw "SQL failed: $Sql`n$($r.Output -join [Environment]::NewLine)" }
    return ([string]$r.Output[-1]).Trim()
}

function Write-Fingerprint([string]$Path, [string]$FilesRoot) {
    $sql = @"
SELECT json_build_object(
 'counts', json_build_object(
   'diary',(SELECT count(*) FROM public.diary),
   'page',(SELECT count(*) FROM public.page),
   'fragment',(SELECT count(*) FROM public.fragment),
   'marquee',(SELECT count(*) FROM public.marquee),
   'image',(SELECT count(*) FROM public.image),
   'person',(SELECT count(*) FROM public.person)),
 'fragmentTypes',(SELECT coalesce(json_object_agg(type,cnt),'{}'::json) FROM (SELECT coalesce(type::text,'NULL') type,count(*) cnt FROM public.fragment GROUP BY type ORDER BY type) q),
 'reusedImageReferenceGroups',(SELECT count(*) FROM (SELECT image_id FROM public.fragment WHERE image_id IS NOT NULL GROUP BY image_id HAVING count(*)>1) q),
 'sampleFragment',(SELECT row_to_json(q) FROM (SELECT id,version,type,image_id,page_id,year,month,day,sequence,text FROM public.fragment ORDER BY id LIMIT 1) q),
 'sampleImage',(SELECT row_to_json(q) FROM (SELECT id,relative_path,checksum,mime_type FROM public.image ORDER BY id LIMIT 1) q),
 'sampleMarquee',(SELECT row_to_json(q) FROM (SELECT id,page_id,fragment_id,x,y,width,height FROM public.marquee ORDER BY id LIMIT 1) q)
)::text;
"@
    $dbText = Invoke-DbScalar -Sql $sql
    $db = $dbText | ConvertFrom-Json
    $files = @()
    [int64]$totalBytes = 0
    $root = [System.IO.Path]::GetFullPath($FilesRoot).TrimEnd('\')
    foreach ($file in Get-ChildItem -LiteralPath $root -Recurse -File | Sort-Object FullName) {
        $relative = $file.FullName.Substring($root.Length).TrimStart('\').Replace('\','/')
        if ($relative -eq '.image-staging' -or $relative.StartsWith('.image-staging/')) { continue }
        $hash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        [int64]$sizeBytes = $file.Length
        $totalBytes += $sizeBytes
        $files += [pscustomobject][ordered]@{path=$relative; sizeBytes=$sizeBytes; sha256=$hash}
    }
    $fingerprint = [pscustomobject][ordered]@{
        schemaVersion=1; feature='0033-FEAT'; step=9; logicalDataset=$DatasetName
        database=$db
        files=[pscustomobject][ordered]@{fileCount=$files.Count; totalBytes=$totalBytes; entries=$files}
    }
    $json = $fingerprint | ConvertTo-Json -Depth 20
    [System.IO.File]::WriteAllText($Path,$json+[Environment]::NewLine,(New-Object System.Text.UTF8Encoding($false)))
    return $fingerprint
}

function Assert-RepresentativeState([object]$Fingerprint) {
    Require ([int64]$Fingerprint.database.counts.marquee -gt 0) 'Disposable dataset must contain MARQUEE state.'
    $imageFragments = 0
    if ($null -ne $Fingerprint.database.fragmentTypes.IMAGE) { $imageFragments = [int64]$Fingerprint.database.fragmentTypes.IMAGE }
    Require ($imageFragments -gt 0) 'Disposable dataset must contain IMAGE Fragments.'
    Require ([int64]$Fingerprint.database.reusedImageReferenceGroups -gt 0) 'Disposable dataset must contain at least one reused Image reference.'
    Require ([int64]$Fingerprint.files.fileCount -ge 2) 'Disposable dataset must contain multiple durable Files.'
    $nested = @($Fingerprint.files.entries | Where-Object { ([string]$_.path).Contains('/') })
    Require ($nested.Count -gt 0) 'Disposable dataset must contain at least one nested durable Files path.'
}

function Compare-FingerprintFiles([string]$Before, [string]$After) {
    $a = Get-Content -Raw -LiteralPath $Before
    $b = Get-Content -Raw -LiteralPath $After
    Require ($a -ceq $b) 'Post-restore fingerprint does not exactly match the pre-backup fingerprint.'
}

Require (Test-Path -LiteralPath $LocalEnv -PathType Leaf) "Machine-local environment file is required: $LocalEnv"
Require (Test-Path -LiteralPath $SourceBackup -PathType Container) "Source complete backup does not exist: $SourceBackup"
Require ($DatasetName -match '^[A-Za-z0-9][A-Za-z0-9._-]*$') 'DatasetName must be a safe leaf name.'
Require ($FilesDir -match '^[A-Za-z0-9][A-Za-z0-9._-]*$') 'FilesDir must be a safe leaf name.'
Require ($DatasetName -ne 'common') 'Step 9 must use a disposable dataset, never common.'
Require ($FilesDir -ne 'files-development-common' -and $FilesDir -ne 'files') 'Step 9 must use a disposable Files selector.'

$SourceBackup = [System.IO.Path]::GetFullPath($SourceBackup)
$timestamp = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
if ([string]::IsNullOrWhiteSpace($EvidenceDirectory)) { $EvidenceDirectory = Join-Path $FeatureDir "evidence\Step 9\runtime-$timestamp" }
$EvidenceDirectory = [System.IO.Path]::GetFullPath($EvidenceDirectory)
Require (-not (Test-Path -LiteralPath $EvidenceDirectory)) "EvidenceDirectory already exists: $EvidenceDirectory"
New-Item -ItemType Directory -Path $EvidenceDirectory -Force | Out-Null
Start-Transcript -LiteralPath (Join-Path $EvidenceDirectory 'REHEARSAL-TRANSCRIPT.txt') -Force | Out-Null

$localEnvBytes = [System.IO.File]::ReadAllBytes($LocalEnv)
$localEnvSha = (Get-FileHash -LiteralPath $LocalEnv -Algorithm SHA256).Hash.ToLowerInvariant()
$temporaryLocalEnvActive = $false
$composeStarted = $false
$originalWindowsNasHost = [Environment]::GetEnvironmentVariable('DIARIES_WINDOWS_NAS_HOST','Process')
$windowsNasHostOverridden = $false
$filesRoot = $null
$databasePath = Join-Path $ProjectDir "data\database\$DatasetName"
$backupRoot = Join-Path $ProjectDir "data\dataset-backups\$DatasetName"
$restoreRoot = Join-Path $ProjectDir "data\dataset-restores\$DatasetName"
$backupId = [DateTime]::UtcNow.ToString('yyyyMMdd-HHmmssZ')
$finalBackup = Join-Path $backupRoot $backupId
$python = Get-PythonCommand

try {
    Write-Host '0033 Step 9 - full disposable backup/restore rehearsal'
    Write-Host "  Source seed backup: $SourceBackup"
    Write-Host "  Disposable dataset: $DatasetName"
    Write-Host "  Disposable Files:   $FilesDir"
    Write-Host "  Evidence:           $EvidenceDirectory"
    Write-Host ''

    & $python.File @($python.Prefix + @($ManifestHelper,'verify','--backup-dir',$SourceBackup))
    if ($LASTEXITCODE -ne 0) { throw 'Source seed complete backup failed schema-2 validation.' }

    foreach ($name in 'diaries-local-db','diaries-local-mqtt','diaries-local-responder','diaries-local-web','diaries-local-client') {
        $state = Get-ContainerState -Name $name
        Require ($state -eq 'absent' -or $state -in @('exited','dead')) "Refusing rehearsal while $name is active ($state). Stop local-docker-build first."
    }
    [System.IO.File]::WriteAllBytes((Join-Path $EvidenceDirectory 'local.env.original'),$localEnvBytes)
    [System.IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'local.env.original.sha256'),$localEnvSha+[Environment]::NewLine,(New-Object System.Text.UTF8Encoding($false)))
    Set-DisposablePairInLocalEnv -Path $LocalEnv -DatabaseValue "./data/database/$DatasetName" -FilesValue $FilesDir
    $temporaryLocalEnvActive = $true

    $envValues = Merge-DotEnv -First (Read-DotEnv $ModeEnv) -Second (Read-DotEnv $LocalEnv)
    Import-ProcessEnv -Values $envValues
    if (-not $env:DIARIES_DB_NAME) { $env:DIARIES_DB_NAME='diaries' }
    if (-not $env:DIARIES_DB_USERNAME) { $env:DIARIES_DB_USERNAME='diaries' }

    $content = ([string]$env:DIARIES_NAS_CONTENT_PATH).Trim('/').Replace('/','\')

    # The Docker CIFS mount and the host-side Windows tooling do not have to use the
    # same DNS spelling. Keep DIARIES_NAS_HOST unchanged for Compose so the normal
    # local-docker-build/local-published-smoke project and volume identities remain
    # distinct. Supply a process-only host alias to the Windows dataset resolver.
    $windowsNasHost = Resolve-WindowsNasHost -ConfiguredHost ([string]$env:DIARIES_NAS_HOST) -Share ([string]$env:DIARIES_NAS_SHARE) -ContentPath $content
    [Environment]::SetEnvironmentVariable('DIARIES_WINDOWS_NAS_HOST',$windowsNasHost,'Process')
    $windowsNasHostOverridden = $true
    if ($windowsNasHost -ne [string]$env:DIARIES_NAS_HOST) {
        Write-Host "INFO: using host-only DIARIES_WINDOWS_NAS_HOST '$windowsNasHost' for Windows SMB access; Docker keeps DIARIES_NAS_HOST '$($env:DIARIES_NAS_HOST)'."
    } else {
        Write-Host "PASS: configured DIARIES_NAS_HOST '$windowsNasHost' is also reachable from Windows."
    }
    $filesRoot = "\\$windowsNasHost\$($env:DIARIES_NAS_SHARE)\$content\$FilesDir"

    if ($ResetDisposable) {
        Require ($DatasetName -eq '0033-step9-rehearsal') '-ResetDisposable is permitted only for the default 0033-step9-rehearsal dataset.'
        Require ($FilesDir -eq 'files-0033-step9-rehearsal') '-ResetDisposable is permitted only for the default files-0033-step9-rehearsal selector.'
        Remove-DisposablePath -Path $databasePath -Label 'database directory'
        Remove-DisposablePath -Path $backupRoot -Label 'backup namespace'
        Remove-DisposablePath -Path $restoreRoot -Label 'restore namespace'
        Remove-DisposablePath -Path $filesRoot -Label 'Files root'
    }

    Require (-not (Test-Path -LiteralPath $databasePath)) "Disposable database directory already exists: $databasePath"
    Require (-not (Test-Path -LiteralPath $backupRoot)) "Disposable backup namespace already exists: $backupRoot"
    Require (-not (Test-Path -LiteralPath $restoreRoot)) "Disposable restore namespace already exists: $restoreRoot"
    Require (-not (Test-Path -LiteralPath $filesRoot)) "Disposable Files root already exists: $filesRoot"
    New-Item -ItemType Directory -Path $filesRoot -Force | Out-Null

    Write-Host 'Starting disposable PostgreSQL + MQTT foundation...'
    $compose = Get-ComposeArgs
    Invoke-Checked -File 'docker.exe' -Arguments ($compose + @('up','-d','diaries-db','diaries-mqtt')) -Label 'Docker foundation start' | Out-Null
    $composeStarted = $true
    Wait-Container 'diaries-local-db'
    Wait-Container 'diaries-local-mqtt'

    Write-Host 'Seeding disposable PostgreSQL from the verified source backup...'
    $seedDump = Join-Path $SourceBackup 'database\diaries.dump'
    Invoke-Checked -File 'docker.exe' -Arguments @('cp',$seedDump,'diaries-local-db:/tmp/0033-step9-seed.dump') -Label 'docker cp seed dump' | Out-Null
    $seedSql = 'dropdb --force --if-exists -U "$POSTGRES_USER" "$POSTGRES_DB" && createdb -U "$POSTGRES_USER" "$POSTGRES_DB" && pg_restore --exit-on-error --no-owner --no-privileges -U "$POSTGRES_USER" -d "$POSTGRES_DB" /tmp/0033-step9-seed.dump && rm -f /tmp/0033-step9-seed.dump'
    Invoke-Checked -File 'docker.exe' -Arguments @('exec','diaries-local-db','sh','-lc',$seedSql) -Label 'seed database restore' | Out-Null

    Write-Host 'Seeding disposable Files root from the same source backup...'
    $sourceFiles = Join-Path $SourceBackup 'files'
    & robocopy.exe $sourceFiles $filesRoot /MIR /COPY:DAT /DCOPY:DAT /R:2 /W:1 /NP /NDL /NFL
    $robo = $LASTEXITCODE
    if ($robo -ge 8) { throw "Seed Files robocopy failed with exit code $robo" }
    New-Item -ItemType Directory -Path (Join-Path $filesRoot '.image-staging') -Force | Out-Null

    Write-Host 'Starting the complete local-docker-build stack against the disposable pair...'
    & (Join-Path $ProjectDir 'scripts\windows\local-docker-build\start.bat')
    if ($LASTEXITCODE -ne 0) { throw 'local-docker-build start failed.' }
    foreach ($name in 'diaries-local-db','diaries-local-mqtt','diaries-local-responder','diaries-local-web','diaries-local-client') { Wait-Container $name 240 }

    $beforePath = Join-Path $EvidenceDirectory 'FINGERPRINT-BEFORE.json'
    $before = Write-Fingerprint -Path $beforePath -FilesRoot $filesRoot
    Assert-RepresentativeState -Fingerprint $before
    Write-Host "PASS: representative disposable state present: MARQUEE + IMAGE + reused Image references + nested Files"

    Write-Host "Creating new complete rehearsal backup $backupId ..."
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $BackupScript -ModeName $ModeName -ProjectDir $ProjectDir -BackupId $backupId
    if ($LASTEXITCODE -ne 0) { throw 'Complete rehearsal backup failed.' }
    Require (Test-Path -LiteralPath $finalBackup -PathType Container) "Expected completed backup not found: $finalBackup"
    & $python.File @($python.Prefix + @($ManifestHelper,'verify','--backup-dir',$finalBackup))
    if ($LASTEXITCODE -ne 0) { throw 'Independent validation of rehearsal backup failed.' }

    Write-Host 'Running destructive-media negative cases against disposable backup copies...'
    $negativeDir = Join-Path $EvidenceDirectory 'negative-media'
    & $python.File @($python.Prefix + @($NegativeHelper,'--backup-dir',$finalBackup,'--validator',$ManifestHelper,'--work-dir',$negativeDir))
    if ($LASTEXITCODE -ne 0) { throw 'Negative media cases failed.' }

    Write-Host 'Running mismatched-target restore-preflight negative case...'
    $mismatchParent = Join-Path $EvidenceDirectory 'mismatched-target'
    $mismatchBackup = Join-Path $mismatchParent $backupId
    New-Item -ItemType Directory -Path $mismatchParent -Force | Out-Null
    Copy-Item -LiteralPath $finalBackup -Destination $mismatchBackup -Recurse
    $mismatchManifestPath = Join-Path $mismatchBackup 'dataset-manifest.json'
    $mismatchManifest = Get-Content -Raw -LiteralPath $mismatchManifestPath | ConvertFrom-Json
    $mismatchManifest.logicalDataset = '0033-step9-other-dataset'
    [System.IO.File]::WriteAllText($mismatchManifestPath,($mismatchManifest|ConvertTo-Json -Depth 20)+[Environment]::NewLine,(New-Object System.Text.UTF8Encoding($false)))
    & $RestoreWrapper preflight $mismatchBackup
    if ($LASTEXITCODE -eq 0) { throw 'Mismatched target dataset preflight unexpectedly succeeded.' }
    Write-Host 'PASS: mismatched target dataset rejected.'
    Remove-Item -LiteralPath $mismatchParent -Recurse -Force

    Write-Host 'Mutating both disposable durable halves after the backup...'
    [void](Invoke-DbScalar -Sql "UPDATE public.fragment SET version = version + 1000 WHERE id=(SELECT min(id) FROM public.fragment); SELECT 1;")
    $candidateFiles = @($before.files.entries | Where-Object { ([string]$_.path).ToLowerInvariant() -notlike '*thumbs.db' })
    Require ($candidateFiles.Count -ge 2) 'Need at least two non-Thumbs durable files for change/delete mutation.'
    $changePath = Join-Path $filesRoot (([string]$candidateFiles[0].path).Replace('/','\'))
    $deletePath = Join-Path $filesRoot (([string]$candidateFiles[1].path).Replace('/','\'))
    [System.IO.File]::AppendAllText($changePath,"`n0033 STEP9 MUTATED`n",(New-Object System.Text.UTF8Encoding($false)))
    Remove-Item -LiteralPath $deletePath -Force
    $extraPath = Join-Path $filesRoot '0033-step9\post-backup-extra.txt'
    New-Item -ItemType Directory -Path (Split-Path -Parent $extraPath) -Force | Out-Null
    [System.IO.File]::WriteAllText($extraPath,"post-backup extra durable file`n",(New-Object System.Text.UTF8Encoding($false)))
    $mutatedPath = Join-Path $EvidenceDirectory 'FINGERPRINT-MUTATED.json'
    [void](Write-Fingerprint -Path $mutatedPath -FilesRoot $filesRoot)
    Require ((Get-Content -Raw $beforePath) -cne (Get-Content -Raw $mutatedPath)) 'Mutation fingerprint unexpectedly matches baseline.'

    Write-Host 'Running unexpected staging payload negative case...'
    $unexpectedStage = Join-Path $filesRoot '.image-staging\unexpected-step9.bin'
    [System.IO.File]::WriteAllBytes($unexpectedStage,[byte[]](1,2,3,4))
    & $BackupWrapper preflight
    if ($LASTEXITCODE -eq 0) { throw 'Backup preflight unexpectedly accepted unexplained staging payload.' }
    Write-Host 'PASS: unexplained staging payload rejected.'
    Remove-Item -LiteralPath $unexpectedStage -Force

    Write-Host 'Restoring the complete rehearsal backup through the real Step 5-7 commands...'
    & $RestoreWrapper preflight $backupId
    if ($LASTEXITCODE -ne 0) { throw 'Restore preflight failed.' }
    & $RestoreWrapper prepare $backupId
    if ($LASTEXITCODE -ne 0) { throw 'Restore prepare failed/cancelled. Type RESTORE when prompted.' }
    & $RestoreWrapper apply $backupId
    if ($LASTEXITCODE -ne 0) { throw 'Restore apply failed/cancelled. Type APPLY when prompted.' }

    Write-Host 'Forcing one failed postflight to prove failure leaves writers stopped...'
    $postflightExtra = Join-Path $filesRoot '0033-step9-postflight-negative.txt'
    [System.IO.File]::WriteAllText($postflightExtra,"force Step 9 postflight failure`n",(New-Object System.Text.UTF8Encoding($false)))
    & $RestoreWrapper postflight $backupId
    if ($LASTEXITCODE -eq 0) { throw 'Failed-postflight negative case unexpectedly succeeded.' }
    $responderState = Get-ContainerState -Name 'diaries-local-responder'
    Require ($responderState -notin @('running','healthy','starting')) "Responder unexpectedly running after failed postflight: $responderState"
    Write-Host 'PASS: failed postflight rejected and writer remained stopped.'
    Remove-Item -LiteralPath $postflightExtra -Force

    Write-Host 'Retrying postflight after removing the injected fault...'
    & $RestoreWrapper postflight $backupId
    if ($LASTEXITCODE -ne 0) { throw 'Corrected postflight retry failed.' }

    $afterPath = Join-Path $EvidenceDirectory 'FINGERPRINT-AFTER.json'
    [void](Write-Fingerprint -Path $afterPath -FilesRoot $filesRoot)
    Compare-FingerprintFiles -Before $beforePath -After $afterPath
    Write-Host 'PASS: database + Files fingerprint exactly returned to the pre-backup state.'

    $preparedState = Join-Path $restoreRoot "$backupId.prepared\restore-state.json"
    Require (Test-Path -LiteralPath $preparedState -PathType Leaf) "Restore state missing: $preparedState"
    $state = Get-Content -Raw -LiteralPath $preparedState | ConvertFrom-Json
    $safetyBackup = [string]$state.safetyBackup.directory
    Require (Test-Path -LiteralPath $safetyBackup -PathType Container) "Safety backup missing: $safetyBackup"
    Write-Host 'Proving the pre-restore safety backup remains valid and structurally usable...'
    & $RestoreWrapper preflight $safetyBackup
    if ($LASTEXITCODE -ne 0) { throw 'Safety backup preflight failed.' }

    Write-Host 'Checking client/reader-service health after accepted restore...'
    foreach ($name in 'diaries-local-responder','diaries-local-web','diaries-local-client') { Wait-Container $name 180 }
    $client = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8080/diaries/' -TimeoutSec 15
    Require ($client.StatusCode -eq 200) 'Client /diaries/ did not return HTTP 200.'
    $web = Invoke-WebRequest -UseBasicParsing -Uri 'http://localhost:8082/health/ready' -TimeoutSec 15
    Require ($web.StatusCode -eq 200) 'Reader/web readiness endpoint did not return HTTP 200.'

    $summary = [ordered]@{
        schemaVersion=1; feature='0033-FEAT'; step=9; status='PASSED'; completedAt=[DateTime]::UtcNow.ToString('o')
        disposableDataset=$DatasetName; disposableFiles=$FilesDir; sourceSeedBackup=$SourceBackup; rehearsalBackup=$finalBackup
        fingerprintBefore=(Split-Path -Leaf $beforePath); fingerprintAfter=(Split-Path -Leaf $afterPath); fingerprintExactMatch=$true
        negativeCases=@('missing dump','modified dump','missing Files item','modified Files item','extra backup item','invalid manifest','mismatched target dataset','unexpected staging payload','interrupted backup','failed postflight')
        safetyBackup=$safetyBackup; clientHttpStatus=$client.StatusCode; readerHealthStatus=$web.StatusCode
        localEnvOriginalSha256=$localEnvSha
    }
    [System.IO.File]::WriteAllText((Join-Path $EvidenceDirectory 'SUMMARY.json'),($summary|ConvertTo-Json -Depth 10)+[Environment]::NewLine,(New-Object System.Text.UTF8Encoding($false)))
    Write-Host ''
    Write-Host 'STEP 9 DISPOSABLE BACKUP/RESTORE REHEARSAL PASSED.' -ForegroundColor Green
    Write-Host "  Evidence: $EvidenceDirectory"
    Write-Host "  Rehearsal backup: $finalBackup"
    Write-Host "  Safety backup: $safetyBackup"
    Write-Host '  Database/Files fingerprint: exact before/after match'
    Write-Host '  Client + reader-service: HTTP 200'
}
finally {
    if ($composeStarted -and $temporaryLocalEnvActive) {
        try {
            Write-Host 'Stopping disposable local-docker-build stack before restoring local.env...'
            $compose = Get-ComposeArgs
            $null = Invoke-Docker -Arguments ($compose + @('down','--remove-orphans')) -AllowFailure
        } catch { Write-Warning "Could not stop disposable Compose stack: $($_.Exception.Message)" }
    }
    if ($windowsNasHostOverridden) {
        [Environment]::SetEnvironmentVariable('DIARIES_WINDOWS_NAS_HOST',$originalWindowsNasHost,'Process')
        Write-Host 'PASS: original DIARIES_WINDOWS_NAS_HOST process setting restored.'
    }
    if ($temporaryLocalEnvActive) {
        [System.IO.File]::WriteAllBytes($LocalEnv,$localEnvBytes)
        $restoredSha = (Get-FileHash -LiteralPath $LocalEnv -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($restoredSha -ne $localEnvSha) { Write-Warning 'local.env byte-for-byte restoration check FAILED.' }
        else { Write-Host 'PASS: original local.env restored byte-for-byte.' }
    }
    try { Stop-Transcript | Out-Null } catch { }
}
