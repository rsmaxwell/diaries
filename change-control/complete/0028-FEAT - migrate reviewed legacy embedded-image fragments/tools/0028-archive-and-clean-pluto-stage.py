#!/usr/bin/env python3
"""Windows Cygwin: preserve completed 0028 pluto runtime stage, verify, then remove it.

Run from Diaries parent repository root. Creates ONLY ignored private evidence locally.
Never operates on database, Docker containers, backup datasets, or other /run trees.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile

FEATURE = Path('change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments')
DEST_ROOT = FEATURE / 'evidence/Step 3/private'
STAGE_NAME = 'diaries-0028-production-migration-input'
REMOTE_STAGE = '/run/' + STAGE_NAME
EXPECTED = {
    'production-apply/result/summary.json': 'APPLY_COMMITTED_DATABASE_PASS_MQTT_REPLAY_PENDING',
    'production-postflight/result/summary.json': 'POSTFLIGHT_DATABASE_PASS_MQTT_NOT_CHECKED',
}
PINNED_JAR = '9a2910515bbe0929c93c0557f91c2b27b8323bb9da61fb2573a0ff9b20c209a1'
REMOTE_MANIFEST = r'''
import hashlib,json,os,stat,sys
root='/run/diaries-0028-production-migration-input'
if not os.path.isdir(root) or os.path.islink(root): sys.exit('FAIL: 0028 stage missing or symlink')
if os.stat(root).st_uid != os.getuid(): sys.exit('FAIL: stage is not owned by SSH user')
files={}
for base,dirs,names in os.walk(root,followlinks=False):
    for d in dirs:
        p=os.path.join(base,d)
        if os.path.islink(p): sys.exit('FAIL: directory symlink in stage')
    for name in names:
        p=os.path.join(base,name); mode=os.lstat(p).st_mode
        if not stat.S_ISREG(mode): sys.exit('FAIL: non-regular file in stage: '+name)
        h=hashlib.sha256()
        with open(p,'rb') as f:
            for chunk in iter(lambda:f.read(1048576),b''):h.update(chunk)
        files[os.path.relpath(p,root).replace(os.sep,'/')]={'sha256':h.hexdigest(),'size':os.stat(p).st_size}
print(json.dumps({'root':root,'files':files},sort_keys=True))
'''
REMOTE_REMOVE = r'''
import hashlib,json,os,shutil,sys
root='/run/diaries-0028-production-migration-input'
expected=json.loads(EXPECTED_JSON_LITERAL)
if os.path.islink(root) or not os.path.isdir(root) or os.stat(root).st_uid!=os.getuid():
    sys.exit('FAIL: stage absent, unsafe, or owner changed; nothing deleted')
files={}
for base,dirs,names in os.walk(root,followlinks=False):
    for d in dirs:
        if os.path.islink(os.path.join(base,d)):sys.exit('FAIL: symlink; nothing deleted')
    for name in names:
        p=os.path.join(base,name)
        if not os.path.isfile(p) or os.path.islink(p):sys.exit('FAIL: special file; nothing deleted')
        h=hashlib.sha256()
        with open(p,'rb') as f:
            for block in iter(lambda:f.read(1048576),b''):h.update(block)
        files[os.path.relpath(p,root).replace(os.sep,'/')]={'sha256':h.hexdigest(),'size':os.path.getsize(p)}
if files!=expected:sys.exit('FAIL: stage changed since archive; nothing deleted')
shutil.rmtree(root)
print('PASS: removed only '+root)
'''


def remote_python(code, *args):
    proc = subprocess.run(['ssh','pluto','python3','-',*args],input=code,text=True,
                          capture_output=True)
    if proc.returncode:
        raise RuntimeError('Remote check failed: '+proc.stderr[-1200:])
    return proc.stdout.strip()


def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()


def main():
    if len(sys.argv)!=1: raise RuntimeError('No arguments required')
    if not (FEATURE/'IMPLEMENTATION-STEPS.md').is_file():
        raise RuntimeError('Run from the Diaries parent repository root')
    manifest=json.loads(remote_python(REMOTE_MANIFEST))
    files=manifest['files']
    for rel,result in EXPECTED.items():
        if rel not in files: raise RuntimeError('Missing completed '+rel+'; no cleanup')
    if 'diaries-0028-reviewed-migration-fat.jar' not in files or files['diaries-0028-reviewed-migration-fat.jar']['sha256'] != PINNED_JAR:
        raise RuntimeError('Pinned JAR absent/mismatch; no cleanup')
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    dest=DEST_ROOT/(stamp+'-pluto-production-stage-archive')
    dest.mkdir(parents=True,exist_ok=False,mode=0o700)
    archive=dest/'pluto-0028-runtime.tar'
    print('=== Archive exact production stage to ignored private feature evidence ===',flush=True)
    with archive.open('wb') as out:
        proc=subprocess.run(['ssh','pluto','tar','-C','/run','-cf','-',STAGE_NAME],stdout=out,stderr=subprocess.PIPE)
    if proc.returncode:
        raise RuntimeError('SSH/tar failed; remote stage untouched: '+proc.stderr.decode(errors='replace')[-1000:])
    print('=== Verify archive integrity and ALL staged file hashes ===',flush=True)
    seen={}
    with tarfile.open(archive,'r:') as t:
        for member in t:
            name=member.name
            if name in (STAGE_NAME,STAGE_NAME+'/'):continue
            prefix=STAGE_NAME+'/'
            if not name.startswith(prefix):raise RuntimeError('Unexpected archive path; remote untouched')
            rel=name[len(prefix):]
            parts=Path(rel).parts
            if not rel or any(x in ('..','.') for x in parts) or Path(rel).is_absolute():
                raise RuntimeError('Unsafe archive path; remote untouched')
            if member.isdir():continue
            if not member.isfile() or rel not in files or rel in seen:
                raise RuntimeError('Unexpected archive entry; remote untouched: '+rel)
            stream=t.extractfile(member)
            h=hashlib.sha256(); size=0
            for chunk in iter(lambda:stream.read(1048576),b''):
                h.update(chunk);size+=len(chunk)
            item={'sha256':h.hexdigest(),'size':size}
            if item!=files[rel]: raise RuntimeError('Archive checksum mismatch: '+rel)
            seen[rel]=item
    if seen!=files:raise RuntimeError('Archive missing staged files; remote untouched')
    # Validate actual CLI result payloads without exposing private content on console.
    with tarfile.open(archive,'r:') as t:
        for rel,required in EXPECTED.items():
            entry=t.extractfile(STAGE_NAME+'/'+rel)
            result=json.load(entry)
            if result.get('result')!=required:
                raise RuntimeError('Unexpected '+rel+' result; remote untouched')
    (dest/'REMOTE-MANIFEST.PRIVATE.json').write_text(json.dumps(manifest,indent=2)+'\n')
    receipt={'capturedAt':datetime.now(timezone.utc).isoformat(),
             'remote':REMOTE_STAGE,'archive':archive.name,'archiveSha256':sha(archive),
             'fileCount':len(seen),'bytes':sum(x['size'] for x in seen.values()),
             'apply':EXPECTED['production-apply/result/summary.json'],
             'postflight':EXPECTED['production-postflight/result/summary.json'],
             'verification':'PASS: exact remote manifest and each archive member SHA-256 match',
             'cleanup':'PENDING'}
    receipt_path=dest/'ARCHIVE-AND-CLEANUP-RECEIPT.PRIVATE.json'
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print(f'PASS: {len(seen)} files archived and SHA-256 verified; archive SHA-256 {receipt["archiveSha256"]}',flush=True)
    print('=== Remove ONLY unchanged /run 0028 stage on pluto ===',flush=True)
    print(remote_python(REMOTE_REMOVE.replace('EXPECTED_JSON_LITERAL',repr(json.dumps(files,separators=(',',':'))))),flush=True)
    receipt['cleanup']='PASS: exact archived stage removed from pluto /run'
    receipt_path.write_text(json.dumps(receipt,indent=2)+'\n')
    print('PASS: evidence saved to '+str(dest),flush=True)
    print('PASS: production database, services, retained MQTT and backup snapshots untouched',flush=True)


if __name__=='__main__':
    try:main()
    except Exception as exc:
        print('FAIL:',str(exc),file=sys.stderr)
        print('No automatic retry. Any unverified remote stage remains in place.',file=sys.stderr)
        sys.exit(1)
