#!/usr/bin/env python3
"""A staged or witnessed journal cannot enter the legacy delete path."""
import importlib.util
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]/'files'
spec=importlib.util.spec_from_file_location('rec',ROOT/'btrfs-agreed-parent-incomplete-reconciler.py')
rec=importlib.util.module_from_spec(spec);spec.loader.exec_module(rec)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE='a'*64
J={'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':NONCE,
'scope_unit':'btrfs-agreed-receive-'+B['timestamp']+'-'+NONCE[:16]+'.scope',
'scope_binding':'reserved-not-termination-evidence','receiver_boot_id':'e87ccc64-fddc-41e7-a6e0-a4151dbb3fad',
'staging':{'directory_dev':11,'directory_ino':123}}
class Tests(unittest.TestCase):
 def test_staged_is_recognised(self):
  self.assertEqual(rec.validate_journal(J,A,B),'staged')
 def test_witness_is_recognised(self):
  witnessed=dict(J,publication_witness={'subvolume_uuid':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb','received_uuid':B['uuid']})
  self.assertEqual(rec.validate_journal(witnessed,A,B),'staged')
 def test_staged_cleanup_refused_before_destructive_callbacks(self):
  state={'schema':1,'established':A,'pending':B,'previous':None}
  seen=[]
  def bad(*args,**kw):seen.append('unsafe');return True
  capture=lambda:{'state':state,'journal':J,'receipt_absent':True,
     'destination':'/@data/mars-received/@data/'+B['timestamp']}
  with self.assertRaises(rec.Refused):
   rec.reconcile(A,B,capture=capture,fence=bad,inspect_destination=bad,
     delete_subvolume=bad,remove_journal=bad,readback=bad,locks_held=True)
  self.assertFalse(seen)
if __name__=='__main__':unittest.main(verbosity=2)
