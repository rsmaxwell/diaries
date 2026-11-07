#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-receive-boundary.py'
s=importlib.util.spec_from_file_location('boundary',p); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':B,'previous':None}
D={'snapshot_absent':True,'receipt_absent':True,'partial_artifacts_absent':True,'prune_journal_absent':True}
T={'parent':A,'candidate':B,'receipt_verified':True,'received_uuid_verified':True,'readonly_verified':True,'incremental_parent_verified':True}
class Test(unittest.TestCase):
 def test_preflight(self): self.assertFalse(m.verify_before_receive(S,A,B,D,manager_lock_held=True,writer_lock_held=True)['authorizes_transfer'])
 def test_manager_lock_required(self):
  with self.assertRaises(m.Refused): m.verify_before_receive(S,A,B,D,writer_lock_held=True)
 def test_writer_lock_required(self):
  with self.assertRaises(m.Refused): m.verify_before_receive(S,A,B,D,manager_lock_held=True)
 def test_divergent_state(self):
  with self.assertRaises(m.Refused): m.verify_before_receive(dict(S,pending=None),A,B,D,manager_lock_held=True,writer_lock_held=True)
 def test_partial_destination(self):
  with self.assertRaises(m.Refused): m.verify_before_receive(S,A,B,dict(D,partial_artifacts_absent=False),manager_lock_held=True,writer_lock_held=True)
 def test_prune_journal(self):
  with self.assertRaises(m.Refused): m.verify_before_receive(S,A,B,dict(D,prune_journal_absent=False),manager_lock_held=True,writer_lock_held=True)
 def test_postcondition(self): self.assertEqual(m.verify_after_receive(S,S,A,B,T,manager_lock_held=True,writer_lock_held=True)['status'],'receiver-boundary-verified')
 def test_changed_state(self):
  with self.assertRaises(m.Refused): m.verify_after_receive(S,dict(S,previous=A),A,B,T,manager_lock_held=True,writer_lock_held=True)
 def test_bad_receipt(self):
  with self.assertRaises(m.Refused): m.verify_after_receive(S,S,A,B,dict(T,receipt_verified=False),manager_lock_held=True,writer_lock_held=True)
 def test_lost_lock(self):
  with self.assertRaises(m.Refused): m.verify_after_receive(S,S,A,B,T,manager_lock_held=True)
if __name__=='__main__': unittest.main(verbosity=2)
