#!/usr/bin/python3
"""Offline tests of fixed, single-shot prepare transport; no SSH or mutation."""
import importlib.util
import json
from pathlib import Path
import subprocess
import types
import unittest

BASE = Path(__file__).resolve().parents[1] / 'files'
def module(name):
    spec=importlib.util.spec_from_file_location(name.replace('-','_'), BASE / ('btrfs-agreed-parent-'+name+'.py'))
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
m=module('prepare-transport'); c=module('prepare-transport-contract')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
R=c.prepare_request(S,S,B)

class Tests(unittest.TestCase):
    def success(self, cmd, **kw):
        self.assertEqual(cmd, list(m.SSH))
        self.assertEqual(json.loads(kw['input']), R)
        self.assertEqual(kw['timeout'],90)
        self.assertTrue(kw['capture_output'])
        return types.SimpleNamespace(returncode=0,stdout=json.dumps({'schema':1,'operation':'prepare','transaction_id':B['timestamp'],'status':'success','state':c.expected_after(R)}))
    def test_success(self):
        v=m.invoke(R,locks_held=True,source_verified=True,run=self.success,contract=c)
        self.assertEqual(v['status'],'receiver-prepared-verified')
        self.assertEqual(v['prepare_attempts'],1)
        self.assertEqual(v['receiver']['pending'],B)
        self.assertTrue(all(val is False for k,val in v.items() if k.startswith('authorizes_')))
    def test_missing_locks(self):
        with self.assertRaises(ValueError): m.invoke(R,source_verified=True,run=self.success,contract=c)
    def test_missing_evidence(self):
        with self.assertRaises(ValueError): m.invoke(R,locks_held=True,run=self.success,contract=c)
    def test_bad_request(self):
        with self.assertRaises(ValueError): m.invoke(dict(R,operation='promote'),locks_held=True,source_verified=True,run=self.success,contract=c)
    def test_extra_request_field(self):
        with self.assertRaises(ValueError): m.invoke(dict(R,unexpected=1),locks_held=True,source_verified=True,run=self.success,contract=c)
    def test_failed_exit_uncertain(self):
        with self.assertRaises(m.PrepareUncertain): m.invoke(R,locks_held=True,source_verified=True,run=lambda *a,**k: types.SimpleNamespace(returncode=1,stdout=''),contract=c)
    def test_timeout_uncertain(self):
        def timeout(*a,**k): raise subprocess.TimeoutExpired('ssh',90)
        with self.assertRaises(m.PrepareUncertain): m.invoke(R,locks_held=True,source_verified=True,run=timeout,contract=c)
    def test_missing_reply_uncertain(self):
        with self.assertRaises(m.PrepareUncertain): m.invoke(R,locks_held=True,source_verified=True,run=lambda *a,**k: types.SimpleNamespace(returncode=0,stdout=''),contract=c)
    def test_wrong_state_uncertain(self):
        def wrong(*a,**k): return types.SimpleNamespace(returncode=0,stdout=json.dumps({'schema':1,'operation':'prepare','transaction_id':B['timestamp'],'status':'success','state':S}))
        with self.assertRaises(m.PrepareUncertain): m.invoke(R,locks_held=True,source_verified=True,run=wrong,contract=c)
    def test_no_entrypoint(self):
        source=(BASE/'btrfs-agreed-parent-prepare-transport.py').read_text()
        self.assertNotIn("if __name__ == '__main__'",source)
        self.assertNotIn('release-source',source)
        self.assertNotIn('btrfs subvolume delete',source)
if __name__=='__main__': unittest.main(verbosity=2)
