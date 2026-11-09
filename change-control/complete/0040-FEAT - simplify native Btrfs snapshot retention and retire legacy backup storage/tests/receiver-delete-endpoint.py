import importlib.util, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import sys

SOURCE = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('endpoint', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
UUID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

class ReceiverDelete(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.root = Path(self.t.name)
        self.snap = self.root / 'snapshots'
        self.state = self.root / 'state'
        self.snap.mkdir(); self.state.mkdir()
        self.stamp = '20261020-030000Z'
        self.parent = '20261021-030000Z'
        (self.snap / self.stamp).mkdir()
        (self.snap / self.parent).mkdir()
        self.receipt = self.state / (self.stamp + '.json')
        self.receipt.write_text(json.dumps({'schema':1,'snapshot':self.stamp,'destination':str(self.snap/self.stamp), 'source_uuid':UUID,'received_uuid':UUID,'read_only_verified':True}))
        self.parent_receipt = self.state / (self.parent + '.json')
        self.parent_receipt.write_text(json.dumps({'schema':1,'snapshot':self.parent,'destination':str(self.snap/self.parent),'source_uuid':UUID,'received_uuid':UUID,'read_only_verified':True}))
        self.journal = self.state / '.receiver-prune-pending.json'
        self.journal.write_text(json.dumps({'schema':1,'snapshot':self.stamp,'destination':str(self.snap/self.stamp),'receipt':str(self.receipt),'source_uuid':UUID,'protected_parent':self.parent,'protected_parent_uuid':UUID}))
        patches = [patch.object(mod,'RECEIVE_DIR',self.snap), patch.object(mod,'RECEIVER_STATE',self.state), patch.object(mod,'RECEIVER_PENDING',self.journal),patch.object(mod,'fs_check'),patch.object(mod,'show',side_effect=lambda p:{'Flags':'readonly','Received UUID':UUID})]
        for item in patches:
            item.start(); self.addCleanup(item.stop)
        self.deleted=[]
        def run(*args):
            self.deleted.append(args)
            (self.snap/self.stamp).rmdir()
        self.p=patch.object(mod,'run',side_effect=run)
        self.p.start(); self.addCleanup(self.p.stop)

    def test_valid_delete_keeps_receipt_journal_parent(self):
        mod.delete_receiver(self.stamp)
        self.assertEqual(len(self.deleted),1)
        self.assertEqual(self.deleted[0],('btrfs','subvolume','delete',str(self.snap/self.stamp)))
        self.assertTrue(self.receipt.exists() and self.journal.exists() and (self.snap/self.parent).exists())
    def test_missing_journal_fails(self):
        self.journal.unlink()
        with self.assertRaises(RuntimeError):mod.delete_receiver(self.stamp)
        self.assertFalse(self.deleted)
    def test_protected_parent_same_fails(self):
        d=json.loads(self.journal.read_text());d['protected_parent']=self.stamp;self.journal.write_text(json.dumps(d))
        with self.assertRaises(RuntimeError):mod.delete_receiver(self.stamp)
        self.assertFalse(self.deleted)
    def test_wrong_uuid_fails(self):
        d=json.loads(self.journal.read_text());d['source_uuid']='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb';self.journal.write_text(json.dumps(d))
        with self.assertRaises(RuntimeError):mod.delete_receiver(self.stamp)
        self.assertFalse(self.deleted)
    def test_missing_parent_fails(self):
        (self.snap/self.parent).rmdir()
        with self.assertRaises(RuntimeError):mod.delete_receiver(self.stamp)
        self.assertFalse(self.deleted)
    def test_symlink_receipt_fails(self):
        self.receipt.rename(self.state/'original')
        self.receipt.symlink_to(self.state/'original')
        with self.assertRaises(RuntimeError):mod.delete_receiver(self.stamp)
        self.assertFalse(self.deleted)

if __name__ == '__main__':unittest.main(verbosity=2,argv=[sys.argv[0]])
