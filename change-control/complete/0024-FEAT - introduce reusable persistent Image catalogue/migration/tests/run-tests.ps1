[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Container,
    [Parameter(Mandatory)][string]$BackupFile,
    [Parameter(Mandatory)][string]$EvidenceDirectory
)
$ErrorActionPreference='Stop'
if (Test-Path -LiteralPath $EvidenceDirectory) { throw 'Choose a new evidence directory.' }
$inspection = docker inspect $Container | ConvertFrom-Json
if ($LASTEXITCODE -ne 0 -or $Container -notlike 'diaries-0024-*-test*' -or
    $inspection[0].HostConfig.NetworkMode -ne 'none' -or '/var/lib/postgresql' -notin $inspection[0].HostConfig.Tmpfs.PSObject.Properties.Name) {
    throw 'Tests require a dedicated diaries-0024-*-test container, network none, PostgreSQL storage in tmpfs.'
}
$evidence = (New-Item -ItemType Directory -Path $EvidenceDirectory).FullName
$migration = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$prefix = 't0024_' + [guid]::NewGuid().ToString('N').Substring(0,8)
$seed = $prefix + '_seed'
$passed = New-Object 'Collections.Generic.List[string]'
function Docker-Checked {
    param([string[]]$Arguments)
    $out = & docker @Arguments 2>&1
    if ($LASTEXITCODE -ne 0) { throw ($out -join "`n") }
    return $out
}
$null = Docker-Checked @('cp', $migration, ($Container + ':/tmp/' + $prefix))
$null = Docker-Checked @('cp', (Resolve-Path -LiteralPath $BackupFile).Path, ($Container + ':/tmp/' + $prefix + '.dump'))
$null = Docker-Checked @('exec',$Container,'createdb','-U','diaries',$seed)
$null = Docker-Checked @('exec',$Container,'pg_restore','--no-owner','--no-privileges','-U','diaries','-d',$seed,('/tmp/'+$prefix+'.dump'))
function New-TestDatabase {
    param([string]$Suffix,[string]$Template=$seed)
    $name=$prefix+'_'+$Suffix
    $null = Docker-Checked @('exec',$Container,'createdb','-U','diaries','-T',$Template,$name)
    return $name
}
function Psql-Test {
    param([string]$Name,[string]$Database,[string[]]$Arguments,[bool]$ShouldPass=$true,[string]$ExpectedError='')
    $output = & docker exec $Container psql -X -U diaries -d $Database -v ON_ERROR_STOP=1 @Arguments 2>&1
    $code=$LASTEXITCODE
    [IO.File]::WriteAllText((Join-Path $evidence ($Name+'.txt')), ($output -join "`n")+"`n", (New-Object Text.UTF8Encoding($false)))
    if (($code -eq 0) -ne $ShouldPass) { throw "Unexpected result for $Name (exit $code); see log." }
    if (!$ShouldPass -and ($output -join "`n") -notmatch [regex]::Escape($ExpectedError)) { throw "Wrong rejection reason for $Name; see log." }
    $passed.Add($Name)
}
$dir='/tmp/'+$prefix
$workflow=@('-f',($dir+'/001-preflight.sql'),'-f',($dir+'/002-add-image-catalogue.sql'),'-f',($dir+'/003-postflight.sql'))
$good=New-TestDatabase 'good'
Psql-Test '01-read-only-preflight' $good @('-c','SET default_transaction_read_only=on;','-f',($dir+'/001-preflight.sql'))
Psql-Test '02-fresh-apply' $good $workflow
Psql-Test '03-idempotent-rerun' $good $workflow
Psql-Test '04-constraints' $good @('-f',($dir+'/tests/constraints.sql'))
$null=Docker-Checked @('exec',$Container,'psql','-X','-U','diaries','-d',$good,'-v','ON_ERROR_STOP=1','-c',
    "INSERT INTO public.image(relative_path,mime_type,original_filename,width,height,checksum) VALUES ('existing.png','image/png','existing.png',1,1,repeat('a',64));")
