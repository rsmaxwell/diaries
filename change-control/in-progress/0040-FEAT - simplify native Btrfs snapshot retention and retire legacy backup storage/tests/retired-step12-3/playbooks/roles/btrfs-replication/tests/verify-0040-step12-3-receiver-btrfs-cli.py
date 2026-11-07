#!/usr/bin/env python3
"""Regression tests for receiver-owned Btrfs diagnostics (never cleanup)."""
import importlib.util
from pathlib import Path
from unittest import TestCase, main, mock

BASE = Path(__file__).resolve().parents[1]
p = BASE / 'files/btrfs-agreed-parent-receiver-entry.py'
spec = importlib.util.spec_from_file_location('receiver_entry_btrfs', p)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Cases(TestCase):
    def deps(self, tx_present=True, destination_present=True):
        class Lock:
            def __enter__(self): return self
            def __exit__(self, *args): pass
        receiver = type("Receiver", (), {})()
        receiver._lock = mock.Mock()
        receiver._lock.side_effect = lambda stack, path: stack.enter_context(Lock())
        inspection = mock.Mock()
        inspection.inspect_locked_under_existing_locks.return_value = {
            'destination_present': tx_present, 'cleanup_authorized': False}
        inspection.inspect_btrfs_destination.return_value = (
            {'status': 'btrfs-subvolume-observed', 'cleanup_authorized': False}
            if destination_present else {'status': 'absent', 'cleanup_authorized': False})
        return {'receiver': receiver, 'finalisation-storage': mock.Mock(),
                'incomplete-inspection': inspection, 'state': mock.Mock()}
    def call(self, deps):
        with mock.patch.object(entry.os, 'geteuid', return_value=0):
            return entry.inspect_incomplete_btrfs_fixed(A, B, loader=lambda name: deps[name])
    def test_present_report_never_authorizes_cleanup(self):
        d=self.deps()
        result=self.call(d)
        self.assertFalse(result['cleanup_authorized'])
        self.assertFalse(result['stream_terminated_independently_proven'])
        self.assertFalse(result['journal_ownership_proven'])
        self.assertFalse(result['retransmit_authorized'])
        self.assertEqual(d['receiver']._lock.call_count, 2)
    def test_absent_report(self):
        result=self.call(self.deps(False, False))
        self.assertEqual(result['destination']['status'], 'absent')
    def test_disappeared_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'changed'):
            self.call(self.deps(True, False))
    def test_appeared_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'appeared'):
            self.call(self.deps(False, True))
    def test_root_required(self):
        with mock.patch.object(entry.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'root'):
                entry.inspect_incomplete_btrfs_fixed(A, B)
    def test_btrfs_error_propagates(self):
        d=self.deps()
        d['incomplete-inspection'].inspect_btrfs_destination.side_effect = RuntimeError('bad Btrfs identity')
        with self.assertRaisesRegex(RuntimeError, 'bad Btrfs'):
            self.call(d)
    def test_cli_is_exclusive(self):
        source=p.read_text()
        self.assertIn("mode.add_argument('--inspect-incomplete-btrfs'", source)
        self.assertIn('result = inspect_incomplete_btrfs_fixed(parent, candidate)', source)

if __name__ == '__main__': main(verbosity=2)
