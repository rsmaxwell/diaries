#!/usr/bin/env python3
"""Offline tests for dormant independent receiver readback."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-receiver-promoted-readback.py'
spec = importlib.util.spec_from_file_location('readback', FILE)
readback = importlib.util.module_from_spec(spec)
spec.loader.exec_module(readback)
A = {'timestamp': '20261030-100000Z', 'uuid': 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
B = {'timestamp': '20261030-110000Z', 'uuid': 'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'}
GOOD = {'schema': 1, 'established': B, 'pending': None, 'previous': A}


class Receiver:
    def __init__(self): self.paths = []
    def _lock(self, stack, path): self.paths.append(path)


class State:
    def __init__(self, value): self.value = value; self.calls = []
    def snapshot(self, value): self.calls.append(('snapshot', value))
    def load(self, path, *, require_root):
        self.calls.append(('load', path, require_root))
        return self.value


class Gate(unittest.TestCase):
    def go(self, state=GOOD):
        receiver, module = Receiver(), State(state)
        result = readback.read_promoted_state(A, B, dependencies={'receiver': receiver, 'state': module})
        return result, receiver, module

    def test_success(self):
        result, receiver, module = self.go()
        self.assertEqual(result, GOOD)
        self.assertEqual(receiver.paths, [readback.MANAGER, readback.WRITER])
        self.assertEqual(module.calls[-1], ('load', readback.STATE / '.agreed-parent.json', True))

    def test_pending_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'not B promoted'):
            self.go({**GOOD, 'pending': B})

    def test_missing_previous_refused(self):
        with self.assertRaises(RuntimeError): self.go({**GOOD, 'previous': None})

    def test_wrong_established_refused(self):
        with self.assertRaises(RuntimeError): self.go({**GOOD, 'established': A})

    def test_extra_state_fields_refused(self):
        with self.assertRaises(RuntimeError): self.go({**GOOD, 'unsafe': True})

    def test_invalid_order_refused_before_lock(self):
        receiver, module = Receiver(), State(GOOD)
        with self.assertRaisesRegex(RuntimeError, 'ordering'):
            readback.read_promoted_state(B, A, dependencies={'receiver': receiver, 'state': module})
        self.assertEqual(receiver.paths, [])

    def test_invalid_dependencies_refused(self):
        with self.assertRaisesRegex(RuntimeError, 'dependencies'):
            readback.read_promoted_state(A, B, dependencies={})

    def test_no_production_call_without_root(self):
        with patch.object(readback.os, 'geteuid', return_value=1000):
            with self.assertRaisesRegex(RuntimeError, 'root required'):
                readback.read_promoted_state(A, B)


if __name__ == '__main__': unittest.main(verbosity=2)
