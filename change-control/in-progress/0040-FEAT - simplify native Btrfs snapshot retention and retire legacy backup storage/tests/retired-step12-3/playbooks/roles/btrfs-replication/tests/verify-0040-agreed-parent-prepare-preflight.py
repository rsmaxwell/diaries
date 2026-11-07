#!/usr/bin/python3
"""Offline, no root, no network or Btrfs test of 0040 3H.5j."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

PATH = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-prepare-preflight.py'
spec = importlib.util.spec_from_file_location('preflight', PATH)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
STATE = {'schema':1,'established':A,'pending':None,'previous':None}

def validate(s):
    if set(s) != {'schema','established','pending','previous'}: raise ValueError('state')

class Tests(unittest.TestCase):
    def test_ready_never_authorizes(self):
        r=p.evaluate(STATE,STATE,B,dict(B,verified=True),validate=validate)
        self.assertEqual(r['request']['operation'],'prepare')
        self.assertEqual(r['request']['expected_before'],STATE)
        self.assertEqual(r['request']['transaction_id'], B['timestamp'])
        self.assertTrue(all(v is False for k,v in r.items() if k.startswith('authorizes_')))
    def test_diverged(self):
        with self.assertRaises(RuntimeError): p.evaluate(STATE,dict(STATE,established=B),B,dict(B,verified=True),validate=validate)
    def test_pending(self):
        s=dict(STATE,pending=B)
        with self.assertRaises(RuntimeError): p.evaluate(s,s,B,dict(B,verified=True),validate=validate)
    def test_previous(self):
        s=dict(STATE,previous=B)
        with self.assertRaises(RuntimeError): p.evaluate(s,s,B,dict(B,verified=True),validate=validate)
    def test_invalid_evidence(self):
        with self.assertRaises(RuntimeError): p.evaluate(STATE,STATE,B,B,validate=validate)
    def test_stale_candidate(self):
        with self.assertRaises(RuntimeError): p.evaluate(STATE,STATE,A,dict(A,verified=True),validate=validate)
    def test_invalid_candidate(self):
        with self.assertRaises(RuntimeError): p.evaluate(STATE,STATE,dict(B,extra=True),dict(B,verified=True),validate=validate)
    def test_failed_validation(self):
        with self.assertRaises(ValueError): p.evaluate(dict(STATE,unexpected=1),STATE,B,dict(B,verified=True),validate=validate)
    def test_no_mutating_surface(self):
        import inspect
        text=inspect.getsource(p)
        self.assertNotIn('subprocess.run(',text)
        self.assertNotIn('state.save(',text)
        self.assertNotIn('btrfs send',text)
    def test_source_locked_sequence(self):
        # Exercise lock order and ensure failure occurs before any receiver I/O.
        l=Mock(); s=Mock(); e=Mock(); t=Mock()
        s.load.return_value=dict(STATE,pending=B)
        with self.assertRaises(RuntimeError): p.inspect(B['timestamp'],modules=(l,s,e,t))
        self.assertEqual([c.args[1] for c in l.acquire.call_args_list],[p.PUSH_LOCK,p.MANAGER_LOCK])
        t.get_state.assert_not_called()

if __name__=='__main__': unittest.main(verbosity=2)
