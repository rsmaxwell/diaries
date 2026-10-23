import importlib.machinery
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch
import sys

loader = importlib.machinery.SourceFileLoader('tested_snapshot_manager', sys.argv[1])
spec = importlib.util.spec_from_loader(loader.name, loader)
manager = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = manager
loader.exec_module(manager)

STAMP = '20261013-171228Z'
UUID = '340674cc-d02c-244e-b7ec-e3ea5a6b151f'

class GuardTests(TestCase):
    def setUp(self):
        self.tmp = TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = Path(self.tmp.name)
        self.snapshot = self.state / STAMP
        self.snapshot.mkdir()
        self.entries = [(STAMP, manager.parse_timestamp(STAMP), self.snapshot)]
        self.config = SimpleNamespace(mode='receiver', receiver_state_dir=self.state,
            checkpoint_holds_required=True, sources=(SimpleNamespace(name='@data'),))
        self.receipt = {'schema': 1, 'snapshot': STAMP, 'destination': str(self.snapshot),
            'source_uuid': UUID, 'received_uuid': UUID, 'read_only_verified': True}
        (self.state / (STAMP + '.json')).write_text(json.dumps(self.receipt))
        self.holds = {STAMP: {'reason': 'accepted historical checkpoint', 'source_uuids': {'@data': UUID}}}

    def checked(self):
        with patch.object(manager, 'read_checkpoint_holds', return_value=self.holds):
            return manager.receiver_verified_checkpoint_holds(self.config, self.entries)

    def test_valid_held_checkpoint(self):
        self.assertEqual(self.checked(), {STAMP})

    def test_unconfigured_holds_fail_closed(self):
        self.config.checkpoint_holds_required = False
        with self.assertRaisesRegex(manager.SnapshotError, 'not configured'):
            self.checked()

    def test_missing_held_snapshot_fails_closed(self):
        with patch.object(manager, 'read_checkpoint_holds', return_value=self.holds):
            with self.assertRaisesRegex(manager.SnapshotError, 'absent'):
                manager.receiver_verified_checkpoint_holds(self.config, [])

    def test_wrong_checkpoint_uuid_fails_closed(self):
        self.receipt['source_uuid'] = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
        (self.state / (STAMP + '.json')).write_text(json.dumps(self.receipt))
        with self.assertRaisesRegex(manager.SnapshotError, 'UUID mismatch'):
            self.checked()

    def test_missing_receipt_fails_closed(self):
        (self.state / (STAMP + '.json')).unlink()
        with self.assertRaisesRegex(manager.SnapshotError, 'unsafe'):
            self.checked()

    def test_symlink_receipt_fails_closed(self):
        p = self.state / (STAMP + '.json')
        p.unlink()
        p.symlink_to(self.state / 'elsewhere')
        with self.assertRaisesRegex(manager.SnapshotError, 'unsafe'):
            self.checked()

    def test_hold_gate_is_on_destructive_path(self):
        source = Path(sys.argv[1]).read_text()
        section = source.split('def receiver_delete_one_locked(',1)[1].split('def receiver_guarded_prune(',1)[0]
        self.assertLess(section.index('receiver_verified_checkpoint_holds(config, entries)'), section.index('receiver_journal_write(state, record)'))
        self.assertIn('keep.update(receiver_verified_checkpoint_holds(config, entries))', section)

    def test_public_delete_stays_blocked(self):
        source = Path(sys.argv[1]).read_text()
        section = source.split('def receiver_guarded_prune(',1)[1].split('def show_list(',1)[0]
        self.assertIn('receiver pruning blocked', section)

if __name__ == '__main__':
    main(argv=[sys.argv[0]], verbosity=2)
