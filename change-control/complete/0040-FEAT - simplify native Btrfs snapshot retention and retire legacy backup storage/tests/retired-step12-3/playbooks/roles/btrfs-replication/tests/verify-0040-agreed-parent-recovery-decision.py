#!/usr/bin/python3
"""Offline 0040 3H.5s regression: no production I/O."""
import importlib.util
from pathlib import Path
import unittest
from copy import deepcopy
from contextlib import ExitStack
from unittest.mock import patch

PATH = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-recovery-decision.py'
spec = importlib.util.spec_from_file_location('recovery', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
def state(pending=None, previous=None, parent=A):
    return {'schema':1,'established':deepcopy(parent),'pending':deepcopy(pending),'previous':deepcopy(previous)}
def reply(value=None):
    return dict(schema=1, receiver=state(B) if value is None else value, **{k:False for k in mod.AUTH})
def validate(s):
    if type(s) is not dict or set(s) != {'schema','established','pending','previous'} or s['schema'] != 1:
        raise ValueError('invalid')
    for name in ('established','pending','previous'):
        if s[name] is not None and (type(s[name]) is not dict or set(s[name]) != {'timestamp','uuid'}):
            raise ValueError('invalid snapshot')

class Tests(unittest.TestCase):
    def decide(self, source=None, receiver=None, candidate=None, vc=None, vp=None):
        return mod.decide(state() if source is None else source,
                          reply() if receiver is None else receiver,
                          deepcopy(B) if candidate is None else candidate,
                          dict(B, verified=True) if vc is None else vc,
                          dict(A, verified=True) if vp is None else vp, validate=validate)
    def test_success_no_authority(self):
        result=self.decide()
        self.assertEqual(result['status'],'receiver-prepared-source-unprepared')
        self.assertTrue(all(value is False for key,value in result.items() if key.startswith('authorizes_')))
        self.assertEqual(result['next_action'],'independent-source-prepare-review')
    def test_receiver_not_prepared(self):
        with self.assertRaises(RuntimeError): self.decide(receiver=reply(state()))
    def test_wrong_pending(self):
        with self.assertRaises(RuntimeError): self.decide(receiver=reply(state(A)))
    def test_established_mismatch(self):
        with self.assertRaises(RuntimeError): self.decide(receiver=reply(state(B, parent=B)))
    def test_source_pending(self):
        with self.assertRaises(RuntimeError): self.decide(source=state(B))
    def test_source_previous(self):
        with self.assertRaises(RuntimeError): self.decide(source=state(previous=B))
    def test_receiver_previous(self):
        with self.assertRaises(RuntimeError): self.decide(receiver=reply(state(B,previous=A)))
    def test_unverified_candidate(self):
        with self.assertRaises(RuntimeError): self.decide(vc=dict(B,verified=False))
    def test_unverified_parent(self):
        with self.assertRaises(RuntimeError): self.decide(vp=dict(A,verified=False))
    def test_claimed_authority(self):
        r=reply(); r['authorizes_transfer']=True
        with self.assertRaises(RuntimeError): self.decide(receiver=r)
    def test_unexpected_field(self):
        r=reply();r['surprise']=1
        with self.assertRaises(RuntimeError): self.decide(receiver=r)
    def test_invalid_candidate(self):
        with self.assertRaises(RuntimeError): self.decide(candidate=dict(A))
    def test_lock_order_and_observation(self):
        events=[]
        class Locks:
            def acquire(self,stack,path):
                events.append(path.name)
                return stack.enter_context(ExitStack())
        class State:
            validate=staticmethod(validate)
            def load(self,*args,**kwargs): events.append('read-source');return state()
        class Evidence:
            def verify_source(self,item):events.append('verify-'+item['timestamp']);return dict(item,verified=True)
        class Transport:
            def get_state(self,ts,**kwargs):
                selfkwargs=kwargs
                assert selfkwargs == {'source_lock_held': True}
                events.append('receiver-get-state');return reply()
        result=mod.inspect(B['timestamp'], modules=(Locks(),State(),Evidence(),Transport()),
                           target_identity=lambda ts: (events.append('target'),deepcopy(B))[1])
        self.assertEqual(result['candidate'], B)
        self.assertEqual(events[:3],['.native-push.lock','btrfs-snapshot-manager.lock','read-source'])
        self.assertEqual(events[-1],'receiver-get-state')
    def test_transport_exception_fail_closed(self):
        class Locks:
            def acquire(self,stack,path):return stack.enter_context(ExitStack())
        class State:
            validate=staticmethod(validate)
            def load(self,*args,**kwargs):return state()
        class Evidence:
            def verify_source(self,item):return dict(item,verified=True)
        class Transport:
            def get_state(self,*args,**kwargs):raise RuntimeError('SSH failed')
        with self.assertRaises(RuntimeError):
            mod.inspect(B['timestamp'],modules=(Locks(),State(),Evidence(),Transport()),target_identity=lambda ts:B)
    def test_no_mutation_entrypoint(self):
        source=PATH.read_text()
        self.assertNotIn('state.save(',source)
        self.assertNotIn('subprocess.run(',source)
        self.assertNotIn('prepare_request(',source)

if __name__ == '__main__':unittest.main(verbosity=2)
