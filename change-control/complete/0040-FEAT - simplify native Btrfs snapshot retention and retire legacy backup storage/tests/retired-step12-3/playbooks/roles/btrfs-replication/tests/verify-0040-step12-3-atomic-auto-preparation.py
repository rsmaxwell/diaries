#!/usr/bin/env python3
"""Atomic auto-candidate selection within the authoritative preparation checkpoint."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
P = Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-preparation-checkpoint.py'
s = importlib.util.spec_from_file_location('auto_checkpoint', P)
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
T = Path(__file__).resolve().parent/'verify-0040-agreed-parent-preparation-checkpoint.py'
s2 = importlib.util.spec_from_file_location('base_checkpoint_tests', T)
base = importlib.util.module_from_spec(s2); s2.loader.exec_module(base)

class AtomicSelection(unittest.TestCase):
    def make(self):
        d, events, locks, remote = base.Tests().make()
        def select(parent):
            self.assertEqual(parent, base.A['timestamp'])
            self.assertEqual([p for _,p in locks.events], ['.native-push.lock', 'btrfs-snapshot-manager.lock'])
            events.append('select')
            return dict(base.B)
        d['candidate-selection'] = SimpleNamespace(select_candidate=select)
        return d, events, locks

    def test_review_selection_inside_locks(self):
        d, events, locks = self.make()
        result = m.checkpoint(auto_target=True, deps=d)
        self.assertEqual(result['status'], 'review-only')
        self.assertEqual(events, ['select', 'get'])
        self.assertFalse(result['state_changed'])

    def test_execution_selection_and_prepare(self):
        d, events, locks = self.make()
        result = m.checkpoint(auto_target=True, execute=True, deps=d)
        self.assertEqual(result['status'], 'prepared-checkpoint')
        self.assertEqual(events[:3], ['select', 'get', 'prepare'])
        self.assertFalse(result['authorizes_transfer'])

    def test_identity_changed_refuses_before_peer_request(self):
        d, events, locks = self.make()
        d['transfer-plan'].target_identity = lambda _: dict(base.B, uuid='00000000-0000-0000-0000-000000000000')
        with self.assertRaisesRegex(RuntimeError, 'identity changed'):
            m.checkpoint(auto_target=True, execute=True, deps=d)
        self.assertEqual(events, ['select'])

    def test_no_candidate_is_read_only(self):
        d, events, locks = self.make()
        d['candidate-selection'].select_candidate = lambda _: None
        result = m.checkpoint(auto_target=True, execute=True, deps=d)
        self.assertEqual(result['status'], 'no-eligible-candidate')
        self.assertEqual(events, [])

    def test_unsettled_source_blocks_selection(self):
        d, events, locks = self.make()
        d['state'].load = lambda *a, **kw: dict(base.S, pending=base.B)
        with self.assertRaisesRegex(RuntimeError, 'already active'):
            m.checkpoint(auto_target=True, execute=True, deps=d)
        self.assertEqual(events, [])

    def test_target_modes_exclusive(self):
        d, _, _ = self.make()
        with self.assertRaisesRegex(RuntimeError, 'cannot accept'):
            m.checkpoint(base.B['timestamp'], auto_target=True, deps=d)

if __name__=='__main__': unittest.main(verbosity=2)
