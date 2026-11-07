
#!/usr/bin/env python3
import importlib.util, pathlib, subprocess, types, unittest, json
from unittest.mock import patch

ROOT=pathlib.Path(__file__).resolve().parents[1]/'files'

def load(filename):
 spec=importlib.util.spec_from_file_location('test_receipt_'+filename.replace('-','_').replace('.','_'),ROOT/filename)
 mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod

entry=load('btrfs-agreed-parent-receiver-entry.py')
commands=load('btrfs-agreed-parent-fixed-commands.py')
client=load('btrfs-agreed-parent-receipt-readback.py')

A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

RECEIPT={'schema':1,'snapshot':B['timestamp'],'destination':'/@data/mars-received/@data/'+B['timestamp'],'source_uuid':B['uuid'],'received_uuid':B['uuid'],'parent_snapshot':A['timestamp'],'parent_source_uuid':A['uuid'],'read_only_verified':True,'source_send_exit':0,'receiver_receive_exit':0}

class ReaderTests(unittest.TestCase):
 def fake(self,receipt=None,observed=None,state=None):
  calls=[]
  class Lock:
   def _lock(self,stack,path): calls.append(str(path))
  storage=types.SimpleNamespace(read_state=lambda p: state if state is not None else {'established':A,'pending':B,'previous':None},_safe_read=lambda p:receipt if receipt is not None else RECEIPT)
  core=types.SimpleNamespace(inspect=lambda s: observed if observed is not None else {'received_uuid':B['uuid'],'flags':'readonly'})
  with patch.object(entry.os, 'geteuid', return_value=0):
   result=entry.receipt_fixed(A,B,loader=lambda n:{'receiver':Lock(),'finalisation-storage':storage,'receive-core':core}[n])
  self.assertEqual(len(calls),2)
  return result

 def test_receipt_under_two_locks(self):
  x=self.fake();self.assertTrue(x['receipt_committed']);self.assertFalse(x['authorizes_prune'])

 def test_bad_receipt_refused(self):
  with self.assertRaises(RuntimeError):self.fake(receipt=dict(RECEIPT,received_uuid=A['uuid']))

 def test_bad_btrfs_refused(self):
  with self.assertRaises(RuntimeError):self.fake(observed={'received_uuid':B['uuid'],'flags':'rw'})

 def test_bad_state_refused(self):
  with self.assertRaises(RuntimeError):self.fake(state={'established':B,'pending':B,'previous':None})

 def test_fixed_ssh(self):
  argv=commands.receipt_command(A,B);self.assertIn('--receipt',argv);self.assertIn(B['uuid'],argv)

 def proof(self):
  return {'schema':1,'status':'receiver-final-receipt-verified','parent':A,'candidate':B,'receipt':RECEIPT,'receipt_committed':True,'authorizes_transition':False,'authorizes_prune':False,'authorizes_release':False}

 def test_sender_readback(self):
  run=lambda *a,**kw:types.SimpleNamespace(returncode=0,stdout=json.dumps(self.proof()).encode())
  self.assertTrue(client.verify_receipt_over_ssh(A,B,commands=commands,run=run))

 def test_readback_wrong_uuid(self):
  x=self.proof();x['receipt']=dict(RECEIPT,source_uuid=A['uuid'])
  run=lambda *a,**kw:types.SimpleNamespace(returncode=0,stdout=json.dumps(x).encode())
  with self.assertRaises(client.ReceiptRefused):client.verify_receipt_over_ssh(A,B,commands=commands,run=run)

 def test_receipt_boolean_exit_refused(self):
  x=self.proof();x['receipt']=dict(RECEIPT,source_send_exit=False)
  run=lambda *a,**kw:types.SimpleNamespace(returncode=0,stdout=json.dumps(x).encode())
  with self.assertRaises(client.ReceiptRefused):client.verify_receipt_over_ssh(A,B,commands=commands,run=run)

 def test_readback_failed_exit(self):
  run=lambda *a,**kw:types.SimpleNamespace(returncode=1,stdout=b'{}')
  with self.assertRaises(client.ReceiptRefused):client.verify_receipt_over_ssh(A,B,commands=commands,run=run)

 def test_no_cli(self): self.assertFalse(hasattr(client,'main'))

if __name__=='__main__':unittest.main(verbosity=2)
