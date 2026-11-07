#!/usr/bin/env python3
"""Source/disposable tests: no installed key or Btrfs operation."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]/'files'
spec=importlib.util.spec_from_file_location('agreed_receiver',ROOT/'btrfs-agreed-parent-receiver-entry.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
P={'payload':{'schema':1},'mac':'a'*64}
class Transaction:
    def __init__(self): self.calls=[]
    def finalize_authenticated_transaction(self,*args,**kw):
        self.calls.append((args,kw))
        return {'status':'receiver-receipt-committed-promotion-pending','receipt_committed':True,
                'authorizes_transition':False,'authorizes_prune':False,'authorizes_release':False}
class Tests(unittest.TestCase):
    def invoke(self,payload=None, reader=lambda:b'K'*32, root=True):
        txn=Transaction(); modules={'finalisation-transaction':txn,'finalisation-core':object(),
            'finalisation-storage':object(),'session-proof':object(),
            'receive-core':type('Inspector',(),{'inspect':staticmethod(lambda stamp:{})})()}
        with patch.object(m.os,'geteuid',return_value=0 if root else 1000):
            result=m.finalise_fixed(A,B,input_stream=io.BytesIO(payload if payload is not None else json.dumps(P).encode()),
                                    loader=modules.__getitem__,key_reader=reader)
        return result,txn
    def test_fixed_trusted_binding(self):
        result,t=self.invoke();self.assertEqual(len(t.calls),1)
        self.assertEqual(t.calls[0][1]['key'],b'K'*32)
        self.assertEqual(t.calls[0][1]['evidence'],P)
        self.assertEqual(t.calls[0][1]['receipt_fields']['source_uuid'],B['uuid'])
        self.assertFalse(result['authorizes_transition'])
    def test_nonroot_refused(self):
        with self.assertRaisesRegex(RuntimeError,'root'):self.invoke(root=False)
    def test_oversized_payload_refused(self):
        with self.assertRaisesRegex(RuntimeError,'oversized'):self.invoke(payload=b'x'*4097)
    def test_missing_proof_refused(self):
        with self.assertRaisesRegex(RuntimeError,'missing'):self.invoke(payload=b'')
    def test_invalid_identity_prevents_key_read(self):
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'identity'):
                m.finalise_fixed({'timestamp':'oops','uuid':A['uuid']},B,
                   input_stream=io.BytesIO(json.dumps(P).encode()),key_reader=lambda: (_ for _ in ()).throw(AssertionError()))
    def test_reject_unsafe_transaction_result(self):
        class Unsafe:
            def finalize_authenticated_transaction(self,*a,**k):return {'status':'receiver-receipt-committed-promotion-pending','receipt_committed':True,'authorizes_transition':True,'authorizes_prune':False,'authorizes_release':False}
        modules={'finalisation-transaction':Unsafe(),'finalisation-core':object(),'finalisation-storage':object(),'session-proof':object(),'receive-core':type('I',(),{'inspect':staticmethod(lambda _: {})})()}
        with patch.object(m.os,'geteuid',return_value=0):
            with self.assertRaisesRegex(RuntimeError,'unsafe finalisation'):
                m.finalise_fixed(A,B,input_stream=io.BytesIO(json.dumps(P).encode()),loader=modules.__getitem__,key_reader=lambda:b'K'*32)
    def test_no_cli_provided_key_or_exits(self):
        import inspect
        src=inspect.getsource(m.main)
        self.assertNotIn('source-send-exit',src)
        self.assertNotIn('key-file',src)
        self.assertIn('input_stream=sys.stdin.buffer',src)
    def test_canonical_key_only(self):
        with self.assertRaisesRegex(RuntimeError,'noncanonical'):
            m.read_protected_key(Path('/tmp/not-our-key'))
    def test_key_permissions(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'key';path.write_bytes(b'K'*32);path.chmod(0o644)
            with patch.object(m,'PROOF_KEY',path):
                with self.assertRaisesRegex(RuntimeError,'unsafe'):
                    m.read_protected_key(path)
if __name__=='__main__':unittest.main(verbosity=2)
