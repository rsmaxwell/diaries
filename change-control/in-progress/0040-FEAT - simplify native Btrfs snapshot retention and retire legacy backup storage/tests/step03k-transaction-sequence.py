import importlib.util, json, pathlib, tempfile, unittest, sys
from unittest.mock import Mock
module=pathlib.Path(sys.argv[1]); spec=importlib.util.spec_from_file_location('manager3k',module); m=importlib.util.module_from_spec(spec);sys.modules[spec.name]=m;spec.loader.exec_module(m)
STAMP='20261023-030037Z'; UID='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
class Tests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  root=pathlib.Path(self.tmp.name);self.state=root/'state';self.state.mkdir();self.path=root/STAMP;self.path.mkdir()
  self.receipt=self.state/(STAMP+'.json');self.record=dict(schema=1,snapshot=STAMP,source_uuid=UID,destination=str(self.path),receipt=str(self.receipt))
  self.receipt.write_text(json.dumps({**self.record,'received_uuid':UID}))
 def execute(self, verify=None, delete=None, remove=None):
  m.receiver_transaction_test_sequence(self.state,self.record,verify_protection=verify or Mock(),delete_disposable_snapshot=delete or (lambda:self.path.rmdir()),remove_disposable_receipt=remove or (lambda:self.receipt.unlink()))
 def journal(self):return self.state/'.receiver-prune-pending.json'
 def test_success(self):
  v=Mock();self.execute(verify=v);v.assert_called_once();self.assertFalse(self.journal().exists());self.assertFalse(self.path.exists());self.assertFalse(self.receipt.exists())
 def test_protection_refusal(self):
  def refuse():raise m.SnapshotError('pin not verified')
  with self.assertRaises(m.SnapshotError):self.execute(verify=refuse)
  self.assertFalse(self.journal().exists());self.assertTrue(self.path.exists())
 def test_crash_before_delete(self):
  def crash():raise RuntimeError('crash')
  with self.assertRaises(RuntimeError):self.execute(delete=crash)
  self.assertTrue(self.journal().exists());self.assertTrue(self.path.exists());self.assertTrue(self.receipt.exists())
 def test_crash_after_delete(self):
  def crash():raise RuntimeError('crash after snapshot')
  with self.assertRaises(RuntimeError):self.execute(remove=crash)
  self.assertTrue(self.journal().exists());self.assertFalse(self.path.exists());self.assertTrue(self.receipt.exists())
 def test_receipt_not_removed(self):
  with self.assertRaises(m.SnapshotError):self.execute(remove=lambda:None)
  self.assertTrue(self.journal().exists())
 def test_duplicate_journal(self):
  self.journal().write_text('{}')
  with self.assertRaises(FileExistsError):self.execute()
  self.assertTrue(self.path.exists())
 def test_receipt_mismatch(self):
  payload=json.loads(self.receipt.read_text());payload['source_uuid']='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';self.receipt.write_text(json.dumps(payload))
  with self.assertRaises(m.SnapshotError):self.execute()
  self.assertFalse(self.journal().exists())
 def test_no_cli_authority(self):
  self.assertIn('receiver pruning blocked: live common-parent coordination not implemented',__import__('inspect').getsource(m.receiver_guarded_prune))
 def test_no_btrfs_delete(self):
  import inspect
  code=inspect.getsource(m.receiver_transaction_test_sequence)
  self.assertNotIn('subvolume", "delete',code)
if __name__=='__main__':unittest.main(verbosity=2,argv=[sys.argv[0]])
