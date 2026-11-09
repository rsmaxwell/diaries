import importlib.util, json, tempfile, unittest, sys
from pathlib import Path
from unittest.mock import patch
endpoint_path, manager_path = map(Path, sys.argv[1:3])
spec = importlib.util.spec_from_file_location('endpoint_contract', endpoint_path)
endpoint = importlib.util.module_from_spec(spec); spec.loader.exec_module(endpoint)
UID='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
BAD='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
class ParentContract(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory(); self.addCleanup(t.cleanup)
        root=Path(t.name);self.snap=root/'snap';self.state=root/'state';self.snap.mkdir();self.state.mkdir()
        self.stamp='20261020-030000Z';self.parent='20261021-030000Z'
        (self.snap/self.stamp).mkdir();(self.snap/self.parent).mkdir()
        self.receipt=self.state/(self.stamp+'.json');self.parent_receipt=self.state/(self.parent+'.json')
        for stamp,path in ((self.stamp,self.receipt),(self.parent,self.parent_receipt)):
            path.write_text(json.dumps({'schema':1,'snapshot':stamp,'destination':str(self.snap/stamp),'source_uuid':UID,'received_uuid':UID,'read_only_verified':True}))
        self.journal=self.state/'.receiver-prune-pending.json'
        self.journal.write_text(json.dumps({'schema':1,'snapshot':self.stamp,'destination':str(self.snap/self.stamp),'receipt':str(self.receipt),'source_uuid':UID,'protected_parent':self.parent,'protected_parent_uuid':UID}))
        self.calls=[]
        def fake_run(*args):
            self.calls.append(args)
            (self.snap/self.stamp).rmdir()
        for key,val in [('RECEIVE_DIR',self.snap),('RECEIVER_STATE',self.state),('RECEIVER_PENDING',self.journal),('fs_check',lambda *a:None),('show',lambda p:{'Flags':'readonly','Received UUID':UID}),('run',fake_run)]:
            p=patch.object(endpoint,key,val);p.start();self.addCleanup(p.stop)
    def test_consistent_parent_succeeds(self):
        endpoint.delete_receiver(self.stamp);self.assertEqual(len(self.calls),1)
    def test_missing_parent_uuid_rejected(self):
        j=json.loads(self.journal.read_text());j.pop('protected_parent_uuid');self.journal.write_text(json.dumps(j))
        with self.assertRaises(RuntimeError):endpoint.delete_receiver(self.stamp)
        self.assertFalse(self.calls)
    def test_parent_uuid_mismatch_rejected(self):
        j=json.loads(self.journal.read_text());j['protected_parent_uuid']=BAD;self.journal.write_text(json.dumps(j))
        with self.assertRaises(RuntimeError):endpoint.delete_receiver(self.stamp)
        self.assertFalse(self.calls)
    def test_parent_receipt_mismatch_rejected(self):
        p=json.loads(self.parent_receipt.read_text());p['source_uuid']=BAD;self.parent_receipt.write_text(json.dumps(p))
        with self.assertRaises(RuntimeError):endpoint.delete_receiver(self.stamp)
        self.assertFalse(self.calls)
    def test_missing_parent_receipt_rejected(self):
        self.parent_receipt.unlink()
        with self.assertRaises(RuntimeError):endpoint.delete_receiver(self.stamp)
        self.assertFalse(self.calls)
    def test_manager_requires_parent_uuid_in_journal(self):
        src=manager_path.read_text()
        self.assertIn('"protected_parent": protected_stamp, "protected_parent_uuid": parent_uuid',src)
        self.assertIn('raise SnapshotError("receiver pruning blocked: live common-parent coordination not implemented")',src)
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
