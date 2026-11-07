#!/usr/bin/python3
"""04R pure-adapter tests. No remote endpoint or Btrfs invocation."""
import importlib.util
from pathlib import Path
import unittest
from contextlib import contextmanager

ROOT = Path(__file__).resolve().parents[1] / 'files'

def module(name):
    import sys
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / ('btrfs-agreed-parent-' + name + '.py'))
    m = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = m
    spec.loader.exec_module(m)
    return m

c = module('receiver-session-coordinator')
b = module('receiver-session-binding')
A = {'timestamp':'20261030-030033Z', 'uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z', 'uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Cases(unittest.TestCase):
    def setUp(self):
        self.events = []
        @contextmanager
        def held(name):
            self.events.append('acquire:'+name)
            try: yield
            finally: self.events.append('release:'+name)
        self.held = held

    def locks(self, stack, name):
        stack.enter_context(self.held(name))

    def prepared(self, a, bb):
        self.events.append('preflight')
        return a == A and bb == B

    def registrations(self, token, a, bb):
        self.events.append('register')
        return [ ('data', token, b.TransportProof('richard','conn1',True,'root-coordinator')),
                 ('control', token, b.TransportProof('richard','conn2',True,'root-coordinator')) ]

    def run_review(self, **overrides):
        kw=dict(acquire_lock=self.locks, observe_prepared=self.prepared,
                trusted_registration=self.registrations, binding=b, lock_owner='root-coordinator')
        kw.update(overrides)
        return c.review(A,B,**kw)

    def test_success(self):
        r=self.run_review()
        self.assertEqual(r['status'],'receiver-session-coordination-review')
        self.assertFalse(r['authorizes_transfer'])
        self.assertEqual(self.events, ['acquire:manager','acquire:writer','preflight','register','release:writer','release:manager'])

    def test_bad_preflight(self):
        with self.assertRaises(c.CoordinatorRefused):
            self.run_review(observe_prepared=lambda a,bb:False)
        self.assertEqual(self.events[-2:], ['release:writer','release:manager'])

    def test_duplicate_channel(self):
        def duplicate(token,a,bb):
            return [('data',token,b.TransportProof('richard','one',True,'root-coordinator'))]*2
        with self.assertRaises(b.BindingRefused): self.run_review(trusted_registration=duplicate)
        self.assertEqual(self.events[-2:], ['release:writer','release:manager'])

    def test_wrong_identity(self):
        def wrong(token,a,bb):
            return [('data',token,b.TransportProof('root','one',True,'root-coordinator')),
                    ('control',token,b.TransportProof('richard','two',True,'root-coordinator'))]
        with self.assertRaises(b.BindingRefused): self.run_review(trusted_registration=wrong)

    def test_connection_reuse(self):
        def reuse(token,a,bb):
            return [('data',token,b.TransportProof('richard','one',True,'root-coordinator')),
                    ('control',token,b.TransportProof('richard','one',True,'root-coordinator'))]
        with self.assertRaises(b.BindingRefused): self.run_review(trusted_registration=reuse)

    def test_wrong_token(self):
        def wrong(token,a,bb):
            return [('data','a'*64,b.TransportProof('richard','one',True,'root-coordinator')),
                    ('control',token,b.TransportProof('richard','two',True,'root-coordinator'))]
        with self.assertRaises(b.BindingRefused): self.run_review(trusted_registration=wrong)

    def test_missing_registration(self):
        with self.assertRaises(c.CoordinatorRefused):
            self.run_review(trusted_registration=lambda token,a,bb:[])

    def test_timeout(self):
        t=[0]
        def callback(token,a,bb):
            t[0]=200
            return self.registrations(token,a,bb)
        with self.assertRaises(b.BindingRefused):
            self.run_review(clock=lambda:t[0], duration=10, trusted_registration=callback)

    def test_failure_release(self):
        def fail(token,a,bb): raise RuntimeError('transport refused')
        with self.assertRaises(RuntimeError): self.run_review(trusted_registration=fail)
        self.assertEqual(self.events[-2:], ['release:writer','release:manager'])

    def test_no_cli_or_execution(self):
        source=(ROOT / 'btrfs-agreed-parent-receiver-session-coordinator.py').read_text()
        for forbidden in ('subprocess', 'socket.', 'btrfs receive', 'if __name__', 'os.system'):
            self.assertNotIn(forbidden, source)

if __name__ == '__main__': unittest.main(verbosity=2)
