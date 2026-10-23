import importlib.util, tempfile, json, pathlib, unittest
from unittest.mock import patch
p=pathlib.Path(__import__('sys').argv.pop(1)); spec=importlib.util.spec_from_file_location('snap3i',p); m=importlib.util.module_from_spec(spec); __import__('sys').modules[spec.name]=m;spec.loader.exec_module(m)
class Test(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);root=pathlib.Path(self.t.name);self.state=root/'state';self.state.mkdir();(self.state/'writer.lock').touch();self.directory=root/'received';self.directory.mkdir();self.stamp='20261023-030037Z';self.uid='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';self.snap=self.directory/self.stamp;self.receipt=self.state/(self.stamp+'.json');self.journal=self.state/'.receiver-prune-pending.json';self.config=m.Config(snapshot_root=root,lock_path=root/'manager.lock',writer_lock_path=self.state/'writer.lock',sources=(m.SnapshotSource('data',None,self.directory),),retention=m.RetentionPolicy(48,14,12,24,5,30),verification=m.VerificationPolicy(False,'','','',None),mode='receiver',receiver_state_dir=self.state)
 def journal_write(self,**kwargs):
  r={'schema':1,'snapshot':self.stamp,'destination':str(self.snap),'receipt':str(self.receipt),'source_uuid':self.uid};r.update(kwargs);self.journal.write_text(json.dumps(r))
 def receipt_write(self,**kwargs):
  r={'schema':1,'snapshot':self.stamp,'destination':str(self.snap),'source_uuid':self.uid,'received_uuid':self.uid,'read_only_verified':True};r.update(kwargs);self.receipt.write_text(json.dumps(r))
 def runplan(self):
  def fake(command,**kw):
   import subprocess
   if command[1:3]==['subvolume','show']:return subprocess.CompletedProcess(command,0,'Received UUID: '+self.uid+'\n','')
   if command[1:3]==['property','get']:return subprocess.CompletedProcess(command,0,'ro=true\n','')
   raise AssertionError(command)
  with patch.object(m,'run',side_effect=fake):return m.receiver_recovery_plan(self.config)
 def test_clean(self):self.assertEqual(self.runplan()['state'],'CLEAN')
 def test_before_delete(self):
  self.journal_write();self.receipt_write();self.snap.mkdir();self.assertEqual(self.runplan()['state'],'BEFORE_DELETE');self.assertTrue(self.journal.exists())
 def test_after_delete(self):self.journal_write();self.receipt_write();self.assertEqual(self.runplan()['state'],'AFTER_DELETE_RECEIPT_PRESENT')
 def test_after_receipt(self):self.journal_write();self.assertEqual(self.runplan()['state'],'AFTER_RECEIPT_REMOVAL')
 def test_inconsistent(self):
  self.journal_write();self.snap.mkdir();self.assertEqual(self.runplan()['state'],'INCONSISTENT')
 def test_mismatch(self):
  self.journal_write();self.receipt_write(source_uuid='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb')
  with self.assertRaises(m.SnapshotError):self.runplan()
 def test_traversal(self):
  self.journal_write(destination='/wrong/path');self.receipt_write()
  with self.assertRaises(m.SnapshotError):self.runplan()
 def test_symlink(self):
  self.journal_write();self.receipt.symlink_to(self.state/'absent')
  with self.assertRaises(m.SnapshotError):self.runplan()
 def test_guard_still_blocked(self):
  from dataclasses import replace
  with self.assertRaisesRegex(m.SnapshotError,'live common-parent coordination not implemented'):
   m.receiver_guarded_prune(replace(self.config,receiver_prune_enabled=True))
if __name__=='__main__': unittest.main(verbosity=2)
