#Requires -Version 7.0
param([Parameter(Mandatory)][string]$EvidenceDirectory)
$ErrorActionPreference='Stop'
if(Test-Path $EvidenceDirectory) { throw 'Choose a new evidence directory' }
$e=(New-Item -ItemType Directory $EvidenceDirectory).FullName
$m=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$repo=(Resolve-Path (Join-Path $m '../../../..')).Path
$backup=Join-Path $repo 'data/database-backups/development-infrastructure/diaries-development-20260912-203528.dump'
$schema=Join-Path $repo 'change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/migration/schema.sql'
$container='diaries-0025-schema-'+[guid]::NewGuid().ToString('N').Substring(0,12)
$owned=$false
$result=[ordered]@{status='RUNNING';startedAtUtc=[DateTime]::UtcNow.ToString('o');container=$container;liveDatabaseUsed=$false;cases=@()}
function Run([string[]]$Arguments,[string]$Log) {
 $out=& docker @Arguments 2>&1
 $code=$LASTEXITCODE
 if($Log) { [IO.File]::WriteAllText((Join-Path $e $Log),($out -join "`n")+"`n") }
 if($code -ne 0) {throw "docker failed ($code): $Log"}
 return ($out -join "`n")
}
function Sql([string[]]$Arguments,[string]$Log) {
 return Run (@('exec',$container,'psql','-X','-U','diaries','-d','image_wiring_test','-v','ON_ERROR_STOP=1')+$Arguments) $Log
}
function Reject([string]$Name,[string]$Mutation,[string]$Expected) {
 $out=& docker exec $container psql -X -U diaries -d image_wiring_test -v ON_ERROR_STOP=1 -c BEGIN -c $Mutation -f /tmp/migration/001-preflight.sql 2>&1
 $code=$LASTEXITCODE
 $text=$out -join "`n"
 [IO.File]::WriteAllText((Join-Path $e "$Name.log"),$text+"`n")
 if($code -eq 0 -or $text -notmatch [regex]::Escape($Expected)) { throw "Expected rejection not observed: $Name" }
 $result.cases += $Name
}
try {
 $result.backupSha256=(Get-FileHash $backup).Hash.ToLowerInvariant()
 if($result.backupSha256 -ne 'fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86') {throw 'Frozen backup mismatch'}
 $result.postgresImageId=Run @('image','inspect','postgres:18-alpine','--format','{{.Id}}') 'postgres-image.txt'
 $null=Run @('run','--detach','--rm','--name',$container,'--tmpfs','/var/lib/postgresql','-e','POSTGRES_USER=diaries','-e','POSTGRES_DB=image_wiring_test','-e','POSTGRES_HOST_AUTH_METHOD=trust',$result.postgresImageId) 'start.log'
 $owned=$true
 $deadline=[DateTime]::UtcNow.AddSeconds(45)
 do { & docker exec $container pg_isready -U diaries 2>&1 | Out-Null; if($LASTEXITCODE -eq 0){break}; if([DateTime]::UtcNow -gt $deadline){throw 'Database readiness timeout'}; Start-Sleep -Milliseconds 250 } while($true)
 $null=Run @('cp',$backup,"${container}:/tmp/baseline.dump")
 $null=Run @('exec',$container,'pg_restore','-U','diaries','-d','image_wiring_test','--no-owner','--no-privileges','/tmp/baseline.dump') 'restore.log'
 $null=Run @('cp',$schema,"${container}:/tmp/image.sql")
 $null=Sql @('-f','/tmp/image.sql') 'image-schema.log'
 $null=Run @('cp',$m,"${container}:/tmp/migration")
 $null=Sql @('-c','SELECT conname,convalidated,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid=''public.fragment''::regclass ORDER BY conname') 'baseline-constraints.log'
 $before=Sql @('-f','/tmp/migration/snapshot.sql') 'before.log'
 $apply=@('-f','/tmp/migration/001-preflight.sql','-f','/tmp/migration/002-add-fragment-image-reference.sql','-f','/tmp/migration/003-postflight.sql')
 $null=Sql $apply 'first-apply.log'; $result.cases+='first-apply'
 $null=Sql $apply 'repeat-apply.log'; $result.cases+='repeat-apply'
 $null=Sql @('-f','/tmp/migration/tests/constraints.sql') 'constraints.log'; $result.cases+='constraints'
 Reject 'reject-default' 'ALTER TABLE public.fragment ALTER COLUMN image_id SET DEFAULT 1' 'nullable BIGINT without default'
 Reject 'reject-wrong-type' 'ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_fk; ALTER TABLE public.fragment ALTER COLUMN image_id TYPE integer' 'nullable BIGINT without default'
 Reject 'reject-cascade' 'ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_fk; ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_fk FOREIGN KEY(image_id) REFERENCES public.image(id) ON DELETE CASCADE' 'Incompatible image foreign key'
 Reject 'reject-wrong-index' 'DROP INDEX public.fragment_image_id_idx; CREATE INDEX fragment_image_id_idx ON public.fragment(id)' 'Incompatible fragment_image_id_idx'
 Reject 'reject-weak-check' 'ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_type_check; ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_type_check CHECK(image_id IS NULL OR type=''IMAGE'')' 'Incompatible fragment_image_type_check'
 Reject 'reject-prerequisite' 'ALTER TABLE public.fragment DROP CONSTRAINT fragment_type_check' 'Expected validated MARQUEE/IMAGE'
 $null=Sql @('-c','ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_fk; ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_type_check; DROP INDEX public.fragment_image_id_idx;') 'partial-fixture.log'
 $null=Sql $apply 'partial-recovery.log'; $result.cases+='partial-recovery'
 $null=Sql @('-c','ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_fk; ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_fk FOREIGN KEY(image_id) REFERENCES public.image(id) NOT VALID; ALTER TABLE public.fragment DROP CONSTRAINT fragment_image_type_check; ALTER TABLE public.fragment ADD CONSTRAINT fragment_image_type_check CHECK(image_id IS NULL OR (type IS NOT NULL AND type=''IMAGE'')) NOT VALID;') 'unvalidated-fixture.log'
 $null=Sql $apply 'validate-existing.log'; $result.cases+='validate-existing'
 $seed='INSERT INTO public.image(id,relative_path,mime_type,original_filename,width,height,checksum) VALUES(-25001,''0025-fixture.png'',''image/png'',''0025-fixture.png'',1,1,repeat(''a'',64)); INSERT INTO public.fragment SELECT (jsonb_populate_record(NULL::public.fragment,to_jsonb(f)||jsonb_build_object(''id'',-25001,''type'',''IMAGE'',''image_id'',-25001))).* FROM public.fragment f ORDER BY id LIMIT 1;'
 $null=Sql @('-c',$seed) 'referenced-fixture.log'
 Reject 'reject-unexpected-references' 'SELECT 1' 'Existing references require explicit'
 $null=Sql (@('-v','allow_existing_references=true')+$apply) 'allow-expected-references.log'; $result.cases+='allow-expected-references'
 $null=Sql @('-c','DELETE FROM public.fragment WHERE id=-25001; DELETE FROM public.image WHERE id=-25001;') 'referenced-fixture-cleanup.log'
 $after=Sql @('-f','/tmp/migration/snapshot.sql') 'after.log'
 if($before -ne $after) {throw 'Baseline row snapshots changed'}
 $result.rowsUnchanged=$true
 $result.status='PASSED'
} catch { $result.status='FAILED';$result.failure=$_.Exception.Message;throw }
finally {
 if($owned) { $cleanup=& docker stop $container 2>&1; $result.cleanupExitCode=$LASTEXITCODE; [IO.File]::WriteAllText((Join-Path $e 'cleanup.log'),($cleanup -join "`n")+"`n"); if($LASTEXITCODE -ne 0){$result.status='CLEANUP_FAILED'} }
 $result.finishedAtUtc=[DateTime]::UtcNow.ToString('o')
 $result | ConvertTo-Json -Depth 5 | Set-Content (Join-Path $e 'result.json')
 $result | ConvertTo-Json -Depth 5 | Write-Output
}

