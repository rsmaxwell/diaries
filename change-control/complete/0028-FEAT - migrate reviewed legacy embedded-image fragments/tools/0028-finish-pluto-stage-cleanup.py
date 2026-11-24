#!/usr/bin/env python3
"""Resume ONLY 0028 transient stage cleanup from an already verified local archive.

Run in Windows Cygwin from Diaries parent repository root.
No migration/database/snapshot operations; fail closed on any identity discrepancy.
"""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tarfile

FEATURE=Path('change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments')
PRIVATE=FEATURE/'evidence/Step 3/private'
STAGE='diaries-0028-production-migration-input'
ROOT='/run/'+STAGE
EXPECTED_RESULT={
 'production-apply/result/summary.json':'APPLY_COMMITTED_DATABASE_PASS_MQTT_REPLAY_PENDING',
 'production-postflight/result/summary.json':'POSTFLIGHT_DATABASE_PASS_MQTT_NOT_CHECKED',
}
JAR_SHA='9a2910515bbe0929c93c0557f91c2b27b8323bb9da61fb2573a0ff9b20c209a1'

def digest(f):
 h=hashlib.sha256()
 with open(f,'rb') as src:
  for block in iter(lambda:src.read(1024*1024),b''):h.update(block)
 return h.hexdigest()

def fail(msg):
 raise RuntimeError(msg)

def main():
 if not (FEATURE/'IMPLEMENTATION-STEPS.md').is_file():fail('Run from Diaries parent repository root')
 choices=[]
 for receipt_path in PRIVATE.glob('*-pluto-production-stage-archive/ARCHIVE-AND-CLEANUP-RECEIPT.PRIVATE.json'):
  try:
   rec=json.loads(receipt_path.read_text())
   arc=receipt_path.parent/rec['archive']
   if rec.get('remote')==ROOT and rec.get('verification','').startswith('PASS:') and arc.is_file() and digest(arc)==rec['archiveSha256']:
    choices.append((receipt_path,arc,rec))
  except (KeyError,ValueError,OSError):continue
 if len(choices)!=1:fail(f'Expected exactly one verified archive; found {len(choices)}. No cleanup.')
 receipt_path,arc,rec=choices[0]
 if rec.get('cleanup','').startswith('PASS:'):fail('Cleanup already recorded as completed; no repeat')
 manifest_path=receipt_path.parent/'REMOTE-MANIFEST.PRIVATE.json'
 if not manifest_path.is_file():fail('Missing captured remote manifest')
 manifest=json.loads(manifest_path.read_text())
 if manifest.get('root')!=ROOT:fail('Unexpected stage root in manifest')
 files=manifest['files']
 if files.get('diaries-0028-reviewed-migration-fat.jar',{}).get('sha256')!=JAR_SHA:fail('Pinned JAR mismatch')
 seen={}
 with tarfile.open(arc,'r:') as tar:
  for member in tar:
   if member.name in (STAGE,STAGE+'/'):continue
   if not member.name.startswith(STAGE+'/'):fail('Unexpected archive path')
   rel=member.name[len(STAGE)+1:]
   if not rel or any(p in ('.','..') for p in Path(rel).parts):fail('Unsafe path')
   if member.isdir():continue
   if not member.isfile() or rel in seen or rel not in files:fail('Unexpected archive entry')
   h=hashlib.sha256(); size=0
   source=tar.extractfile(member)
   for chunk in iter(lambda:source.read(1024*1024),b''):
    h.update(chunk);size+=len(chunk)
   seen[rel]={'sha256':h.hexdigest(),'size':size}
  if seen!=files:fail('Archive differs from captured remote manifest')
  for path,expected in EXPECTED_RESULT.items():
   member=tar.extractfile(STAGE+'/'+path)
   if json.load(member).get('result')!=expected:fail('Completed migration result mismatch: '+path)
 if len(files)!=rec['fileCount']:fail('Receipt file count mismatch')
 print('PASS: previously archived',len(files),'files verified again',flush=True)
 # Remote code is sent via standard input; only the fixed root is eligible for deletion.
 remote=r'''import hashlib,json,os,shutil,stat,sys
root='/run/diaries-0028-production-migration-input'
expected=json.loads(sys.argv[1])
if os.path.islink(root) or not os.path.isdir(root):sys.exit('FAIL: stage absent or symlink')
if os.path.realpath(root)!=root:sys.exit('FAIL: unexpected root')
files={}
for base,dirs,names in os.walk(root,followlinks=False):
 for d in dirs:
  p=os.path.join(base,d)
  if os.path.islink(p):sys.exit('FAIL: symlink directory')
 for n in names:
  p=os.path.join(base,n)
  if not stat.S_ISREG(os.lstat(p).st_mode):sys.exit('FAIL: special file')
  h=hashlib.sha256()
  with open(p,'rb') as f:
   for b in iter(lambda:f.read(1048576),b''):h.update(b)
  files[os.path.relpath(p,root).replace(os.sep,'/')]={'sha256':h.hexdigest(),'size':os.path.getsize(p)}
if any(path not in expected or expected[path]!=value for path,value in files.items()):
 sys.exit('FAIL: residual stage differs from verified archive; NOT deleted')
print('PASS: verified',len(files),'remaining files against complete archive')
shutil.rmtree(root)
if os.path.lexists(root):sys.exit('FAIL: stage still present')
print('PASS: removed exact verified 0028 /run stage')
'''
 # Supply expected manifest as a positional argument, safely quoted via shlex.quote.
 import shlex
 cmd='sudo -n python3 - '+shlex.quote(json.dumps(files,separators=(',',':')))
 proc=subprocess.run(['ssh','pluto',cmd],input=remote,text=True,capture_output=True)
 if proc.stdout:print(proc.stdout.strip(),flush=True)
 if proc.returncode:fail('Remote cleanup failed; inspect residual stage: '+proc.stderr.strip()[-1200:])
 rec['cleanup']='PASS: exact archived stage removed from pluto /run'
 receipt_path.write_text(json.dumps(rec,indent=2)+'\n')
 print('PASS: receipt updated:',receipt_path,flush=True)
 print('PASS: production services and backup snapshots untouched',flush=True)

if __name__=='__main__':
 try:main()
 except Exception as e:
  print('FAIL:',e,file=sys.stderr)
  sys.exit(1)
