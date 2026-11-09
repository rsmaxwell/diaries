#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-incomplete-reconciler.py'
s=importlib.util.spec_from_file_location('reconciler',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
PATH='/@data/mars-received/@data/'+B['timestamp']
class Cases(unittest.TestCase):
 def setup(self):
  self.calls=[]
  self.obs={'state':{'schema':1,'established':A,'pending':B,'previous':None},'journal':{'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':'a'*64},'receipt_absent':True,'destination':PATH}
  self.proof={'path':PATH,'kind':'btrfs-subvolume','read_only':False,'committed':False,'owner_nonce':'a'*64,'exact_identity_proven':True}
 def run_it(self,**kw):
  ops=dict(capture=lambda:self.obs.copy(),fence=lambda *args:True,inspect_destination=lambda path:self.proof,delete_subvolume=lambda path:self.calls.append('delete') or True,remove_journal=lambda nonce:self.calls.append('journal') or True,readback=lambda:{'destination_absent':True,'journal_absent':True,'receipt_absent':True,'state':self.obs['state']},locks_held=True)
  ops.update(kw)
  return m.reconcile(A,B,**ops)
 def test_success(self):
  self.setup();self.assertEqual(self.run_it()['status'],'receiver-provisional-reconciled');self.assertEqual(self.calls,['delete','journal'])
 def test_no_lock(self):
  self.setup();self.assertRaises(m.Refused,self.run_it,locks_held=False);self.assertFalse(self.calls)
 def test_no_fence(self):
  self.setup();self.assertRaises(m.Refused,self.run_it,fence=lambda *args:False);self.assertFalse(self.calls)
 def test_receipt_present(self):
  self.setup();self.obs['receipt_absent']=False;self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_journal_nonce_invalid(self):
  self.setup();self.obs['journal']['nonce']='bad';self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_state_mismatch(self):
  self.setup();self.obs['state']['pending']=None;self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_readonly_refused(self):
  self.setup();self.proof['read_only']=True;self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_owner_unproven(self):
  self.setup();self.proof['exact_identity_proven']=False;self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_noncanonical_path(self):
  self.setup();self.obs['destination']='/tmp/wrong';self.assertRaises(m.Refused,self.run_it);self.assertFalse(self.calls)
 def test_changed_evidence(self):
  self.setup();n=[0]
  def change():
   n[0]+=1
   x=self.obs.copy()
   if n[0]>1: x['receipt_absent']=False
   return x
  self.assertRaises(m.Refused,self.run_it,capture=change);self.assertFalse(self.calls)
 def test_delete_failure_preserves_journal(self):
  self.setup();self.assertRaises(m.Refused,self.run_it,delete_subvolume=lambda p:False);self.assertFalse(self.calls)
 def test_journal_failure_reports_ambiguous(self):
  self.setup();self.assertRaises(m.Refused,self.run_it,remove_journal=lambda n:False);self.assertEqual(self.calls,['delete'])
 def test_bad_readback(self):
  self.setup();self.assertRaises(m.Refused,self.run_it,readback=lambda:{'destination_absent':False});self.assertEqual(self.calls,['delete','journal'])
if __name__=='__main__':unittest.main(verbosity=2)
