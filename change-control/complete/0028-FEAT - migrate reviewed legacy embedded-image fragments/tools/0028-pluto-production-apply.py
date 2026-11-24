#!/usr/bin/env python3
"""0028 production apply: execute only on pluto with staged accepted evidence.
Usage: python3 - apply JAR_SHA256 BACKUP_RECEIPT_SHA256 REHEARSAL_RECEIPT_SHA256
       python3 - postflight JAR_SHA256
Keep the responder and backup publisher stopped until MQTT replay and UI checks.
"""
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

STAGE = Path('/run/diaries-0028-production-migration-input')
PROJECT = Path('/home/richard/projects/diaries')
JAR = STAGE / 'diaries-0028-reviewed-migration-fat.jar'
CONFIG = PROJECT / 'config/responder/responder.json'
MANIFEST = STAGE / 'reviewed'
PLAN = STAGE / 'result/dry-run/result/0028-reviewed-dry-run-plan.json'
IMAGE = 'rsmaxwell/diaries-responder:0.0.9-build-86'
MAIN = 'com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments'
EXPECTED_PLAN = '3510eb32429f789d1b99c8e26e315d060950975afe477a2910cc86d7b7b55730'
EXPECTED_JAR = '9a2910515bbe0929c93c0557f91c2b27b8323bb9da61fb2573a0ff9b20c209a1'
BACKUP_EVIDENCE = STAGE / 'accepted-evidence/backup.md'
REHEARSAL_EVIDENCE = STAGE / 'accepted-evidence/rehearsal.md'
JOURNAL_SQL = '''BEGIN;
CREATE TABLE IF NOT EXISTS public.migration0028_source (
    fragment_id bigint PRIMARY KEY REFERENCES public.fragment(id),
    journal_schema_version integer NOT NULL DEFAULT 1 CHECK (journal_schema_version = 1),
    input_identity text NOT NULL,
    plan_sha256 varchar(64) NOT NULL,
    source_date date NOT NULL,
    original_version bigint NOT NULL,
    original_page_id bigint,
    original_html_sha256 varchar(64) NOT NULL,
    original_html text NOT NULL,
    post_html_sha256 varchar(64) NOT NULL,
    post_version bigint NOT NULL,
    image_id bigint NOT NULL REFERENCES public.image(id),
    destination_page_id bigint NOT NULL REFERENCES public.page(id),
    old_marquee_id bigint,
    committed_at timestamptz NOT NULL DEFAULT transaction_timestamp()
);
CREATE TABLE IF NOT EXISTS public.migration0028_image_occurrence (
    source_fragment_id bigint NOT NULL REFERENCES public.migration0028_source(fragment_id),
    ordinal integer NOT NULL CHECK (ordinal > 0),
    image_id bigint NOT NULL REFERENCES public.image(id),
    image_checksum varchar(64) NOT NULL,
    original_src_sha256 varchar(64) NOT NULL,
    post_caption text NOT NULL,
    post_link_url text,
    PRIMARY KEY (source_fragment_id, ordinal)
);
COMMIT;
'''

def require(condition, msg):
    if not condition: raise RuntimeError(msg)

def execute(argv, input=None):
    p = subprocess.run(argv, input=input, text=True, capture_output=True)
    if p.returncode: raise RuntimeError(f'{argv[0]} failed ({p.returncode}): {p.stderr[-1600:]}')
    return p.stdout.strip()

def sha(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(1024*1024),b''): h.update(chunk)
    return h.hexdigest()

def db(sql):
    return execute(['docker','exec','diaries-postgres','sh','-c',
       'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"',
       'sh',sql])

