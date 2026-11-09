#!/usr/bin/env python3
"""Scoped-journal and reboot-fencing contracts; no live Btrfs deletion."""
import importlib.util
from pathlib import Path
import unittest
path=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-incomplete-reconciler.py'
spec=importlib.util.spec_from_file_location('reconciler',path)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
OLD='e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'
NEW='c67fab3c-85be-4a5e-9c69-44243ae1ab49'
def journal():
 n='a'*64
 return dict(schema=1,status='receiving',parent=A,candidate=B,nonce=n,
             scope_unit=f'btrfs-agreed-receive-{B["timestamp"]}-{n[:16]}.scope',
             scope_binding='reserved-not-termination-evidence',receiver_boot_id=OLD)
class Tests(unittest.TestCase):
 def test_scoped_contract(self): self.assertEqual(m.validate_journal(journal(),A,B),'scoped')
 def test_reboot_is_evidence_only(self):
  x=m.fence_previous_boot(journal(),boot_id_reader=lambda:NEW)
  self.assertTrue(x['termination_proven']);self.assertFalse(x['cleanup_authorized'])
  self.assertFalse(x['destination_ownership_proven']);self.assertFalse(x['retransmit_authorized'])
 def test_same_boot_refuses(self): self.assertRaises(m.Refused,m.fence_previous_boot,journal(),boot_id_reader=lambda:OLD)
 def test_missing_boot_refuses(self):
  j=journal();j.pop('receiver_boot_id');self.assertRaises(m.Refused,m.validate_journal,j,A,B)
 def test_wrong_scope_refuses(self):
  j=journal();j['scope_unit']='wrong.scope';self.assertRaises(m.Refused,m.validate_journal,j,A,B)
 def test_wrong_nonce_binding_refuses(self):
  j=journal();j['nonce']='b'*64;self.assertRaises(m.Refused,m.validate_journal,j,A,B)
 def test_bad_current_boot_refuses(self): self.assertRaises(m.Refused,m.fence_previous_boot,journal(),boot_id_reader=lambda:'invalid')
 def test_legacy_has_no_boot_fence(self):
  j={k:v for k,v in journal().items() if k not in {'scope_unit','scope_binding','receiver_boot_id'}}
  self.assertEqual(m.validate_journal(j,A,B),'legacy')
  self.assertRaises(m.Refused,m.fence_previous_boot,j,boot_id_reader=lambda:NEW)
 def test_extra_field_refuses(self):
  j=journal();j['cleanup_authorized']=True;self.assertRaises(m.Refused,m.validate_journal,j,A,B)
 def test_wrong_state_refuses(self):self.assertRaises(m.Refused,m.validate_journal,journal(),B,A)
if __name__=='__main__':unittest.main(verbosity=2)
