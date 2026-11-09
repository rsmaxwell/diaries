#!/usr/bin/env python3
"""Fixed receiver staged-mode wiring; mocks prevent all real Btrfs execution."""
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import unittest

ENTRY = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receiver-entry.py'
spec = importlib.util.spec_from_file_location('staged_fixed_receiver_test', ENTRY)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Cases(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def core_receive(*args, **kwargs):
            self.calls.append((args, kwargs))
            return {'status': 'receiver-provisional-only', 'receipt_committed': False,
                    'transfer_finalized': False, 'authorizes_transition': False,
                    'authorizes_prune': False, 'authorizes_release': False}
        self.modules = {
            'receive-core': SimpleNamespace(receive_prepared_candidate_integrated=core_receive, inspect=lambda x: {}),
            'state': SimpleNamespace(), 'transfer-absence': SimpleNamespace(),
            'endpoint': SimpleNamespace(),
            'provisional-journal': SimpleNamespace(bind_staging=lambda *a, **k: None),
            'transfer-attestation': SimpleNamespace(),
            'scope-observer': SimpleNamespace(inspect_scope_lifecycle=lambda x: {'unit': x}),
            'staging-storage': SimpleNamespace(reserve=lambda *a, **k: {'directory_dev': 1, 'directory_ino': 2}),
        }
    def loader(self, name):
        if name not in self.modules:
            raise AssertionError('unexpected dependency ' + name)
        return self.modules[name]
    def invoke(self, scoped=False, staged=False):
        with patch.object(entry.os, 'geteuid', return_value=0):
            return entry.receive_fixed(A, B, input_stream=io.BytesIO(b'not a real Btrfs stream'),
                                       loader=self.loader, scoped=scoped, staged=staged)
    def test_staged_selects_privileged_scoped_execution(self):
        result = self.invoke(scoped=True, staged=True)
        self.assertEqual(result['status'], 'receiver-provisional-only')
        self.assertEqual(len(self.calls), 1)
        kwargs = self.calls[0][1]
        self.assertIsNone(kwargs['runner'])
        self.assertTrue(kwargs['scoped'])
        self.assertTrue(kwargs['staged'])
        self.assertIs(kwargs['staging_storage'], self.modules['staging-storage'])
        self.assertTrue(kwargs['scope_lifecycle'])
        self.assertTrue(callable(kwargs['scope_query']))
    def test_staged_refuses_unscoped(self):
        with self.assertRaisesRegex(RuntimeError, 'invalid scoped/staged receive mode'):
            self.invoke(scoped=False, staged=True)
        self.assertFalse(self.calls)
    def test_staged_requires_trusted_storage(self):
        self.modules['staging-storage'] = SimpleNamespace()
        with self.assertRaisesRegex(RuntimeError, 'trusted staging reservation'):
            self.invoke(scoped=True, staged=True)
        self.assertFalse(self.calls)
    def test_staged_requires_journal_binding(self):
        self.modules['provisional-journal'] = SimpleNamespace()
        with self.assertRaisesRegex(RuntimeError, 'trusted staging reservation'):
            self.invoke(scoped=True, staged=True)
        self.assertFalse(self.calls)
    def test_direct_mode_unchanged(self):
        self.invoke()
        kwargs = self.calls[0][1]
        self.assertNotIn('staged', kwargs)
        self.assertNotIn('scoped', kwargs)
        self.assertIs(kwargs['runner'], __import__('subprocess').run)
    def test_scoped_direct_unchanged(self):
        self.invoke(scoped=True)
        kwargs = self.calls[0][1]
        self.assertTrue(kwargs['scoped'])
        self.assertNotIn('staged', kwargs)
        self.assertIsNone(kwargs['runner'])
    def test_staged_mode_explicit_and_exclusive(self):
        source = ENTRY.read_text()
        self.assertIn("mode.add_argument('--receive-staged-scoped'", source)
        self.assertIn('staged=args.receive_staged_scoped', source)
        self.assertIn('mode = parser.add_mutually_exclusive_group(required=True)', source)
        self.assertIn('staged_module_loader=loader', source)
    def test_root_required(self):
        with patch.object(entry.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'root required'):
                entry.receive_fixed(A, B, input_stream=io.BytesIO(), loader=self.loader, scoped=True, staged=True)

if __name__ == '__main__':
    unittest.main(verbosity=2)
