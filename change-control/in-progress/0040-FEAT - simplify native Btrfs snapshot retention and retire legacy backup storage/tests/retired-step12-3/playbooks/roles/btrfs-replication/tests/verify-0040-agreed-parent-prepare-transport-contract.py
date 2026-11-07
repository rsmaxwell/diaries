#!/usr/bin/python3
"""Offline regression for dormant 3H.5k request/response contract."""
import importlib.util
import json
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-prepare-transport-contract.py'
s=importlib.util.spec_from_file_location('contract',p); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
def wire(op,tid,state): return json.dumps({'schema':1,'operation':op,'transaction_id':tid,'status':'success','state':state})
class Tests(unittest.TestCase):
    def setUp(self):
        self.req=m.prepare_request(S,S,B);self.after=m.expected_after(self.req)
    def test_conditional_request(self): self.assertEqual(self.req['expected_before'],S)
    def test_expected_pending(self): self.assertEqual(self.after['pending'],B)
    def test_happy(self): self.assertEqual(m.reconcile(self.req,prepare_exit=0,prepare_stdout=wire('prepare',B['timestamp'],self.after))['status'],'receiver-prepared-verified')
    def test_lost_ack_recovery(self): self.assertEqual(m.reconcile(self.req,prepare_exit=255,prepare_stdout='',recover_exit=0,recover_stdout=wire('get-state',B['timestamp'],self.after))['status'],'receiver-prepared-recovered')
    def test_recovery_not_committed(self):
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=255,prepare_stdout='',recover_exit=0,recover_stdout=wire('get-state',B['timestamp'],S))
    def test_recovery_divergent(self):
        other=dict(S,pending={'timestamp':'20261030-180000Z','uuid':B['uuid']})
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=255,prepare_stdout='',recover_exit=0,recover_stdout=wire('get-state',B['timestamp'],other))
    def test_failed_ssh_even_valid_reply(self):
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=1,prepare_stdout=wire('prepare',B['timestamp'],self.after))
    def test_no_recovery(self):
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=255,prepare_stdout='')
    def test_stale_response(self):
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=0,prepare_stdout=wire('prepare',A['timestamp'],self.after))
    def test_wrong_postcondition(self):
        with self.assertRaises(m.ContractError): m.reconcile(self.req,prepare_exit=0,prepare_stdout=wire('prepare',B['timestamp'],S))
    def test_source_receiver_diverged(self):
        with self.assertRaises(m.ContractError): m.prepare_request(S,dict(S,pending=B),B)
    def test_pending_rejected(self):
        with self.assertRaises(m.ContractError): m.prepare_request(dict(S,pending=B),dict(S,pending=B),B)
    def test_no_mutation_authority(self):
        out=m.reconcile(self.req,prepare_exit=0,prepare_stdout=wire('prepare',B['timestamp'],self.after))
        self.assertTrue(all(out[k] is False for k in out if k.startswith('authorizes_')))
    def test_no_io(self):
        src=p.read_text(); self.assertNotIn('import subprocess',src); self.assertNotIn('os.system',src); self.assertNotIn('def main(',src)
    def test_wrong_transaction(self):
        bad=dict(self.req,transaction_id=A['timestamp'])
        with self.assertRaises(m.ContractError): m.expected_after(bad)
if __name__=='__main__':unittest.main(verbosity=2)