def isolation():
    for unit in ('diaries-complete-backup-publish.timer','diaries-complete-backup-publish.service'):
        require(execute(['systemctl','show',unit,'--property=ActiveState','--value'])=='inactive',unit+' not inactive')
    for container, expected in (('diaries-responder','false'),('diaries-postgres','true'),('diaries-mosquitto','true')):
        require(execute(['docker','inspect','-f','{{.State.Running}}',container])==expected,container+' state changed')
    hba = db('show hba_file')
    content = execute(['docker','exec','-u','0','diaries-postgres','cat',hba])
    require('# 0028-MAINTENANCE-ISOLATION' in content and
            'host all all 0.0.0.0/0 reject' in content and 'host all all ::/0 reject' in content,
            'HBA isolation missing')
    require(db("select count(*) from pg_stat_activity where backend_type='client backend' and pid<>pg_backend_pid()")=='0',
            'Active client sessions present')

def common(jarhash):
    require(jarhash==EXPECTED_JAR,'JAR hash argument mismatch')
    require(STAGE.is_dir() and not STAGE.is_symlink() and STAGE.stat().st_uid==os.getuid() and not STAGE.stat().st_mode & 0o077,
            'Private stage missing or not secure')
    require(JAR.is_file() and sha(JAR)==EXPECTED_JAR,'Pinned JAR mismatch')
    require(PLAN.is_file() and sha(PLAN)==EXPECTED_PLAN,'Accepted production plan missing/mismatched')
    require(MANIFEST.is_dir() and CONFIG.is_file(),'Production manifest/config missing')
    require(execute(['docker','inspect','-f','{{.Config.Image}}','diaries-responder'])==IMAGE,'Responder image drift')
    # No silent repair or retries. Verify read-only Files mount independently.
    shell='test -r /data/files && awk \'$2=="/data/files" && $4 ~ /(^|,)ro(,|$)/ {ok=1} END {exit !ok}\' /proc/mounts'
    execute(['docker','run','--rm','--network','none','--volumes-from','diaries-responder:ro',
             '--read-only','--entrypoint','sh',IMAGE,'-c',shell])
    plan=json.loads(PLAN.read_text())
    require(plan.get('mode')=='dry-run' and len(plan.get('conversions',[]))==71 and plan.get('deferredFragments')==[1564],
            'Plan scope mismatch')
    return plan

def private_config():
    original=json.loads(CONFIG.read_text())
    require(original.get('diaries',{}).get('root')=='/data' and original['diaries'].get('files')=='files',
            'Unexpected deployed Files-root')
    config=dict(original)
    config['db']=dict(original['db'],host='127.0.0.1',port=5432)
    target=STAGE/'0028-responder-loopback-apply.PRIVATE.json'
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f: json.dump(config,f)
    return target

def run_java(mode,out,config,approval=None):
    require(not out.exists(),'Output directory already exists; inspect prior apply before retry')
    out.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    mounts=['--mount',f'type=bind,src={STAGE},dst=/0028-input,readonly',
            '--mount',f'type=bind,src={out.parent},dst=/0028-output']
    cmd=['docker','run','--rm','--network','container:diaries-postgres',
         '--volumes-from','diaries-responder:ro','--read-only',
         '--tmpfs','/tmp:rw,nosuid,nodev,size=32m',*mounts,
         '--mount',f'type=bind,src={config},dst=/0028-config.json,readonly',
         '--entrypoint','java',IMAGE,'-cp','/0028-input/diaries-0028-reviewed-migration-fat.jar',MAIN,
         '--mode',mode,'--manifest','/0028-input/reviewed','--config','/0028-config.json',
         '--plan','/0028-input/result/dry-run/result/0028-reviewed-dry-run-plan.json',
         '--output',f'/0028-output/{out.name}']
    if approval:
        cmd.extend(['--approval',f'/0028-input/{approval.name}','--permit-production-apply','YES'])
    print(execute(cmd))
    return json.loads((out/'summary.json').read_text())

