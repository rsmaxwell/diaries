#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace
p=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-transfer-absence-transport.py'
s=importlib.util.spec_from_file_location('transport_test',p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':B,'previous':None}
R=dict(schema=1,status='receiver-destination-absent',host='backup',parent=A,candidate=B,state=S,destination_absent=True,receipt_absent=True,state_changed=False,authorizes_transfer=False,authorizes_promote=False,authorizes_prune=False,authorizes_release=False)
class Tests(unittest.TestCase):
 def test_command_identity(self):
  c=m.command(A,B,identity=lambda x: None);self.assertEqual(c[:5],list(m.SSH[:5]));self.assertEqual(c[-2:],['--candidate-uuid',B['uuid']]);self.assertIn('richard@10.254.22.1',c)
 def test_valid(self):self.assertTrue(m.validate(R,A,B)['destination_absent'])
 def test_wrong_candidate(self):
  with self.assertRaises(RuntimeError):m.validate(dict(R,candidate=A),A,B)
 def test_unsafe_authority(self):
  with self.assertRaises(RuntimeError):m.validate(dict(R,authorizes_transfer=True),A,B)
 def test_wrong_state(self):
  with self.assertRaises(RuntimeError):m.validate(dict(R,state=dict(S,pending=None)),A,B)
 def test_lock_required(self):
  with self.assertRaises(RuntimeError):m.observe(A,B,identity=lambda x:None)
 def test_ssh_error(self):
  with self.assertRaises(RuntimeError):m.observe(A,B,source_lock_held=True,identity=lambda x:None,run=lambda *a,**k:SimpleNamespace(returncode=255,stdout=''))
 def test_timeout(self):
  def fail(*a,**k):raise subprocess.TimeoutExpired('ssh',1)
  with self.assertRaises(RuntimeError):m.observe(A,B,source_lock_held=True,identity=lambda x:None,run=fail)
if __name__=='__main__':unittest.main(verbosity=2)
