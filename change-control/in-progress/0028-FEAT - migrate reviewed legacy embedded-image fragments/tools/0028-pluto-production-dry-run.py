#!/usr/bin/env python3
"""One-shot 0028 production CLI validate-manifest + dry-run, no journal/apply/MQTT.

Executed on pluto through `ssh pluto 'python3 - preflight|probe|run SHA256' < this-file`.
Must be preceded by accepted 0028 writer isolation and independent mars+backup
rollback holds. Stage private files to /run/diaries-0028-production-migration-input.
No application image/service deploy. No persistent remote evidence store.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

PROJECT = Path('/home/richard/projects/diaries')
STAGE = Path('/run/diaries-0028-production-migration-input')
JAR = STAGE / 'diaries-0028-reviewed-migration-fat.jar'
MANIFEST = STAGE / 'reviewed'
CONFIG = PROJECT / 'config/responder/responder.json'
IMAGE_EXPECTED = 'rsmaxwell/diaries-responder:0.0.9-build-86'
JAVA_MAIN = 'com.rsmaxwell.diaries.responder.migration.migration0028.Migration0028ReviewedFragments'
HBA_MARK = b'# 0028-MAINTENANCE-ISOLATION'


def fail(msg):
    raise RuntimeError(msg)


def execute(argv, *, check=True):
    proc=subprocess.run(argv,stdout=subprocess.PIPE,stderr=subprocess.PIPE,check=False)
    if check and proc.returncode:
        fail(f'{argv[0]} returned {proc.returncode}: {proc.stderr.decode(errors="replace")[-650:]}')
    return proc


def text(argv): return execute(argv).stdout.decode().strip()


def db(sql):
    return text(['docker','exec','diaries-postgres','sh','-c',
                 'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"',
                 'sh', sql])


def digest(path):
    h=hashlib.sha256()
    with path.open('rb') as file:
        for block in iter(lambda: file.read(1048576),b''): h.update(block)
    return h.hexdigest()


def require_isolated():
    if text(['systemctl','show','diaries-complete-backup-publish.timer','--property=ActiveState','--value']) != 'inactive':
        fail('Backup timer is not stopped')
    if text(['systemctl','show','diaries-complete-backup-publish.service','--property=ActiveState','--value']) != 'inactive':
        fail('Backup publisher is active')
    for name,needed in [('diaries-responder','false'),('diaries-postgres','true'),('diaries-mosquitto','true')]:
        if text(['docker','inspect','-f','{{.State.Running}}',name]) != needed:
            fail('Unexpected state for '+name)
    hba=db('show hba_file')
    data=execute(['docker','exec','-u','0','diaries-postgres','cat',hba]).stdout
    if (HBA_MARK not in data or b'host all all 0.0.0.0/0 reject' not in data or
            b'host all all ::/0 reject' not in data):
        fail('Temporary 0028 PostgreSQL HBA isolation is absent/incomplete')
    count=int(db("select count(*) from pg_stat_activity where backend_type='client backend' and pid<>pg_backend_pid()"))
    if count:
        fail(f'Unexpected PostgreSQL session(s) during dry-run gate: {count}')


def validate_stage(expected_hash):
    if not re.fullmatch(r'[0-9a-f]{64}',expected_hash):
        fail('Expected pinned JAR SHA-256 (64 lowercase hex) required')
    if not STAGE.is_dir() or STAGE.is_symlink():
        fail('Missing approved transient stage')
    if STAGE.stat().st_uid != os.getuid() or STAGE.stat().st_mode & 0o077:
        fail('Transient staging directory is not private')
    if not JAR.is_file() or JAR.is_symlink() or digest(JAR) != expected_hash:
        fail('Pinned JAR missing or SHA-256 mismatch')
    required={
        '0028-dispositions.csv','0028-image-decisions.csv',
        '0028-v2-preservation-decisions.PRIVATE.csv',
        'PREPARATION-RESULT.json','SHA256SUMS.txt'
    }
    if not MANIFEST.is_dir() or MANIFEST.is_symlink() or not required.issubset({x.name for x in MANIFEST.iterdir()}):
        fail('Prepared private manifest incomplete')
    for file in MANIFEST.iterdir():
        if file.is_symlink() or not file.is_file(): fail('Manifest contains unsafe entry')
    rows=json.loads((MANIFEST/'PREPARATION-RESULT.json').read_text())
    expected={'CONVERT_TO_IMAGE':71,'DEFER':1,'links_preserved':30,'marquees_preserved':22}
    if any(rows.get('counts',{}).get(k)!=v for k,v in expected.items()) or rows.get('productionApplyAllowed') is not False:
        fail('Prepared 71+1 manifest scope or production authority unexpected')
    # Re-hash files in the source's SHA256SUMS; excludes arbitrary extra paths.
    for line in (MANIFEST/'SHA256SUMS.txt').read_text().splitlines():
        result=re.fullmatch(r'([0-9a-f]{64})  ([A-Za-z0-9._-]+)',line)
        if not result or result.group(2) not in required or digest(MANIFEST/result.group(2)) != result.group(1):
            fail('Prepared manifest checksum mismatch')




def verify_files_mount_readonly(image):
    # Observe actual mounted filesystem flags from a disposable, network-disabled
    # container; checking Docker CLI '--volumes-from :ro' alone is insufficient.
    shell=("test -d /data/files && test -r /data/files && "
           "awk '$2==\"/data/files\" && $4 ~ /(^|,)ro(,|$)/ {ok=1} "
           "END {exit !ok}' /proc/mounts")
    p=execute(['docker','run','--rm','--network','none',
               '--volumes-from','diaries-responder:ro','--read-only',
               '--entrypoint','sh',image,'-c',shell],check=False)
    if p.returncode:
        fail('Files volume absent, unreadable, or NOT mounted read-only in one-shot container')

def runner(image, output_dir, mode, cfg):
    output_dir.mkdir(mode=0o700, parents=True)
    docker=['docker','run','--rm','--network','container:diaries-postgres',
        '--volumes-from','diaries-responder:ro','--read-only',
        '--tmpfs','/tmp:rw,nosuid,nodev,size=32m',
        '--mount',f'type=bind,src={STAGE},dst=/0028-input,readonly',
        '--mount',f'type=bind,src={output_dir},dst=/0028-output',
        '--mount',f'type=bind,src={cfg},dst=/0028-config.json,readonly',
        '--entrypoint','java',image,'-cp','/0028-input/diaries-0028-reviewed-migration-fat.jar',
        JAVA_MAIN,'--mode',mode,'--manifest','/0028-input/reviewed',
        '--output','/0028-output/result']
    if mode=='dry-run': docker.extend(['--config','/0028-config.json'])
    p=execute(docker,check=False)
    if p.returncode:
        fail(f'Java 0028 {mode} failed (exit={p.returncode}): {p.stderr.decode(errors="replace")[-850:]}')
    return p.stdout.decode(errors='replace')


def action(mode, expected_hash):
    if mode != 'preflight':
        require_isolated()
    validate_stage(expected_hash)
    image=text(['docker','inspect','-f','{{.Config.Image}}','diaries-responder'])
    if image != IMAGE_EXPECTED: fail('Responder image unexpectedly changed')
    java=execute(['docker','run','--rm','--network','none','--entrypoint','java',image,'-version'],check=False)
    if java.returncode or not re.search(r'\b25(?:\.|\b)',java.stderr.decode(errors='replace')):
        fail('Java 25 one-shot image compatibility not established')
    if not CONFIG.is_file(): fail('Original deployed responder config missing')
    original=json.loads(CONFIG.read_text())
    if not isinstance(original.get('db'),dict) or not isinstance(original.get('diaries'),dict):
        fail('Deployed responder configuration unexpected')
    if original['db'].get('database') is None or original['diaries'].get('files')!='files':
        fail('Unexpected production DB or Files selector')
    if not (original['diaries'].get('root') == '/data'):
        fail('Unexpected production Files-root config; do not infer mount layout')
    verify_files_mount_readonly(image)
    if mode=='preflight':
        # Offline CLI test before any production outage: network disabled; no DB.
        out=STAGE/'offline-preflight'
        if out.exists(): fail('Offline preflight output already exists; refuse overwrite')
        out.mkdir(mode=0o700)
        cmd=['docker','run','--rm','--network','none',
             '--volumes-from','diaries-responder:ro','--read-only',
             '--tmpfs','/tmp:rw,nosuid,nodev,size=32m',
             '--mount',f'type=bind,src={STAGE},dst=/0028-input,readonly',
             '--mount',f'type=bind,src={out},dst=/0028-output',
             '--entrypoint','java',image,'-cp',
             '/0028-input/diaries-0028-reviewed-migration-fat.jar',JAVA_MAIN,
             '--mode','validate-manifest','--manifest','/0028-input/reviewed',
             '--output','/0028-output/validation']
        outcome=execute(cmd,check=False)
        if outcome.returncode:
            fail('Offline validated-manifest CLI failed: '+outcome.stderr.decode(errors='replace')[-600:])
        receipt=json.loads((out/'validation'/'summary.json').read_text())
        if receipt.get('result')!='PASS_OFFLINE' or receipt.get('writes') is not False or receipt.get('count')!=72:
            fail('Offline CLI validation scope/result mismatch')
        print('PASS: one-shot Java 25 + pinned JAR + complete 72-row manifest')
        print('PASS: Docker read-only responder volumes; network disabled for preflight')
        print('NO PostgreSQL DB connection, service outage or migration apply')
        return
    if mode=='probe':
        print('PASS: writer-stopped contract and pinned JAR+prepared manifest verified')
        print('PASS: one-shot Java 25 image is locally available')
        print('PENDING: protected rollback point verification on both backup hosts')
        print('NO DATABASE WRITES OR MIGRATION APPLY')
        return
    if mode!='run': fail('Unknown action')
    config=dict(original)
    config['db']=dict(original['db'],host='127.0.0.1',port=5432)
    cfg=STAGE/'0028-responder-loopback.PRIVATE.json'
    if cfg.exists(): fail('Temporary config already exists; do not overwrite')
    fd=os.open(cfg,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    try:
        with os.fdopen(fd,'w',encoding='utf-8') as f:
            json.dump(config,f)
            f.write('\n')
        # Dry-run results are temporary until copied to private Windows feature evidence.
        out=STAGE/'result'
        if out.exists(): fail('Existing dry-run output; refusing overwrite')
        print(runner(image,out/'validate','validate-manifest',cfg))
        print(runner(image,out/'dry-run','dry-run',cfg))
        summary=json.loads((out/'dry-run'/'result'/'summary.json').read_text())
        if (summary.get('result')!='DRY_RUN_PASS' or summary.get('reviewedConversions')!=71 or
                summary.get('deferredFragments')!=[1564] or summary.get('writes') is not False):
            fail('Production dry-run summary is not the exact approved no-write scope')
        if not (out/'dry-run'/'result'/'0028-reviewed-dry-run-plan.json').is_file():
            fail('Production dry-run plan missing')
        print('PASS: live production reviewed 71 conversions, defer 1564; NO database writes requested')
        print('PRIVATE OUTPUT ON PLUTO (TRANSIENT):',out)
        print('COPY TO WINDOWS PRIVATE FEATURE EVIDENCE BEFORE CLEANUP; DO NOT COMMIT')
        print('PRODUCTION APPLY NOT AUTHORISED')
    finally:
        cfg.unlink(missing_ok=True)

if __name__=='__main__':
    try:
        if len(sys.argv)!=3 or sys.argv[1] not in ('preflight','probe','run'):
            fail('Usage: python3 - {preflight|probe|run} <pinned-fat-JAR-sha256>')
        action(sys.argv[1],sys.argv[2])
    except Exception as exc:
        print('FAIL:',exc,file=sys.stderr)
        print('No apply invoked. Keep writer isolation until operator decides reopen.',file=sys.stderr)
        sys.exit(2)
