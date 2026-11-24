import hashlib
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from step3_retained_dataset_check import (inspect_dataset, selected_backup,
                                          summarize, canonical_relative)

ID = '20261124-003112Z'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def make_dataset(root):
    def write(rel,data):
        dst=root/rel; dst.parent.mkdir(parents=True, exist_ok=True);dst.write_bytes(data);return data
    custom=write('database/diaries.dump',b'PGDMP-example-content')
    sql=write('database/diaries.sql',b'SELECT 1;\n')
    sample1=write('files/a/image.png',b'image test')
    sample2=write('files/b/test.jpg',b'longer photo mock')
    files=[{'path':'files/a/image.png','sizeBytes':len(sample1),'sha256':digest(sample1)},
           {'path':'files/b/test.jpg','sizeBytes':len(sample2),'sha256':digest(sample2)}]
    dbhashes=write('verification/database.sha256',
                   ('{}  database/diaries.dump\n{}  database/diaries.sql\n'.format(digest(custom),digest(sql))).encode())
    filehashes=write('verification/files.sha256',
                     ('\n'.join('{}  {}'.format(f['sha256'],f['path']) for f in files)+'\n').encode())
    inv=write('verification/inventory.json',json.dumps({'schemaVersion':1,'root':'files','fileCount':2,
       'totalBytes':len(sample1)+len(sample2),'files':files}).encode())
    manifest={
       'schemaVersion':2,'backupType':'complete-dataset','completeDatasetBackup':True,'status':'complete',
       'backupId':ID,'logicalDataset':'production',
       'database':{'customDump':{'path':'database/diaries.dump','sizeBytes':len(custom),'sha256':digest(custom)},
                    'sqlDump':{'path':'database/diaries.sql','sizeBytes':len(sql),'sha256':digest(sql)}},
       'files':{'snapshot':{'path':'files','fileCount':2,'totalBytes':len(sample1)+len(sample2),
                             'verification':'verified','inventorySha256':digest(inv),
                             'hashListSha256':digest(filehashes)}}}
    blob=write('dataset-manifest.json',json.dumps(manifest,sort_keys=True).encode())
    return digest(blob),manifest

def status(backup_id=ID,health='healthy'):
 return {'health':health,'component':'diaries','conflictedBackups':0,
         'latest':{'backupId':backup_id,'logicalDataset':'production'}}

class RetainedDatasetTest(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name)/ID
  self.root.mkdir();self.hash,self.manifest=make_dataset(self.root)
 def test_metadata_component_pass_without_restore_claim(self):
  r=inspect_dataset(self.root, ID, self.hash)
  self.assertEqual(r['files']['fileCount'],2)
  self.assertEqual(r['files']['sampleFilesPresentWithExpectedSize'],2)
  self.assertFalse(r['restoreVerified'])
  self.assertFalse(r['fullFileContentVerified'])
  self.assertFalse(r['productionApplyAuthorised'])
 def test_changed_manifest_bytes_rejected(self):
  with self.assertRaisesRegex(ValueError,'manifest hash mismatch'):
   inspect_dataset(self.root,ID,'0'*64)
 def test_missing_database_dump_rejected(self):
  (self.root/'database/diaries.dump').unlink()
  with self.assertRaises(OSError):inspect_dataset(self.root,ID,self.hash)
 def test_changed_dump_size_rejected(self):
  (self.root/'database/diaries.dump').write_bytes(b'a')
  with self.assertRaisesRegex(ValueError,'size mismatch'):inspect_dataset(self.root,ID,self.hash)
 def test_different_backup_id_rejected(self):
  with self.assertRaisesRegex(ValueError,'identity mismatch'):inspect_dataset(self.root,'20261123-003111Z',self.hash)
 def test_mismatched_files_index_rejected(self):
  (self.root/'verification/files.sha256').write_bytes(b'bad')
  with self.assertRaisesRegex(ValueError,'index/hash-list checksum mismatch'):
   inspect_dataset(self.root,ID,self.hash)
 def test_file_symlink_rejected(self):
  (self.root/'files/b/test.jpg').unlink()
  (self.root/'files/b/test.jpg').symlink_to(self.root/'files/a/image.png')
  with self.assertRaisesRegex(ValueError,'symlink'):
   inspect_dataset(self.root,ID,self.hash)
 def test_noncanonical_file_inventory_rejected(self):
  with self.assertRaises(ValueError):canonical_relative('files/../escape')
 def test_identity_status_paired_only_when_healthy(self):
  self.assertEqual(selected_backup(status(), status()),ID)
  with self.assertRaises(ValueError):selected_backup(status(),status('20261123-003111Z'))
  with self.assertRaises(ValueError):selected_backup(status('20261124-003112Z',health='error'),status())
 def test_paired_summary_matches_and_never_authorises(self):
  r=inspect_dataset(self.root,ID,self.hash)
  folder=Path(self.tmp.name)/'receipts';folder.mkdir()
  for host in ('mars','backup'):
   (folder/(host+'-status.json')).write_text(json.dumps(status()))
   (folder/(host+'-contents.json')).write_text(json.dumps(r))
  result=summarize(folder)
  self.assertEqual(result['inspectionResult'],'MATCHING_RETAINED_COMPONENT_METADATA')
  self.assertFalse(result['restoreVerified'])
  self.assertFalse(result['productionApplyAuthorised'])
  r['files']['inventorySha256']='0'*64
  (folder/'backup-contents.json').write_text(json.dumps(r))
  with self.assertRaisesRegex(ValueError,'metadata mismatch'):summarize(folder)

if __name__ == '__main__':unittest.main()
