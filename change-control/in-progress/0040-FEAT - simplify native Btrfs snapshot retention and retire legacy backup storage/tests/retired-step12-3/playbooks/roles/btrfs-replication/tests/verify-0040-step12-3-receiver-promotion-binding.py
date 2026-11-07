#!/usr/bin/env python3
"""Source-only tests for actual adapter/readback composition; no host state touched."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

FILES = Path(__file__).resolve().parents[1] / 'files'
def load(stem):
    spec = importlib.util.spec_from_file_location(stem.replace('-', '_'), FILES / ('btrfs-agreed-parent-' + stem + '.py'))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
binding = load('receiver-promotion-binding')
adapter = load('receiver-promotion-adapter')
readback = load('receiver-promoted-readback')
A={'timestamp':'20261030-100000Z','uuid':'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'}
B={'timestamp':'20261030-110000Z','uuid':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'}
GOOD={'schema':1,'established':B,'pending':None,'previous':A}
class Receiver:
    def __init__(self): self.locks=[]
    def _lock(self, stack, path): self.locks.append(path)
class State:
    def __init__(self, value): self.value=value
    def snapshot(self, _value): pass
    def load(self, _path, *, require_root): return self.value
class Entry:
    def __init__(self, ack): self.ack=ack; self.calls=0
    def promote_receiver_fixed(self, a,b):
        self.calls+=1
        if isinstance(self.ack,Exception): raise self.ack
        return self.ack

def ack():
    return {'schema':1,'status':'receiver-promoted-previous-pinned', 'parent':A,'candidate':B,'state':GOOD,'receipt_committed':True,'authorizes_prune':False,'authorizes_release':False}

class Gate(unittest.TestCase):
    def run_binding(self, *, receipt=None, observed=GOOD):
        entry=Entry(ack() if receipt is None else receipt)
        receiver=Receiver(); state=State(observed)
        class Reader:
            def read_promoted_state(self, a,b):
                return readback.read_promoted_state(a,b,dependencies={'receiver':receiver,'state':state})
        result=binding.promote_verified_receiver(A,B,modules={'entry':entry,'adapter':adapter,'readback':Reader()})
        return result,entry,receiver
    def test_actual_modules_compose(self):
        result,entry,receiver=self.run_binding()
        self.assertEqual(result,GOOD)
        self.assertEqual(entry.calls,1)
        self.assertEqual(receiver.locks,[readback.MANAGER,readback.WRITER])
    def test_ack_mismatch_refuses(self):
        with self.assertRaises(adapter.PromotionAdapterRefused): self.run_binding(receipt={**ack(),'receipt_committed':False})
    def test_independent_readback_mismatch_refuses(self):
        with self.assertRaises(adapter.PromotionAdapterRefused): self.run_binding(observed={**GOOD,'previous':None})
    def test_uncertain_promotion_refuses(self):
        with self.assertRaises(adapter.PromotionAdapterRefused): self.run_binding(receipt=OSError('lost acknowledgement'))
    def test_no_release_authorization(self):
        with self.assertRaises(adapter.PromotionAdapterRefused): self.run_binding(receipt={**ack(),'authorizes_release':True})
    def test_missing_internal_dep_refuses(self):
        with self.assertRaisesRegex(RuntimeError,'dependencies'): binding.promote_verified_receiver(A,B,modules={})
    def test_root_required_without_test_seam(self):
        with patch.object(binding.os,'geteuid',return_value=1000):
            with self.assertRaisesRegex(RuntimeError,'root required'): binding.promote_verified_receiver(A,B)
if __name__=='__main__': unittest.main(verbosity=2)