def main():
    require(len(sys.argv) in (3,5),'Usage: python3 - apply JAR_SHA BACKUP_RECEIPT_SHA REHEARSAL_RECEIPT_SHA; or postflight JAR_SHA')
    mode=sys.argv[1]
    require(mode in ('apply','postflight'),'Unknown action')
    isolation()
    plan=common(sys.argv[2])
    config=private_config()
    try:
        if mode=='apply':
            require(len(sys.argv)==5,'Two accepted receipt digests required')
            backup,rehearsal=sys.argv[3:]
            require(all(re.fullmatch('[0-9a-f]{64}',x) for x in (backup,rehearsal)),
                    'Verified backup and rehearsal SHA-256 receipts required')
            require(BACKUP_EVIDENCE.is_file() and REHEARSAL_EVIDENCE.is_file(),
                    'Accepted recovery/rehearsal evidence files missing')
            require(sha(BACKUP_EVIDENCE)==backup and sha(REHEARSAL_EVIDENCE)==rehearsal,
                    'Evidence digest mismatch')
            backup_text=BACKUP_EVIDENCE.read_text(encoding='utf-8')
            rehearsal_text=REHEARSAL_EVIDENCE.read_text(encoding='utf-8')
            require('20261124-173416Z' in backup_text and '20261124-172811Z' in backup_text,
                    'Expected protected snapshot/backup identities absent from recovery evidence')
            require('20261123T185712Z-isolated-db-rehearsal' in rehearsal_text and
                    ('71/71' in rehearsal_text or '71 conversions' in rehearsal_text),
                    'Accepted restored-DB rehearsal identity/results absent')
            require(db("select to_regclass('public.migration0028_source') is not null")== 'f',
                    'Journal already exists: inspect journal, do not automatically retry')
            runroot=STAGE/'production-apply'
            require(not runroot.exists(),'Previous apply artefacts exist: inspect before any retry')
            runroot.mkdir(mode=0o700)
            approval=STAGE/'0028-production-approval.PRIVATE.json'
            require(not approval.exists(),'Approval already exists: refuse overwrite')
            data={'schema':'0028-apply-approval-v1','plan_sha256':EXPECTED_PLAN,
                  'input_identity':plan['inputIdentity'], 'database_identity':plan['databaseIdentity'],
                  'files_root':plan['filesRoot'],'scope':'PRODUCTION','writer_state':'OFFLINE_WRITERS_STOPPED',
                  'approved_by':'Diaries owner (explicit approval in ChatGPT conversation, 2026-11-24)',
                  'approved_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  'verified_backup_receipt_sha256':backup,'accepted_rehearsal_receipt_sha256':rehearsal}
            fd=os.open(approval,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            with os.fdopen(fd,'w') as f: json.dump(data,f,indent=2);f.write('\n')
            print('EVIDENCE: backup report SHA-256:',backup,flush=True)
            print('EVIDENCE: rehearsal report SHA-256:',rehearsal,flush=True)
            # A distinct, reviewed DDL operation; no migration data writes until DDL completes.
            print('Installing reviewed migration0028 journal schema ...')
            execute(['docker','exec','-i','diaries-postgres','sh','-c',
                     'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'],
                    input=JOURNAL_SQL)
            print('Journal installed. Beginning the authorised production apply ...')
            summary=run_java('apply',runroot/'result',config,approval)
            require(summary.get('result')=='APPLY_COMMITTED_DATABASE_PASS_MQTT_REPLAY_PENDING',
                    'Apply result unexpected; keep writer isolation')
            print('PASS: production database migration applied; MQTT replay still required')
        else:
            require(len(sys.argv)==3,'Unexpected postflight arguments')
            out=STAGE/'production-postflight'/'result'
            summary=run_java('postflight',out,config)
            require(summary.get('result')=='POSTFLIGHT_DATABASE_PASS_MQTT_NOT_CHECKED',
                    'Postflight result unexpected')
            print('PASS: database postflight, MQTT replay not checked')
    finally:
        config.unlink(missing_ok=True)

if __name__=='__main__':
    try: main()
    except Exception as exc:
        print('FAIL:',exc,file=sys.stderr)
        print('KEEP PRODUCTION ISOLATED. Never automatically rerun a partially committed apply.',file=sys.stderr)
        sys.exit(2)
