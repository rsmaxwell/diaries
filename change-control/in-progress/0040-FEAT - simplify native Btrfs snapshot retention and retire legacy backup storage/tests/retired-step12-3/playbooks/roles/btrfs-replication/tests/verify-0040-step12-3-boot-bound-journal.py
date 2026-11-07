#!/usr/bin/env python3
"""Boot identity binding is durable but has no deletion authority."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
src = Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-provisional-journal.py'
spec=importlib.util.spec_from_file_location('boot_bound',src)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
BOOT1='e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'
BOOT2='c67fab3c-85be-4a5e-9c69-44243ae1ab49'
class Cases(unittest.TestCase):
 def reserve(self, scoped=True, reader=lambda: BOOT1):
  with tempfile.TemporaryDirectory() as d:
   p=m.reserve(d,A,B,manager_lock_held=True,writer_lock_held=True,scoped=scoped,boot_id_reader=reader)
   return json.loads(p.read_text())
 def test_scoped_journal_binds_boot(self):
  j=self.reserve();self.assertEqual(j['receiver_boot_id'],BOOT1)
  self.assertNotIn('cleanup_authorized',j)
 def test_unscoped_remains_unchanged(self):
  j=self.reserve(scoped=False);self.assertNotIn('receiver_boot_id',j)
 def test_bad_boot_refuses_without_file(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(m.Refused):
    m.reserve(d,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True,boot_id_reader=lambda:'bad')
   self.assertFalse((Path(d)/m.NAME).exists())
 def test_previous_boot_only_evidence(self):
  r=m.assess_previous_boot(self.reserve(),current_boot_id=BOOT2)
  self.assertTrue(r['old_boot_terminated']);self.assertFalse(r['cleanup_authorized']);self.assertFalse(r['retransmit_authorized'])
 def test_same_boot_does_not_fence(self):
  r=m.assess_previous_boot(self.reserve(),current_boot_id=BOOT1)
  self.assertFalse(r['old_boot_terminated'])
 def test_missing_boot_fails_closed(self):
  j=self.reserve();j.pop('receiver_boot_id')
  with self.assertRaises(m.Refused):m.assess_previous_boot(j,current_boot_id=BOOT2)
 def test_bad_current_boot_fails_closed(self):
  with self.assertRaises(m.Refused):m.assess_previous_boot(self.reserve(),current_boot_id='unknown')
 def test_unscoped_not_fencing(self):
  with self.assertRaises(m.Refused):m.assess_previous_boot(self.reserve(scoped=False),current_boot_id=BOOT2)
if __name__=='__main__':unittest.main(verbosity=2)
