#!/usr/bin/env python3
"""Disposable real schema-2 integration; no network, Btrfs or production writes."""
from pathlib import Path
import tempfile,json,hashlib,subprocess,sys,os,argparse,shutil

parser=argparse.ArgumentParser()
parser.add_argument('--playbooks-root',type=Path,default=Path('/home/richard/ansible-controller/playbooks'))
args=parser.parse_args()
root=args.playbooks_root.resolve()
verifier=root/'roles/diaries/files/sync/scripts/complete-dataset-manifest.py'
history=root/'roles/snapshots/files/diaries-backup-history.py'
assert verifier.is_file() and history.is_file(), 'Missing Playbooks files'
def sha(b): return hashlib.sha256(b).hexdigest()
with tempfile.TemporaryDirectory() as tmp:
  d=Path(tmp); snap=d/'received'/'@data'/'20261116-150008Z'; snap.mkdir(parents=True)
  bkid='20261116-003112Z'; generation=snap/'backup/pluto/.diaries-backup-generations'/bkid; generation.mkdir(parents=True)
  (generation/'database').mkdir(); (generation/'verification').mkdir(); (generation/'files').mkdir()
  dump=b'PGDMPtesting\n'; sql=b'CREATE TABLE t (id int);\n'; doc=b'hello\n'
  for path,data in [('database/diaries.dump',dump),('database/diaries.sql',sql),('files/test.txt',doc)]: (generation/path).write_bytes(data)
  (generation/'verification/database.sha256').write_text(f'{sha(dump)}  database/diaries.dump\n{sha(sql)}  database/diaries.sql\n')
  (generation/'verification/files.sha256').write_text(f'{sha(doc)}  files/test.txt\n')
  (generation/'verification/inventory.json').write_text(json.dumps({'schemaVersion':1,'root':'files','fileCount':1,'totalBytes':len(doc),'files':[{'path':'files/test.txt','sizeBytes':len(doc),'sha256':sha(doc)}]},indent=2)+'\n')
  cmd=[sys.executable,str(verifier),'write','--backup-dir',str(generation),'--logical-dataset','production','--launch-mode','test-fixture','--database-storage-identity','test','--database-name','diaries','--files-selector','fixture','--files-root','/fixture/files','--application-identity-json','{"component":"test"}','--writer-method','offline','--writer','test-writer','--writer-evidence','fixture','--image-row-count','0','--catalogued-file-count','1','--staging-disposition','empty','--staging-entry-count','0','--staging-note','fixture','--started-at','2026-11-16T00:00:00Z','--completed-at','2026-11-16T01:00:00Z']
  p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0, p.stderr
  (snap/'backup/pluto/diaries-backup').symlink_to('.diaries-backup-generations/'+bkid)
  marker=snap/'backup/.diaries-snapshot-verified.json'; marker.write_text(json.dumps({'state':'verified-published','snapshotEligible':True,'datasetRelativePath':'backup/pluto/diaries-backup','backupId':bkid,'logicalDataset':'production','manifestSha256':sha((generation/'dataset-manifest.json').read_bytes())}))
  cfg=d/'manager.json'; cfg.write_text(json.dumps({'mode':'receiver','snapshot_root':str(d/'received'),'sources':[{'name':'@data','snapshot_directory':str(d/'received'/'@data')}], 'verification':{'required':False},'diaries_history':{'enabled':True,'source_name':'@data','dataset_relative_path':'backup/pluto/diaries-backup','marker_relative_path':'backup/.diaries-snapshot-verified.json','manifest_tool':str(verifier)}}))
  cmd=[sys.executable,str(history),'--config',str(cfg),'verify',bkid]
  p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==0, p.stderr
  (generation/'files/test.txt').write_text('tampered!')
  p=subprocess.run(cmd,capture_output=True,text=True); assert p.returncode==2, p.stderr
  assert 'Files inventory' in p.stderr, p.stderr

  # Test the real published layout observed on backup: diaries-backup is a
  # directory, not a symlink resolving to a backupId-named generation.
  (generation/'files/test.txt').write_bytes(doc)
  fixed=snap/'backup/pluto/diaries-backup'
  fixed.unlink()
  shutil.copytree(generation, fixed)
  p=subprocess.run(cmd,capture_output=True,text=True)
  assert p.returncode==0, 'fixed-root verification failed: '+p.stderr
  assert f'backupId={bkid}' in p.stdout, p.stdout
  (fixed/'files/test.txt').write_text('tampered!')
  p=subprocess.run(cmd,capture_output=True,text=True)
  assert p.returncode==2, p.stderr
  assert 'Files inventory' in p.stderr, p.stderr

  # Re-run fixed-root verification with source mode, too. The shared history
  # must continue to work on mars without enabling receiver-only config.
  (fixed/'files/test.txt').write_bytes(doc)
  source_cfg=d/'source-manager.json'
  source_cfg.write_text(json.dumps({'mode':'source','snapshot_root':str(d/'received'),
    'sources':[{'name':'@data','path':'/tmp/source-not-used'}],
    'verification':{'required':True,'source_name':'@data',
      'dataset_relative_path':'backup/pluto/diaries-backup',
      'marker_relative_path':'backup/.diaries-snapshot-verified.json',
      'manifest_tool':str(verifier)}}))
  source_cmd=[sys.executable,str(history),'--config',str(source_cfg),'verify',bkid]
  p=subprocess.run(source_cmd,capture_output=True,text=True)
  assert p.returncode==0, 'source fixed-root verification failed: '+p.stderr
  print('PASS: receiver/source fixed-root and generation verification plus tamper detection')
