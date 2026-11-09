#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest
p=pathlib.Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-incomplete-inspection.py'
spec=importlib.util.spec_from_file_location('inspection',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
a={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
b={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
s={'schema':1,'established':a,'pending':b,'previous':None}
j={'schema':1,'status':'receiving','parent':a,'candidate':b,'nonce':'a'*64}
class Tests(unittest.TestCase):
 def call(self,**changes):
  args=dict(parent=a,candidate=b,state=s,journal=j,receipt_absent=True,destination_exists=True,locks_held=True)
  args.update(changes)
  return m.inspect(**args)
 def test_no_cleanup_even_when_fenced(self):
  r=self.call(stream_terminated_proven=True)
  self.assertFalse(r['cleanup_authorized']);self.assertFalse(r['retransmit_authorized'])
 def test_no_cleanup_when_not_fenced(self):
  self.assertFalse(self.call()['stream_terminated_independently_proven'])
 def test_locks_required(self):
  with self.assertRaises(m.InspectionRefused):self.call(locks_held=False)
 def test_state_mismatch(self):
  with self.assertRaises(m.InspectionRefused):self.call(state={**s,'pending':None})
 def test_journal_mismatch(self):
  with self.assertRaises(m.InspectionRefused):self.call(journal={**j,'candidate':a})
 def test_receipt_refused(self):
  with self.assertRaises(m.InspectionRefused):self.call(receipt_absent=False)
 def test_absent_destination_is_evidence_only(self):
  self.assertFalse(self.call(destination_exists=False)['cleanup_authorized'])
 def test_unknown_destination_refused(self):
  with self.assertRaises(m.InspectionRefused):self.call(destination_exists=None)
if __name__=='__main__':unittest.main(verbosity=2)
