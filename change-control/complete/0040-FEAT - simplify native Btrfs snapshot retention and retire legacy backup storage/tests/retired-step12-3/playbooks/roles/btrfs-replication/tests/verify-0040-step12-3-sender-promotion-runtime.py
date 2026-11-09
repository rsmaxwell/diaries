#!/usr/bin/env python3
import importlib.util
import json
import subprocess
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'files'
spec=importlib.util.spec_from_file_location('promotion_runtime', ROOT/'btrfs-agreed-parent-sender-promotion-runtime.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261101-140039Z','uuid':'69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'}
STATE={'schema':1,'established':B,'pending':None,'previous':A}
class Commands:
    def promote_command(self,a,b):return ['ssh','--promote']
    def promoted_readback_command(self,a,b):return ['ssh','--promoted-readback']
class Result:
    returncode=0
    def __init__(self,payload):self.stdout=json.dumps(payload).encode()
def run_for(payload):return lambda command,**kwargs: Result(payload)
class FakeState:
    def __init__(self):self.saved=[];self.value={'schema':1,'established':A,'pending':B,'previous':None}
    def load(self,p,**kwargs):return self.value.copy()
    def promote(self,v):return STATE.copy()
    def save(self,p,s,**kwargs):self.saved.append(s);self.value=s.copy()
class Tests(unittest.TestCase):
    def test_promotion_and_readback(self):
        response=STATE
        self.assertEqual(m.receiver_promote(A,B,commands=Commands(),run=run_for(response)),response)
        self.assertEqual(m.receiver_readback(A,B,commands=Commands(),run=run_for(STATE)),STATE)
    def test_reject_peer_still_pending(self):
        with self.assertRaises(m.PromotionRuntimeRefused):
            m.receiver_readback(A,B,commands=Commands(),run=run_for({'schema':1,'established':A,'pending':B,'previous':None}))
    def test_source_promotion_after_readback(self):
        state=FakeState()
        out=m.promote_source_locked(A,B,state_module=state,state_path=Path('/canonical'),verify_source=lambda x:dict(x,verified=True),receiver_readback_verified=lambda a,b:STATE)
        self.assertEqual(out,STATE);self.assertEqual(len(state.saved),1)
    def test_source_not_written_when_peer_uncertain(self):
        state=FakeState()
        with self.assertRaises(m.PromotionRuntimeRefused):
            m.promote_source_locked(A,B,state_module=state,state_path=Path('/canonical'),verify_source=lambda x:dict(x,verified=True),receiver_readback_verified=lambda a,b: {'schema':1,'established':A,'pending':B,'previous':None})
        self.assertEqual(state.saved,[])
    def test_source_not_written_on_identity_failure(self):
        state=FakeState()
        with self.assertRaises(m.PromotionRuntimeRefused):
            m.promote_source_locked(A,B,state_module=state,state_path=Path('/canonical'),verify_source=lambda x:{},receiver_readback_verified=lambda a,b:STATE)
        self.assertEqual(state.saved,[])
    def test_receiver_ack_no_prune_allowed(self):
        response=dict(STATE, authorizes_prune=True)
        with self.assertRaises(m.PromotionRuntimeRefused):m.receiver_promote(A,B,commands=Commands(),run=run_for(response))
    def test_reject_unpromoted_receiver_ack(self):
        with self.assertRaises(m.PromotionRuntimeRefused):
            m.receiver_promote(A,B,commands=Commands(),run=run_for({'schema':1,'established':A,'pending':B,'previous':None}))
    def test_reject_legacy_envelope_instead_of_wire_state(self):
        envelope={'schema':1,'status':'receiver-promoted-previous-pinned','parent':A,'candidate':B,'state':STATE,'receipt_committed':True,'authorizes_prune':False,'authorizes_release':False}
        with self.assertRaises(m.PromotionRuntimeRefused):
            m.receiver_promote(A,B,commands=Commands(),run=run_for(envelope))
    def test_nonzero_exit_fails(self):
        class BadResult:
            returncode=1
            stdout=b'{}'
        with self.assertRaises(m.PromotionRuntimeRefused):m.receiver_readback(A,B,commands=Commands(),run=lambda cmd,**kwargs:BadResult())
if __name__=='__main__':unittest.main(verbosity=2)
