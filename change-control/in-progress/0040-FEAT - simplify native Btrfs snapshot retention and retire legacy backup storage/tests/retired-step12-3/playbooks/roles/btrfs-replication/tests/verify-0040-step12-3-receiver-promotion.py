#!/usr/bin/env python3
"""Offline regression for dormant, receipt-gated receiver promotion."""
import importlib.util
import pathlib
import types
import unittest
from unittest.mock import patch

FILES = pathlib.Path(__file__).resolve().parents[1] / 'files'
SPEC = importlib.util.spec_from_file_location('receiver_promotion_entry', FILES / 'btrfs-agreed-parent-receiver-entry.py')
ENTRY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ENTRY)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
RECEIPT = {'schema': 1, 'snapshot': B['timestamp'],
           'destination': '/@data/mars-received/@data/' + B['timestamp'],
           'source_uuid': B['uuid'], 'received_uuid': B['uuid'],
           'parent_snapshot': A['timestamp'], 'parent_source_uuid': A['uuid'],
           'read_only_verified': True, 'source_send_exit': 0, 'receiver_receive_exit': 0}


class PromotionTests(unittest.TestCase):
    def harness(self, *, receipt=None, flags='readonly', fail_save=False, bad_state=False):
        state = {'schema': 1, 'established': A, 'pending': B, 'previous': None}
        if bad_state:
            state['pending'] = None
        calls = []

        class Locks:
            def _lock(self, stack, path):
                calls.append(('lock', str(path)))

        def load(path, require_root=False):
            calls.append(('load', require_root))
            return dict(state)

        def save(path, next_state, require_root=False):
            calls.append(('save', require_root))
            if fail_save:
                raise OSError('durability failed')
            state.update(next_state)

        def promote(current):
            calls.append(('promote', True))
            return {'schema': 1, 'established': B, 'pending': None, 'previous': A}

        state_module = types.SimpleNamespace(load=load, save=save, promote=promote,
                                             snapshot=lambda x: x)
        storage = types.SimpleNamespace(read_state=lambda p: dict(state),
                                        _safe_read=lambda p: dict(RECEIPT if receipt is None else receipt))
        core = types.SimpleNamespace(inspect=lambda stamp: {'received_uuid': B['uuid'], 'flags': flags})
        modules = {'receiver': Locks(), 'finalisation-storage': storage,
                   'receive-core': core, 'state': state_module}
        def run():
            with patch.object(ENTRY.os, 'geteuid', return_value=0):
                return ENTRY.promote_receiver_fixed(A, B, loader=modules.__getitem__)
        return run, calls, state

    def test_promotes_once_and_pins_previous(self):
        run, calls, state = self.harness()
        result = run()
        self.assertEqual(state['established'], B)
        self.assertEqual(state['previous'], A)
        self.assertFalse(result['authorizes_prune'])
        self.assertFalse(result['authorizes_release'])
        self.assertEqual(sum(c[0] == 'save' for c in calls), 1)
        self.assertEqual(sum(c[0] == 'lock' for c in calls), 2)

    def test_retry_after_lost_ack_does_not_write_again(self):
        run, calls, _ = self.harness()
        run()
        run()
        self.assertEqual(sum(c[0] == 'save' for c in calls), 1)

    def test_rejects_uncommitted_receipt_identity(self):
        run, calls, _ = self.harness(receipt=dict(RECEIPT, received_uuid=A['uuid']))
        with self.assertRaises(RuntimeError):
            run()
        self.assertFalse(any(c[0] == 'save' for c in calls))

    def test_rejects_bad_btrfs_identity(self):
        run, calls, _ = self.harness(flags='rw')
        with self.assertRaises(RuntimeError):
            run()
        self.assertFalse(any(c[0] == 'save' for c in calls))

    def test_rejects_incorrect_state(self):
        run, calls, _ = self.harness(bad_state=True)
        with self.assertRaises(RuntimeError):
            run()
        self.assertFalse(any(c[0] == 'save' for c in calls))

    def test_durability_failure_not_reported_success(self):
        run, calls, _ = self.harness(fail_save=True)
        with self.assertRaises(OSError):
            run()

    def test_requires_root(self):
        run, calls, _ = self.harness()
        with patch.object(ENTRY.os, 'geteuid', return_value=1000):
            with self.assertRaises(RuntimeError):
                ENTRY.promote_receiver_fixed(A, B, loader=lambda n: None)
        self.assertEqual(calls, [])

    def test_promotion_cli_preserves_no_prune_interface(self):
        self.assertIn('def promote_receiver_fixed(', (FILES / 'btrfs-agreed-parent-receiver-entry.py').read_text())
        self.assertIn("mode.add_argument('--promote'", (FILES / 'btrfs-agreed-parent-receiver-entry.py').read_text())
        self.assertNotIn("mode.add_argument('--prune'", (FILES / 'btrfs-agreed-parent-receiver-entry.py').read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
