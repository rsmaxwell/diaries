import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

manager = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('snapshots_0040_step03j', manager)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)
STAMP = '20261023-030037Z'
UUID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'

class JournalTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root / 'state'
        self.state.mkdir()
        self.snapshot = self.root / 'received' / STAMP
        self.snapshot.parent.mkdir()
        self.snapshot.mkdir()
        self.receipt = self.state / (STAMP + '.json')
        self.receipt.write_text('{}')
        self.record = {'schema': 1, 'snapshot': STAMP, 'source_uuid': UUID,
                       'destination': str(self.snapshot), 'receipt': str(self.receipt)}
    def write(self):
        return m.receiver_journal_write(self.state, self.record)
    def test_pre_delete_journal_survives(self):
        p = self.write()
        self.assertEqual(json.loads(p.read_text()), self.record)
        self.assertTrue(self.snapshot.exists())
        self.assertTrue(self.receipt.exists())
    def test_no_overwrite(self):
        self.write()
        with self.assertRaises(FileExistsError): self.write()
    def test_reject_symlink_directory(self):
        link = self.root / 'state-link'
        link.symlink_to(self.state, target_is_directory=True)
        with self.assertRaises(m.SnapshotError): m.receiver_journal_write(link, self.record)
    def test_reject_bad_identity(self):
        self.record['snapshot'] = '../evil'
        with self.assertRaises(m.SnapshotError): self.write()
    def test_crash_after_snapshot_delete(self):
        p = self.write()
        self.snapshot.rmdir()
        with self.assertRaises(m.SnapshotError): m.receiver_journal_finish(self.state, snapshot=STAMP)
        self.assertTrue(p.exists())
    def test_crash_before_snapshot_delete(self):
        p = self.write()
        with self.assertRaises(m.SnapshotError): m.receiver_journal_finish(self.state, snapshot=STAMP)
        self.assertTrue(p.exists())
    def test_completed_delete_can_clear(self):
        p = self.write()
        self.snapshot.rmdir()
        self.receipt.unlink()
        m.receiver_journal_finish(self.state, snapshot=STAMP)
        self.assertFalse(p.exists())
    def test_wrong_identity_cannot_clear(self):
        p = self.write()
        self.snapshot.rmdir(); self.receipt.unlink()
        with self.assertRaises(m.SnapshotError): m.receiver_journal_finish(self.state, snapshot='20261022-030037Z')
        self.assertTrue(p.exists())
    def test_no_prune_authority(self):
        self.assertTrue(any(isinstance(x, str) and x.startswith('receiver pruning blocked:') for x in m.receiver_guarded_prune.__code__.co_consts))

if __name__ == '__main__':
    unittest.main(verbosity=2, argv=[sys.argv[0]])
