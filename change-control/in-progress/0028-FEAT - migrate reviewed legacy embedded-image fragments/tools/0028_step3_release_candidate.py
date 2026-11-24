#!/usr/bin/env python3
"""Evidence-only release candidate assessment; NEVER authorises production apply.
Requires real accepted receipts, current runtime survey, and clean Git-pinned JAR.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

NAMES=('diaries-postgres','diaries-mosquitto','diaries-responder','diaries-client','diaries-web')
BACKUP='20261124-003112Z'
SHA=re.compile('^[0-9a-f]{64}$')
GIT_SHA=re.compile('^[0-9a-f]{40}$')

def require(ok,msg):
    if not ok: raise ValueError(msg)

def read(path):
    raw=Path(path).read_bytes()
    result=json.loads(raw)
    require(isinstance(result,dict),'expected JSON object')
    return result,hashlib.sha256(raw).hexdigest()

def assessment(artifact, runtime, recovery, artifact_digest):
    require(artifact['status']=='BUILT_NOT_DEPLOYED_NOT_APPROVED','unsupported artifact status')
    require(GIT_SHA.fullmatch(artifact['source_commit']) is not None,'invalid responder source revision')
    require(SHA.fullmatch(artifact['artifact_sha256']) is not None,'invalid JAR checksum')
    require(artifact_digest==artifact['artifact_sha256'],'JAR bytes differ from release receipt')
    require(runtime.get('mode')=='READ_ONLY_RELEASE_CONTRACT','live runtime survey absent')
    require(runtime.get('writerIsolationVerified') is False and
            runtime.get('productionApplyAuthorised') is False,'invalid claim in runtime survey')
    names=runtime.get('containers')
    require(isinstance(names,dict) and set(names)==set(NAMES),'production service identities differ')
    for name in NAMES:
        require(names[name].get('name')==name and names[name].get('imageId'), 'missing container identity '+name)
    require(names['diaries-postgres'].get('composeService')=='diaries-db','database Compose identity changed')
    require(names['diaries-mosquitto'].get('composeService')=='diaries-mqtt','MQTT Compose identity changed')
    require(names['diaries-responder'].get('composeService')=='diaries-responder','responder Compose identity changed')
    require('postgres:18' in names['diaries-postgres'].get('image',''),'PostgreSQL version drift')
    require(recovery.get('backupId')==BACKUP and
            recovery.get('databaseRestoreVerified') is True and
            recovery.get('restoredCounts')=={'fragments':2331,'marquees':2270,'images':85,'pages':683},
            'accepted retained database recovery receipt changed')
    require(recovery.get('productionApplyAuthorised') is False and
            recovery.get('productionWriterIsolationVerified') is False,
            'accepted recovery receipt claims production permission')
    return {
        'schema':1,'feature':'0028-FEAT','result':'RELEASE_CANDIDATE_PREPARED_NO_PRODUCTION_PERMISSION',
        'migrationJarSha256':artifact_digest,'responderGitCommit':artifact['source_commit'],
        'retainedDatabaseRecoveryBackupId':BACKUP,
        'retainedDatabaseRestoreVerified':True,
        'runtimeSurveyVerified':True,
        'fullFilesRestoreVerified':False,
        'migrationCliLifecycle':'DISPOSABLE_ONESHOT_RETAIN_UNTIL_ACCEPTED_ROLLBACK_WINDOW_CLOSED',
        'permanentResponderDependency':False,
        'currentPostgresPortPublished':runtime['publishedPostgresHostPort'],
        'currentResponderImage':names['diaries-responder']['image'],
        'openHardGates':['formal Step 1/2 owner acceptance','prod CLI/DB/files runtime test',
          'approved writer isolation and direct SQL containment','backup timer coordination',
          'fresh stopped-writer matching DB+Files rollback point','final frozen production plan',
          'signed owner production approval','postflight, retained MQTT and UI acceptance'],
        'writerIsolationVerified':False,'productionApplyAuthorised':False,
    }

def parse_kv(path):
    result={}
    for raw in Path(path).read_text(encoding='utf-8').splitlines():
        if not raw.strip():continue
        key,sep,val=raw.partition('=')
        require(bool(sep) and key not in result, 'invalid identity receipt')
        result[key]=val
    return result

def main(argv=None):
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('artifact-dir','runtime','recovery','output'):
        p.add_argument('--'+name,required=True)
    a=p.parse_args(argv)
    try:
        d=Path(a.artifact_dir)
        receipt=parse_kv(d/'ARTIFACT-IDENTITY.txt')
        artifact=d/receipt['artifact']
        require(artifact.name=='diaries-0028-reviewed-migration-fat.jar', 'unexpected artifact filename')
        require(artifact.is_file(),'release JAR missing')
        digest=hashlib.sha256(artifact.read_bytes()).hexdigest()
        runtime,_=read(a.runtime)
        recovery,_=read(a.recovery)
        result=assessment(receipt,runtime,recovery,digest)
        out=Path(a.output)
        require(not out.exists() and out.parent.is_dir(),'refusing to overwrite or create parent')
        out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        print('PASS: pinned JAR / current pluto contract / accepted retained recovery bound together')
        print('OPEN: direct SQL isolation, new rollback point, exact production dry-run and owner approval')
        print('PRODUCTION APPLY NOT AUTHORISED')
        return 0
    except (OSError,KeyError,TypeError,ValueError,json.JSONDecodeError) as e:
        print('FAIL: release candidate evidence: '+str(e),file=sys.stderr)
        return 2
if __name__=='__main__':sys.exit(main())
