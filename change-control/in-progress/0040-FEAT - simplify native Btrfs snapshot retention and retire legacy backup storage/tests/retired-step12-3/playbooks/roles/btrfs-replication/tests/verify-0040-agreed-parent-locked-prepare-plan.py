#!/usr/bin/python3
"""Offline contract regressions; never contact or modify hosts."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'files'
def load(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / ('btrfs-agreed-parent-' + name + '.py'))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj

plan = load('locked-prepare-plan')
contract = load('prepare-transport-contract')
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S = {'schema':1,'established':A,'pending':None,'previous':None}

def preflight(t):
    return {'schema':1,'status':'ready-for-independent-review',
            'request':contract.prepare_request(S,S,B),
            **{'authorizes_'+k:False for k in ('prepare','source_prepare','transfer','promote','prune','release')}}

class Tests(unittest.TestCase):
    def test_happy(self):
        x=plan.build(B['timestamp'],inspect=preflight,contract=contract)
        self.assertEqual(x['request']['candidate'],B)
        self.assertEqual(x['expected_receiver_after'],dict(S,pending=B))
        self.assertTrue(all(v is False for k,v in x.items() if k.startswith('authorizes_')))
    def test_injected_preflight_called_once(self):
        calls=[]
        def spy(t):
            calls.append(t);return preflight(t)
        plan.build(B['timestamp'],inspect=spy,contract=contract)
        self.assertEqual(calls,[B['timestamp']])
    def test_missing_fields(self):
        def bad(t):
            r=preflight(t);r.pop('authorizes_release');return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_unsafe_authority(self):
        def bad(t):
            r=preflight(t);r['authorizes_prepare']=True;return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_inconsistent_transaction(self):
        def bad(t):
            r=preflight(t);r['request']['transaction_id']='20261030-160011Z';return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_existing_pending(self):
        def bad(t):
            r=preflight(t);r['request']['expected_before']=dict(S,pending=B);return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_extra_fields(self):
        def bad(t):
            r=preflight(t);r['unexpected']=1;return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_wrong_status(self):
        def bad(t):
            r=preflight(t);r['status']='done';return r
        with self.assertRaises(RuntimeError):plan.build(B['timestamp'],inspect=bad,contract=contract)
    def test_no_live_mutation(self):
        source=(ROOT/'btrfs-agreed-parent-locked-prepare-plan.py').read_text()
        for banned in ('subprocess','os.system','--apply','--promote','--accept'):
            self.assertNotIn(banned,source)
    def test_fail_closed_preflight(self):
        def bad(t):raise RuntimeError('locked observation failed')
        with self.assertRaisesRegex(RuntimeError,'locked observation failed'):
            plan.build(B['timestamp'],inspect=bad,contract=contract)

if __name__=='__main__':unittest.main(verbosity=2)
