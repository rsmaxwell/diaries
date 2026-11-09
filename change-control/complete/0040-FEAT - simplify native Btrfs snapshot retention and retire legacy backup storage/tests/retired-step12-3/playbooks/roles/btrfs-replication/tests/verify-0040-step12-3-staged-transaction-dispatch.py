#!/usr/bin/env python3
"""Transaction dispatch test with real file locks, mocked Btrfs operations."""
import importlib.util
import copy
from pathlib import Path
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]/'files'
def load(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/('btrfs-agreed-parent-'+name+'.py'))
 m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
transaction=load('finalisation-transaction'); core=load('finalisation-core')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE='a'*64
ID='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
BOOT='e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'
J={'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':NONCE,
   'scope_unit':'btrfs-agreed-receive-'+B['timestamp']+'-'+NONCE[:16]+'.scope',
   'scope_binding':'reserved-not-termination-evidence','receiver_boot_id':BOOT,
   'staging':{'directory_dev':11,'directory_ino':234}}
FIELDS={'snapshot':B['timestamp'],'source_uuid':B['uuid'],'received_uuid':B['uuid'],
'parent_snapshot':A['timestamp'],'parent_source_uuid':A['uuid'],
'transport':'btrfs-incremental','read_only_verified':True,'source_send_exit':0,'receiver_receive_exit':0}
class Tests(unittest.TestCase):
 def test_lock_owned_staged_dispatch(self):
  with tempfile.TemporaryDirectory() as tmp:
   directory=Path(tmp)
   manager=directory/'manager.lock'; writer=directory/'writer.lock'
   manager.touch();writer.touch()
   old=(transaction.MANAGER,transaction.WRITER,transaction.STATE)
   transaction.MANAGER=manager;transaction.WRITER=writer;transaction.STATE=directory
   try:
    class Storage:
     journal=copy.deepcopy(J)
     receipt=False
     def read_journal(self,d):return copy.deepcopy(self.journal)
     def read_state(self,d):return {'schema':1,'established':A,'pending':B,'previous':None}
     def receipt_absent(self,s,d):return not self.receipt
     def commit_receipt(self,s,r,**kwargs):self.receipt=True
    class Provisional:
     NAME='.agreed-parent-transfer-pending.json'
     def record_publication_witness(self,path,a,b,n,w,**kw):
      self_ref.journal['publication_witness']=copy.deepcopy(w)
    class Staging:
     published=False
     def published_absent(self,stamp,**kw):return not self.published
     def publish(self,s,n,**kw):
      self.published=True
      return {'status':'published-awaiting-receipt','receipt_committed':False,'cleanup_authorized':False}
    class Receive:
     def inspect_staged_received(self,b,n,**kw):
      return {'status':'staged-received-verified','candidate':b,
        'subvolume_uuid':ID,'receipt_committed':False,
        'publication_authorized':False,'cleanup_authorized':False}
    self_ref=Storage(); stage=Staging()
    def trusted(a,b,n):
     return {'authenticated_session':True,'source_send_exit':0,'ssh_exit':0,
             'receiver_receive_exit':0,'parent':a,'candidate':b}
    def inspect(s):
     return {'flags':'readonly','received_uuid':B['uuid'],'uuid':ID} if stage.published else None
    result=transaction.finalize_transaction(A,B, finalisation=core,storage=self_ref,
      verify_sender_completion=trusted,inspect_received=inspect,receipt_fields=FIELDS,
      lock_paths=(manager,writer),state_dir=directory,staged_receive=Receive(),
      staging_storage=stage,provisional_journal=Provisional())
    self.assertTrue(result['receipt_committed'])
    self.assertTrue(stage.published)
    self.assertTrue(self_ref.receipt)
   finally:
    transaction.MANAGER,transaction.WRITER,transaction.STATE=old
if __name__=='__main__':unittest.main(verbosity=2)
