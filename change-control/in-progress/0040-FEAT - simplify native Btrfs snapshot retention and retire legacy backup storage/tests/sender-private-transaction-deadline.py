#!/usr/bin/env python3
"""Private subprocess deadline regression; argv[1] is sender path."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

spec=importlib.util.spec_from_file_location('sender',sys.argv[1]); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
STAMP='20261023-030037Z'; UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38'; CAND='20261022-030026Z'
CHILD='''import json,sys,time
stamp,uuid,candidate,mode=sys.argv[1:]
def send(obj): print(json.dumps(obj),flush=True)
def challenge(i):
 send(dict(kind='transaction-pin-challenge',nonce=format(i+1,'064x'),snapshot=stamp,source_uuid=uuid,candidate=candidate))
 return sys.stdin.readline()
if mode=='silent-first': time.sleep(20)
else:
 if not challenge(0): sys.exit(1)
 if mode=='silent-second': time.sleep(20)
 else:
  if not challenge(1): sys.exit(2)
  if mode=='silent-final': time.sleep(20)
  else: send(dict(kind='transaction-completed',snapshot=candidate,protected_parent=stamp,protected_parent_uuid=uuid,journal_transaction_completed=True))
'''
class Tests(unittest.TestCase):
 def setUp(self):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);self.lock=Path(d.name)/'lock';self.lock.touch();self.calls=[]
 def run_child(self,mode,timeout=1.0):
  start=time.monotonic()
  try:
   return m.run_private_transaction_process([sys.executable,'-u','-c',CHILD,STAMP,UUID,CAND,mode],STAMP,UUID,CAND,source_lock=self.lock, protect_pin=lambda role,stamp: self.pin(role,stamp),transaction_timeout=timeout,abort_timeout=.1)
  finally: self.assertLess(time.monotonic()-start,3)
 def pin(self,role,stamp): self.calls.append((role,stamp));return {'source_uuid':UUID}
 def test_silent_first(self):
  with self.assertRaisesRegex(RuntimeError,'deadline exceeded'): self.run_child('silent-first')
  self.assertEqual(len(self.calls),0)
 def test_silent_second(self):
  with self.assertRaisesRegex(RuntimeError,'deadline exceeded'): self.run_child('silent-second')
  self.assertEqual(len(self.calls),1)
 def test_silent_final(self):
  with self.assertRaisesRegex(RuntimeError,'deadline exceeded'): self.run_child('silent-final')
  self.assertEqual(len(self.calls),2)
 def test_success(self):
  self.assertEqual(self.run_child('success',1)['snapshot'],CAND)
  self.assertEqual(len(self.calls),2)
 def test_reject_invalid_deadline(self):
  with self.assertRaisesRegex(RuntimeError,'Invalid transaction deadline'): self.run_child('success',0)
 def test_private_no_cli(self): self.assertNotIn('run_private_transaction_process(',Path(sys.argv[1]).read_text().split('def main():',1)[1])
if __name__=='__main__':unittest.main(verbosity=2,argv=[sys.argv[0]])
