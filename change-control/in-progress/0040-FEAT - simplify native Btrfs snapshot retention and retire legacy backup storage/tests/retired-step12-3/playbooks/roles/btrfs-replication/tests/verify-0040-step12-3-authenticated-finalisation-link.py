#!/usr/bin/env python3
"""Disposable contract: HMAC sender proof verified against locked receiver nonce."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'files'
def load(filename):
    path=ROOT/filename
    spec=importlib.util.spec_from_file_location(filename.replace('-','_'),path)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
    return mod
transaction=load('btrfs-agreed-parent-finalisation-transaction.py')
proof=load('btrfs-agreed-parent-session-proof.py')
core=load('btrfs-agreed-parent-finalisation-core.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE='f'*64
KEY=b'K'*32
class Storage:
    def __init__(self,nonce=NONCE):self.nonce=nonce;self.writes=[]
    def read_state(self,_):return {'schema':1,'established':A,'pending':B,'previous':None}
    def read_journal(self,_):return {'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':self.nonce}
    def receipt_absent(self,_,__):return not self.writes
    def commit_receipt(self,stamp,receipt,*,directory,locks_held):
        if not locks_held:raise RuntimeError('no locks')
        self.writes.append((stamp,receipt))
FIELDS={'snapshot':B['timestamp'],'source_uuid':B['uuid'],'received_uuid':B['uuid'],
        'parent_snapshot':A['timestamp'],'parent_source_uuid':A['uuid'],
        'transport':'btrfs-incremental','read_only_verified':True,
        'source_send_exit':0,'receiver_receive_exit':0}
def attestation():return proof.create_proof(A,B,NONCE,key=KEY,send_exit=0,ssh_exit=0,receiver_exit=0)
class Tests(unittest.TestCase):
    def execute(self,evidence=None,key=KEY,storage=None,inspect=None):
        s=storage or Storage()
        if evidence is None:evidence=attestation()
        with patch.object(transaction,'_lock',side_effect=[101,102]):
            result=transaction.finalize_authenticated_transaction(
                A,B,evidence=evidence,key=key,proof_module=proof,
                finalisation=core,storage=s,
                inspect_received=inspect or (lambda stamp:{'flags':'readonly','received_uuid':B['uuid'],'uuid':'local-receiver-uuid'}),
                receipt_fields=FIELDS)
        return result,s
    def test_valid_session_receipt_only(self):
        result,s=self.execute()
        self.assertEqual(len(s.writes),1)
        self.assertTrue(result['journal_retained'])
        self.assertFalse(result['authorizes_transition'])
        self.assertFalse(result['authorizes_prune'])
    def test_wrong_receiver_nonce_no_write(self):
        s=Storage('e'*64)
        with self.assertRaises(proof.ProofRefused):self.execute(storage=s)
        self.assertEqual(s.writes,[])
    def test_wrong_key_no_write(self):
        s=Storage()
        with self.assertRaises(proof.ProofRefused):self.execute(key=b'Z'*32,storage=s)
        self.assertEqual(s.writes,[])
    def test_tamper_no_write(self):
        s=Storage();e=attestation();e['payload']['candidate']=A
        with self.assertRaises(proof.ProofRefused):self.execute(evidence=e,storage=s)
        self.assertEqual(s.writes,[])
    def test_unverified_btrfs_no_write(self):
        s=Storage()
        with self.assertRaises(core.FinalisationRefused):
            self.execute(storage=s,inspect=lambda _:{'flags':'readonly','received_uuid':A['uuid'],'uuid':'x'})
        self.assertEqual(s.writes,[])
    def test_missing_key_no_lock(self):
        with patch.object(transaction,'_lock') as lock:
            with self.assertRaises(transaction.TransactionRefused):self.execute(key=b'')
            lock.assert_not_called()
    def test_no_public_entry(self):
        self.assertFalse(hasattr(transaction,'main'))
if __name__=='__main__':unittest.main(verbosity=2)
