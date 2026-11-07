#!/usr/bin/env python3
"""Disposable source-lock integration contract, no Btrfs or SSH calls."""
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace

PATH = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-execution.py'
spec = importlib.util.spec_from_file_location('sender_locked_runtime', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(unittest.TestCase):
    def run_case(self, *, state=None, evidence_ok=True, result=None):
        events = []
        class FakeLock:
            def __enter__(self): return self
            def __exit__(self, *a): events.append('release')
        def lock(stack, path):
            events.append(str(path))
            stack.enter_context(FakeLock())
        current = state or {'schema':1,'established':A,'pending':B,'previous':None}
        def verify(snapshot):
            events.append('verify')
            return dict(snapshot, verified=evidence_ok)
        def execution(a, b, *, pinned_parent_verified):
            events.append('execute')
            self.assertTrue(pinned_parent_verified(a,b))
            self.assertEqual(events[:2], [mod.SOURCE_PUSH_LOCK, mod.SOURCE_MANAGER_LOCK])
            return result if result is not None else {'status':'promotion-pending','authorizes_prune':False,'authorizes_transition':False,'authorizes_release':False}
        def load(path, *, require_root):
            self.assertEqual(str(path), mod.SOURCE_STATE)
            self.assertTrue(require_root)
            return current
        state_mod = SimpleNamespace(load=load, validate=lambda _: None)
        return events, lambda: mod.execute_with_verified_source(A,B,source_observer=SimpleNamespace(lock=lock), state_module=state_mod,evidence_module=SimpleNamespace(verify_source=verify),execution=execution)

    def test_locks_held_through_receipt(self):
        events, run = self.run_case()
        self.assertEqual(run()['status'],'promotion-pending')
        self.assertEqual(events[-3:], ['execute','release','release'])
    def test_pending_mismatch_no_execution(self):
        events, run = self.run_case(state={'schema':1,'established':A,'pending':None,'previous':None})
        with self.assertRaises(mod.ExecutionRefused): run()
        self.assertNotIn('execute',events)
    def test_previous_blocks(self):
        events, run = self.run_case(state={'schema':1,'established':A,'pending':B,'previous':A})
        with self.assertRaises(mod.ExecutionRefused): run()
        self.assertNotIn('execute',events)
    def test_wrong_source_identity(self):
        events, run = self.run_case(evidence_ok=False)
        with self.assertRaises(mod.ExecutionRefused): run()
        self.assertNotIn('execute',events)
    def test_unsafe_result_rejected(self):
        events, run = self.run_case(result={'authorizes_prune':True,'authorizes_transition':False,'authorizes_release':False})
        with self.assertRaises(mod.ExecutionRefused): run()
        self.assertEqual(events[-1], 'release')
    def test_no_public_main(self):
        self.assertFalse(hasattr(mod,'main'))

if __name__ == '__main__': unittest.main(verbosity=2)
