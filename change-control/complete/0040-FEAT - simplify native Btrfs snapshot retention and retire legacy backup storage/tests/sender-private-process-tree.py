#!/usr/bin/env python3
"""0040 Step 3: private process-group and source-pin timeout regression.
Pass Playbooks sender source as argv[1]. Non-destructive local subprocesses only.
"""
import importlib.util
from pathlib import Path
from unittest import mock
import json, os, subprocess, sys, tempfile, time, unittest
spec=importlib.util.spec_from_file_location('sender',sys.argv[1]); mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
STAMP='20261023-030037Z';UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38';CAND='20261022-030026Z'
CHILD='''import os,sys,time,subprocess
if sys.argv[1]=='descendant':
 subprocess.Popen([sys.executable,'-c','import time;time.sleep(60)'],stdout=sys.stdout,stdin=sys.stdin)
 sys.exit(1)
if sys.argv[1]=='silent':time.sleep(60)
'''
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.lock=Path(self.tmp.name)/'lock';self.lock.touch()
 def call(self,mode):
  return mod.run_private_transaction_process([sys.executable,'-u','-c',CHILD,mode],STAMP,UUID,CAND,source_lock=self.lock,protect_pin=lambda *_: {'source_uuid':UUID},abort_timeout=.1,transaction_timeout=.5)
 def test_descendant_retaining_stdout_terminates(self):
  start=time.monotonic()
  with self.assertRaises(RuntimeError): self.call('descendant')
  self.assertLess(time.monotonic()-start,2.0)
 def test_silent_process_group_terminates(self):
  start=time.monotonic()
  with self.assertRaisesRegex(RuntimeError,'deadline exceeded'): self.call('silent')
  self.assertLess(time.monotonic()-start,2.0)
 def test_bounded_pin_uses_subprocess_timeout(self):
  with mock.patch.object(mod.subprocess,'run',side_effect=subprocess.TimeoutExpired('sudo',.2)) as run:
   with self.assertRaises(subprocess.TimeoutExpired): mod.bounded_private_source_pin('protect-prune-source',STAMP,timeout=.2)
   self.assertEqual(run.call_args.kwargs['timeout'],.2)
 def test_private_no_cli(self):
  main=Path(sys.argv[1]).read_text().split('def main():',1)[1]
  self.assertNotIn('run_private_transaction_process(',main)
 def test_untrusted_pin_role_rejected(self):
  with self.assertRaisesRegex(RuntimeError,'Invalid private pin renewal'):
   mod.bounded_private_source_pin('release-prune-source',STAMP)
if __name__=='__main__':unittest.main(verbosity=2,argv=[sys.argv[0]])
