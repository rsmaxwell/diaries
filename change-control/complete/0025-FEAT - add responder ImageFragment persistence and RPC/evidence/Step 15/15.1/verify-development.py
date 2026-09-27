"""Verify already-applied development schema; never executes migration apply SQL."""
from pathlib import Path
import subprocess, json, hashlib, datetime, zipfile, sys
here=Path(__file__).resolve().parent
root=here.parents[5]
feature=here.parents[2]
output=Path(sys.argv[1]).resolve()
output.mkdir(parents=True, exist_ok=False)
container='diaries-development-db'
def run(args, log, data=None):
    completed=subprocess.run(args,input=data,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
    (output/log).write_bytes(completed.stdout)
    if completed.returncode: raise RuntimeError(f'{log}: exit {completed.returncode}')
    return completed.stdout
result={'startedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(), 'container':container,'database':'diaries','mode':'development-infrastructure','migrationAppliedThisRun':False,'responderStartedThisRun':False}
try:
    inspect=json.loads(subprocess.check_output(['docker','inspect',container]))[0]
    identity={k:inspect[k] for k in ['Id','Image','Created']}
    identity.update(imageName=inspect['Config']['Image'],state=inspect['State']['Status'],ports=inspect['NetworkSettings']['Ports'],mounts=inspect['Mounts'],composeProject=inspect['Config']['Labels'].get('com.docker.compose.project'))
    (output/'database-container.json').write_text(json.dumps(identity,indent=2)+'\n',encoding='utf-8')
    assert identity['state']=='running'
    backup=root/'data/database-backups/development-infrastructure/before-0025-20260927-103724.dump'
    data=backup.read_bytes()
    result['backup']={'path':str(backup),'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    run(['docker','exec','-i',container,'pg_restore','--list'],'backup-archive-list.txt',data)
    migration=feature/'migration'
    def expand(name):
        text=(migration/name).read_text(encoding='utf-8')
        for nested in ['assert-schema.sql','snapshot.sql']:
            text=text.replace('\\ir '+nested, (migration/nested).read_text(encoding='utf-8'))
        return text
    inventory="""
SELECT current_database(),current_user,version();
SELECT column_name,data_type,is_nullable,column_default FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='image_id';
SELECT conname,convalidated,condeferrable,pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='public.fragment'::regclass AND conname IN ('fragment_image_fk','fragment_image_type_check');
SELECT indexname,indexdef FROM pg_indexes WHERE schemaname='public' AND tablename='fragment' AND indexname='fragment_image_id_idx';
SELECT count(*) AS image_fragments,count(image_id) AS attached_images FROM public.fragment WHERE type='IMAGE';
"""
    sql='\\set ON_ERROR_STOP on\nBEGIN ISOLATION LEVEL REPEATABLE READ;\n'+expand('001-preflight.sql')+'\n'+expand('003-postflight.sql')+'\n'+inventory+'\nROLLBACK;\n'
    (output/'verification.sql').write_text(sql,encoding='utf-8')
    run(['docker','exec','-i',container,'psql','-X','-U','diaries','-d','diaries','-v','ON_ERROR_STOP=1'],'preflight-postflight-schema.log',sql.encode())
    jar=root/'diaries-responder/build/libs/diaries-responder-0.0.9-SNAPSHOT-fat.jar'
    result['responderArtifact']={'path':str(jar),'sha256':hashlib.sha256(jar.read_bytes()).hexdigest()}
    with zipfile.ZipFile(jar) as z: (output/'responder-build-info.properties').write_bytes(z.read('build-info.properties'))
    for name in ['diaries','diaries-responder']:
        repo=root if name=='diaries' else root/name
        for args,label in [(['rev-parse','HEAD'],'commit'),(['status','--short','--untracked-files=no'],'status')]:
            run(['git','-c','safe.directory='+repo.as_posix(),'-C',str(repo),*args],name+'-'+label+'.txt')
    result['migrationSqlSha256']={f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(migration.glob('*.sql'))}
    result['status']='PASSED'
except Exception as ex:
    result['status']='FAILED';result['error']=str(ex)
    raise
finally:
    result['finishedAtUtc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,indent=2))
