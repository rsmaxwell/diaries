#!/usr/bin/env python3
import importlib.util
import json
import re
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-provisional-journal.py'
spec=importlib.util.spec_from_file_location('provisional',MODULE)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Tests(unittest.TestCase):
 def test_durable_reservation_no_overwrite(self):
  with tempfile.TemporaryDirectory() as td:
   p=m.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True)
   self.assertEqual(json.loads(p.read_text())['status'],'receiving')
   self.assertRegex(json.loads(p.read_text())['nonce'],r'^[0-9a-f]{64}$')
   self.assertEqual(p.stat().st_mode & 0o777,0o600)
   with self.assertRaises(m.Refused): m.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True)
   self.assertTrue(p.exists())
 def test_nonce_is_unique_per_reservation(self):
  with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
   one=json.loads(m.reserve(first,A,B,manager_lock_held=True,writer_lock_held=True).read_text())['nonce']
   two=json.loads(m.reserve(second,A,B,manager_lock_held=True,writer_lock_held=True).read_text())['nonce']
   self.assertNotEqual(one,two)
 def test_refuse_missing_locks(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(m.Refused):m.reserve(td,A,B,manager_lock_held=True)
   self.assertFalse((Path(td)/m.NAME).exists())
 def test_symlink_refused(self):
  with tempfile.TemporaryDirectory() as td:
   (Path(td)/m.NAME).symlink_to('/nonexistent')
   with self.assertRaises(m.Refused):m.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True)
 def test_bad_identity(self):
  with tempfile.TemporaryDirectory() as td:
   with self.assertRaises(m.Refused):m.reserve(td,A,{**B,'timestamp':'../abc'},manager_lock_held=True,writer_lock_held=True)
 def test_existing_guards(self):
  root=Path(__file__).resolve().parents[1]
  receiver=(root/'files'/'btrfs-native-push-receiver.py').read_text()
  manager=(root.parent/'snapshots'/'files'/'btrfs-snapshot-manager.py').read_text()
  self.assertIn("STATE / '.agreed-parent-transfer-pending.json'",receiver)
  self.assertGreaterEqual(manager.count('unfinished agreed-parent transfer blocks receiver pruning'),2)
if __name__=='__main__':unittest.main(verbosity=2)
