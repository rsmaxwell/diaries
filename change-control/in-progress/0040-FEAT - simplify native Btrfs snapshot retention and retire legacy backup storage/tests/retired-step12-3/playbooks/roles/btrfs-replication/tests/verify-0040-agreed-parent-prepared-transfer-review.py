#!/usr/bin/python3
"""Focused offline fail-closed tests for Integration 04A."""
import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-prepared-transfer-review.py'
spec=importlib.util.spec_from_file_location('review', path)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':B,'previous':None}
AUTH=('authorizes_prepare','authorizes_promote','authorizes_transfer','authorizes_prune','authorizes_release')
def reply(state=S): return {'schema':1,'receiver':state,**{k:False for k in AUTH}}
def valid(v):
    if set(v)!={'schema','established','pending','previous'} or v['schema']!=1: raise ValueError('bad state')
def check(source=S, receiver=None, target=B, parent=None, candidate=None):
    return m.verify_prepared(source, reply(receiver) if receiver is not None else reply(),target,
        dict(A,verified=True) if parent is None else parent,
        dict(B,verified=True) if candidate is None else candidate,valid)
class Tests(unittest.TestCase):
    def test_prepared_passes_without_authority(self):
        out=check(); self.assertEqual(out['status'],'prepared-transfer-review')
        self.assertFalse(out['transfer_executed']); self.assertFalse(out['authorizes_transfer'])
    def test_missing_pending_refused(self):
        with self.assertRaises(RuntimeError): check(source={**S,'pending':None})
    def test_divergent_receiver_refused(self):
        with self.assertRaises(RuntimeError): check(receiver={**S,'pending':None})
    def test_previous_refused(self):
        with self.assertRaises(RuntimeError): check(source={**S,'previous':A})
    def test_wrong_target_refused(self):
        with self.assertRaises(RuntimeError): check(target=A)
    def test_wrong_parent_evidence_refused(self):
        with self.assertRaises(RuntimeError): check(parent=dict(A,verified=False))
    def test_wrong_target_evidence_refused(self):
        with self.assertRaises(RuntimeError): check(candidate=dict(B,verified=False))
    def test_receiver_authority_refused(self):
        r=reply();r['authorizes_transfer']=True
        with self.assertRaises(RuntimeError): m.verify_prepared(S,r,B,dict(A,verified=True),dict(B,verified=True),valid)
    def test_no_mutation_interface(self):
        self.assertFalse(hasattr(m,'execute_transfer'))
if __name__=='__main__': unittest.main(verbosity=2)
