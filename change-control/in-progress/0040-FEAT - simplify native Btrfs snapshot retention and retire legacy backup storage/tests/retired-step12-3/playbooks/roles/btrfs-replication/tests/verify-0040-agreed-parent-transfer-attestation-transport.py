#!/usr/bin/python3
import importlib.util
from pathlib import Path
import subprocess
from types import SimpleNamespace
import unittest

source = Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-transfer-attestation-transport.py'
spec = importlib.util.spec_from_file_location('attestation_transport_04e', source)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z', 'uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z', 'uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
R = {'schema':1, 'host':'backup', 'status':'transfer-attested', 'parent':A, 'candidate':B,
     'state':{'schema':1,'established':A,'pending':B,'previous':None},
     'verified':[A,B], 'state_changed':False,
     'receipt':{'schema':1,'snapshot':B['timestamp'],'source_uuid':B['uuid'],
                'received_uuid':B['uuid'],'transport':'btrfs-incremental',
                'parent_snapshot':A['timestamp'],'parent_source_uuid':A['uuid'],
                'read_only_verified':True,'source_send_exit':0,'receiver_receive_exit':0},
     **{k:False for k in m.AUTH}}

class Tests(unittest.TestCase):
    def test_success(self):
        import json
        calls=[]
        def run(cmd, **kw):
            calls.append((cmd,kw)); return SimpleNamespace(returncode=0,stdout=json.dumps(R))
        result=m.attest(A,B,source_lock_held=True,run=run)
        self.assertTrue(result['receipt_valid']); self.assertEqual(len(calls),1)
        self.assertIn('--parent-uuid',calls[0][0]); self.assertEqual(calls[0][0][:len(m.SSH_BASE)],list(m.SSH_BASE))
        self.assertNotIn('release-source', ' '.join(calls[0][0]))
    def test_lock_required(self):
        with self.assertRaises(m.AttestationError): m.attest(A,B)
    def test_invalid_identity(self):
        with self.assertRaises(m.AttestationError): m.attest(A,dict(B,uuid='bad'),source_lock_held=True)
    def test_authority_refused(self):
        with self.assertRaises(m.AttestationError): m.verify_reply(dict(R,authorizes_promote=True),A,B)
    def test_wrong_parent_refused(self):
        with self.assertRaises(m.AttestationError): m.verify_reply(dict(R,parent=B),A,B)
    def test_wrong_receipt_refused(self):
        with self.assertRaises(m.AttestationError): m.verify_reply(dict(R,receipt=dict(R['receipt'],parent_snapshot='wrong')),A,B)
    def test_unverified_candidate_refused(self):
        with self.assertRaises(m.AttestationError): m.verify_reply(dict(R,verified=[A]),A,B)
    def test_wrong_state_refused(self):
        with self.assertRaises(m.AttestationError): m.verify_reply(dict(R,state=dict(R['state'],pending=None)),A,B)
    def test_ssh_failure(self):
        with self.assertRaises(m.AttestationError): m.attest(A,B,source_lock_held=True,run=lambda *a,**kw:SimpleNamespace(returncode=1,stdout=''))
    def test_timeout(self):
        def run(*a,**kw): raise subprocess.TimeoutExpired('ssh',90)
        with self.assertRaises(m.AttestationError): m.attest(A,B,source_lock_held=True,run=run)
    def test_no_execution_entrypoint(self):
        self.assertNotIn('if __name__', source.read_text())

if __name__=='__main__': unittest.main(verbosity=2)
