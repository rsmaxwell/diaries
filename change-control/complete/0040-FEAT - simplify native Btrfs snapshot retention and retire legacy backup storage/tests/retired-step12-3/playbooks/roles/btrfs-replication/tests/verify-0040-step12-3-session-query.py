#!/usr/bin/env python3
import importlib.util, pathlib, tempfile, json, unittest
from unittest.mock import patch
P=pathlib.Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-receiver-entry.py'
s=importlib.util.spec_from_file_location('receiver_session_query',P); m=importlib.util.module_from_spec(s); s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Session(unittest.TestCase):
 def test_refuses_without_root(self):
  with patch.object(m.os,'geteuid',return_value=1000), self.assertRaises(RuntimeError):m.session_fixed(A,B)
 def test_refuses_bad_identity(self):
  with patch.object(m.os,'geteuid',return_value=0),self.assertRaises(RuntimeError):m.session_fixed(A,dict(B,uuid='bad'))
 def test_reads_only_matching_durable_journal_under_locks(self):
  class Lock:
   def _lock(self,stack,path):calls.append(str(path))
  class Storage:
   def read_state(self,path):return {'schema':1,'established':A,'pending':B,'previous':None}
   def read_journal(self,path):return {'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':'ab'*32}
  calls=[]
  with patch.object(m.os,'geteuid',return_value=0):
   out=m.session_fixed(A,B,loader=lambda n:{'receiver':Lock(),'finalisation-storage':Storage()}[n])
  self.assertEqual(calls,[str(m.MANAGER),str(m.WRITER)])
  self.assertEqual(out['nonce'],'ab'*32)
  self.assertFalse(out['receipt_committed'])
  self.assertFalse(out['authorizes_transition'])
 def test_rejects_wrong_candidate(self):
  class Lock:
   def _lock(self,stack,path):pass
  class Storage:
   def read_state(self,path):return {'schema':1,'established':A,'pending':B,'previous':None}
   def read_journal(self,path):return {'schema':1,'status':'receiving','parent':A,'candidate':dict(B,uuid='a'*36),'nonce':'ab'*32}
  with patch.object(m.os,'geteuid',return_value=0),self.assertRaises(RuntimeError):m.session_fixed(A,B,loader=lambda n:{'receiver':Lock(),'finalisation-storage':Storage()}[n])
 def test_rejects_missing_nonce(self):
  class Lock:
   def _lock(self,stack,path):pass
  class Storage:
   def read_state(self,path):return {'schema':1,'established':A,'pending':B,'previous':None}
   def read_journal(self,path):return {'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':'wrong'}
  with patch.object(m.os,'geteuid',return_value=0),self.assertRaises(RuntimeError):m.session_fixed(A,B,loader=lambda n:{'receiver':Lock(),'finalisation-storage':Storage()}[n])
 def test_no_mutating_authority(self):
  import inspect
  src=inspect.getsource(m.session_fixed)
  self.assertNotIn('commit_receipt(',src)
  self.assertNotIn('subvolume delete',src)
if __name__=='__main__':unittest.main(verbosity=2)