Psql-Test '05-populated-correct-rerun' $good $workflow
$mutations=[ordered]@{
    'missing-column'='ALTER TABLE public.image DROP COLUMN caption'
    'wrong-type'='ALTER TABLE public.image ALTER COLUMN mime_type TYPE varchar(128)'
    'wrong-default'='ALTER TABLE public.image ALTER COLUMN version SET DEFAULT 1'
    'nullable'='ALTER TABLE public.image ALTER COLUMN alt_text DROP NOT NULL'
    'missing-check'='ALTER TABLE public.image DROP CONSTRAINT image_width_check'
    'wrong-check'='ALTER TABLE public.image DROP CONSTRAINT image_height_check; ALTER TABLE public.image ADD CONSTRAINT image_height_check CHECK (height >= 0)'
    'wrong-index'='DROP INDEX public.image_relative_path_ci_uq; CREATE UNIQUE INDEX image_relative_path_ci_uq ON public.image(relative_path)'
    'missing-index'='DROP INDEX public.image_checksum_idx'
    'sequence-change'='ALTER SEQUENCE public.image_id_seq INCREMENT BY 2'
    'identity-change'='ALTER TABLE public.image ALTER COLUMN id SET GENERATED ALWAYS'
    'extra-column'='ALTER TABLE public.image ADD COLUMN unexpected text'
    'row-security'='ALTER TABLE public.image ENABLE ROW LEVEL SECURITY'
}
foreach ($case in $mutations.Keys) {
    $db=New-TestDatabase ($case.Replace('-','_')) $good
    $null=Docker-Checked @('exec',$Container,'psql','-X','-U','diaries','-d',$db,'-v','ON_ERROR_STOP=1','-c',$mutations[$case])
    Psql-Test ('reject-'+$case) $db $workflow $false 'Partial or incompatible Image schema'
}
$partial=New-TestDatabase 'partial'
$null=Docker-Checked @('exec',$Container,'psql','-X','-U','diaries','-d',$partial,'-c','CREATE SEQUENCE public.image_id_seq')
Psql-Test 'reject-orphan-sequence' $partial $workflow $false 'Partial Image schema'
$view=New-TestDatabase 'view'
$null=Docker-Checked @('exec',$Container,'psql','-X','-U','diaries','-d',$view,'-c','CREATE VIEW public.image AS SELECT 1 AS id')
Psql-Test 'reject-view' $view $workflow $false 'not an ordinary table'
$priv=New-TestDatabase 'privileges'
$role=$prefix+'_reader'
$null=Docker-Checked @('exec',$Container,'psql','-X','-U','diaries','-d',$priv,'-c',("CREATE ROLE "+$role+"; GRANT USAGE ON SCHEMA public TO "+$role+"; GRANT SELECT ON ALL TABLES IN SCHEMA public TO "+$role))
Psql-Test 'reject-missing-privilege' $priv (@('-c',('SET ROLE '+$role))+$workflow) $false 'public USAGE/CREATE'
Psql-Test 'reject-skipped-preflight' $seed @('-f',($dir+'/002-add-image-catalogue.sql')) $false 'Run 001-preflight.sql first'
# Chronology drift between preflight and apply must fail before table creation.
$drift=New-TestDatabase 'drift'
Psql-Test 'reject-chronology-drift' $drift @('-f',($dir+'/001-preflight.sql'),'-c','UPDATE public.fragment SET version=version+1 WHERE id=(SELECT min(id) FROM public.fragment)','-f',($dir+'/002-add-image-catalogue.sql')) $false 'changed since preflight'
# Inject a postflight failure into a copy of the package. The actual apply
# script must leave no image table after its connection aborts.
$atomic=New-TestDatabase 'atomic'
$copy=Join-Path $evidence 'fault-injection'
$null=New-Item -ItemType Directory -Path $copy
foreach ($file in Get-ChildItem -LiteralPath $migration -File -Filter '*.sql') { Copy-Item -LiteralPath $file.FullName -Destination $copy }
[IO.File]::WriteAllText((Join-Path $copy '003-postflight.sql'), 'DO $$ BEGIN RAISE EXCEPTION ''Injected postflight failure''; END $$;', (New-Object Text.UTF8Encoding($false)))
$null=Docker-Checked @('cp',$copy,($Container+':/tmp/'+$prefix+'_fault'))
Psql-Test 'reject-postflight-atomic' $atomic @('-f',('/tmp/'+$prefix+'_fault/001-preflight.sql'),'-f',('/tmp/'+$prefix+'_fault/002-add-image-catalogue.sql')) $false 'Injected postflight failure'
Psql-Test 'verify-atomic-rollback' $atomic @('-c',"DO `$`$ BEGIN IF to_regclass('public.image') IS NOT NULL THEN RAISE EXCEPTION 'Table survived failed transaction'; END IF; END `$`$;")
$summary=[ordered]@{completedAtUtc=[DateTime]::UtcNow.ToString('o'); testCount=$passed.Count; passed=@($passed); container=$Container; databasePrefix=$prefix; backupFile=[IO.Path]::GetFileName($BackupFile); backupSha256=(Get-FileHash -LiteralPath $BackupFile).Hash.ToLowerInvariant(); notes='All databases were newly created inside the isolated tmpfs test container. Constraints test inserts were rolled back; no development data was changed.'}
[IO.File]::WriteAllText((Join-Path $evidence 'test-results.json'), ($summary|ConvertTo-Json -Depth 5)+"`n", (New-Object Text.UTF8Encoding($false)))
Write-Output "PASS: $($passed.Count) migration integration scenarios. Evidence: $evidence"
