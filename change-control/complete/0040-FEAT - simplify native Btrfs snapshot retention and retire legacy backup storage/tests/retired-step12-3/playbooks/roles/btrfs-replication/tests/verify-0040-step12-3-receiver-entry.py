#!/usr/bin/python3
"""Offline regression for review-only receiver entry; no production I/O."""
from contextlib import contextmanager
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-receiver-entry.py'
spec = importlib.util.spec_from_file_location('receiver_entry_test', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
STATE = {'schema': 1, 'established': A, 'pending': B, 'previous': None}

class FakeReceiver:
    def __init__(self, trace): self.trace = trace
    def _lock(self, stack, path):
        self.trace.append(('enter', path.name))
        @contextmanager
        def locked():
            try: yield
            finally: self.trace.append(('exit', path.name))
        stack.enter_context(locked())

class FakeState:
    def snapshot(self, value):
        if value not in (A, B): raise RuntimeError('bad snapshot')
    def load(self, path): return STATE

class FakeEndpoint:
    def validate_filesystem(self): pass

class FakeAbsence:
    def __init__(self, *, fail=False): self.fail = fail
    def verify(self, a, b, s, *, state):
        if self.fail: raise RuntimeError('absence refused')
        return {'destination_absent': True, 'receipt_absent': True, 'state_changed': False}

class FakeBoundary:
    def __init__(self, trace): self.trace = trace
    def verify_before_receive(self, *a, **k):
        self.trace.append(('preflight', 'boundary'))
        assert k['manager_lock_held'] and k['writer_lock_held']

class Tests(unittest.TestCase):
    def deps(self, trace, *, fail=False):
        return {'receiver': FakeReceiver(trace), 'endpoint': FakeEndpoint(),
                'state': FakeState(), 'transfer-absence': FakeAbsence(fail=fail),
                'receive-boundary': FakeBoundary(trace)}
    def test_review_lock_order_and_no_authority(self):
        trace = []
        result = m.review(A, B, dependencies=self.deps(trace))
        self.assertEqual([x[0] for x in trace], ['enter', 'enter', 'preflight', 'exit', 'exit'])
        self.assertEqual([x[1] for x in trace[:2]], ['btrfs-snapshot-manager.lock', 'writer.lock'])
        self.assertFalse(result['stream_accepted'])
        self.assertFalse(result['journal_created'])
        self.assertFalse(result['authorizes_transfer'])
    def test_failure_releases_locks(self):
        trace = []
        with self.assertRaisesRegex(RuntimeError, 'absence refused'):
            m.review(A, B, dependencies=self.deps(trace, fail=True))
        self.assertEqual([x[0] for x in trace], ['enter','enter','exit','exit'])
    def test_noncanonical_lock_paths(self):
        with self.assertRaisesRegex(RuntimeError, 'noncanonical'):
            m.review(A, B, dependencies=self.deps([]), locks=('/tmp/a','/tmp/b'))
    def test_not_executable_stream(self):
        src=FILE.read_text()
        self.assertNotIn("add_argument('--accept'", src)
        self.assertNotIn('subprocess.run(', src)
        self.assertNotIn('journal.reserve(', src)
    def test_identity_failure(self):
        with self.assertRaisesRegex(RuntimeError, 'bad snapshot'):
            m.review({'timestamp':'wrong','uuid':'wrong'}, B, dependencies=self.deps([]))

if __name__ == '__main__':
    unittest.main(verbosity=2)
