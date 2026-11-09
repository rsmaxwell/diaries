#!/usr/bin/env python3
import importlib.util
import pathlib
import types
import unittest

BASE = pathlib.Path(__file__).resolve().parents[1] / 'files'

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod

execution=load('sender_execution',BASE/'btrfs-agreed-parent-sender-execution.py')

A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(unittest.TestCase):
    def deps(self, *, exits=None, pin=True, receipt=True, handoff_fail=False):
        events=[]
        class Tx:
            @staticmethod
            def send_then_finalize(a,b,*,pinned_parent_verified,receive_transfer,finalise_authenticated,verify_final_receipt):
                if not pinned_parent_verified(a,b): raise RuntimeError('not pinned')
                status=receive_transfer(a,b)
                if status!={'source_send_exit':0,'ssh_exit':0}: raise RuntimeError('bad transfer')
                ack=finalise_authenticated(a,b)
                if not verify_final_receipt(a,b): raise RuntimeError('receipt missing')
                return ack
        class Commands:
            @staticmethod
            def receive_commands(a,b): events.append('commands'); return ['send'],['ssh']
        class Transport:
            @staticmethod
            def run_binary_send_ssh(s,r,*,timeout_seconds):
                events.append('transfer'); return exits if exits is not None else {'source_send_exit':0,'ssh_exit':0}
        class Handoff:
            @staticmethod
            def sender_handoff(a,b,*,exits,commands,proof_module,key):
                events.append('handoff')
                if handoff_fail: raise RuntimeError('unsafe finalise')
                assert exits=={'source_send_exit':0,'ssh_exit':0} and key==b'k'*32
                return {'status':'receiver-receipt-committed-promotion-pending'}
        kwargs=dict(transaction=Tx,fixed_commands=Commands,binary_transport=Transport,
                    sender_handoff=Handoff,session_proof=object(),read_sender_key=lambda:b'k'*32,
                    pinned_parent_verified=lambda a,b:pin,
                    verify_final_receipt=lambda a,b:receipt)
        return kwargs,events
    def test_success_once_and_receipt_only(self):
        d,e=self.deps(); result=execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,['commands','transfer','handoff'])
        self.assertEqual(result['status'],'receiver-receipt-committed-promotion-pending')
    def test_pin_prevents_transport(self):
        d,e=self.deps(pin=False)
        with self.assertRaises(RuntimeError): execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,[])
    def test_bad_send_prevents_finalise(self):
        d,e=self.deps(exits={'source_send_exit':1,'ssh_exit':0})
        with self.assertRaises(execution.ExecutionRefused): execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,['commands','transfer'])
    def test_bad_ssh_prevents_finalise(self):
        d,e=self.deps(exits={'source_send_exit':0,'ssh_exit':2})
        with self.assertRaises(execution.ExecutionRefused): execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,['commands','transfer'])
    def test_boolean_exit_prevents_finalise(self):
        d,e=self.deps(exits={'source_send_exit':False,'ssh_exit':0})
        with self.assertRaises(execution.ExecutionRefused): execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,['commands','transfer'])
    def test_handoff_failure_no_promotion(self):
        d,e=self.deps(handoff_fail=True)
        with self.assertRaises(RuntimeError): execution.execute_provisional_then_receipt(A,B,**d)
        self.assertEqual(e,['commands','transfer','handoff'])
    def test_receipt_missing_fails(self):
        d,e=self.deps(receipt=False)
        with self.assertRaises(RuntimeError): execution.execute_provisional_then_receipt(A,B,**d)
    def test_invalid_deadline(self):
        d,e=self.deps()
        with self.assertRaises(execution.ExecutionRefused): execution.execute_provisional_then_receipt(A,B,timeout_seconds=True,**d)
        self.assertEqual(e,[])
    def test_no_public_cli(self):
        self.assertFalse(hasattr(execution,'main'))

if __name__=='__main__': unittest.main(verbosity=2)
