#!/usr/bin/env python3
import importlib.util
import json
import pathlib
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / 'files'
def load(filename):
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), ROOT / filename)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
handoff = load('btrfs-agreed-parent-sender-proof-handoff.py')
commands = load('btrfs-agreed-parent-fixed-commands.py')
proof = load('btrfs-agreed-parent-session-proof.py')
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
KEY = b'K'*32
NONCE = 'a'*64
GOOD = {'schema':1,'status':'receiver-receipt-committed-promotion-pending','parent':A,'candidate':B,
        'receipt_committed':True,'state_changed':False,'authorizes_prune':False,'authorizes_release':False}
class Tests(unittest.TestCase):
    def run_handoff(self, exits=None, nonce=NONCE, ack=None, final_rc=0):
        calls=[]
        def runner(argv, **kwargs):
            calls.append((argv,kwargs))
            if len(calls)==1:
                return subprocess.CompletedProcess(argv,0,json.dumps({'schema':1,'status':'receiver-session-provisional','parent':A,'candidate':B,'nonce':nonce}).encode(),b'')
            return subprocess.CompletedProcess(argv,final_rc,json.dumps(GOOD if ack is None else ack).encode(),b'')
        result=handoff.sender_handoff(A,B,exits={'source_send_exit':0,'ssh_exit':0} if exits is None else exits,
                                     commands=commands,proof_module=proof,key=KEY,runner=runner)
        return result,calls
    def test_success(self):
        result,calls=self.run_handoff()
        self.assertEqual(result['status'],'receiver-receipt-committed-promotion-pending')
        self.assertIn('--session',calls[0][0]); self.assertIn('--finalise',calls[1][0]); self.assertEqual(len(calls),2)
        submitted=json.loads(calls[1][1]['input'])
        self.assertTrue(proof.verify_proof(submitted,A,B,NONCE,key=KEY)['authenticated_session'])
    def test_failure_prevents_session_request(self):
        for exits in ({'source_send_exit':1,'ssh_exit':0},{'source_send_exit':0,'ssh_exit':1},
                      {'source_send_exit':True,'ssh_exit':0},{}):
            with self.subTest(exits=exits), self.assertRaises(handoff.HandoffRefused):
                self.run_handoff(exits=exits)
    def test_wrong_nonce_refused(self):
        with self.assertRaises(handoff.HandoffRefused): self.run_handoff(nonce='invalid')
    def test_unsafe_ack_refused(self):
        with self.assertRaises(handoff.HandoffRefused): self.run_handoff(ack={**GOOD,'authorizes_prune':True})
    def test_failed_finalisation_refused(self):
        with self.assertRaises(handoff.HandoffRefused): self.run_handoff(final_rc=1)
    def test_fixed_session_command(self):
        cmd=commands.session_command(A,B)
        self.assertEqual(cmd[:3],['ssh','-o','BatchMode=yes'])
        self.assertEqual(cmd[-8:],['--parent',A['timestamp'],'--parent-uuid',A['uuid'],
                                     '--candidate',B['timestamp'],'--candidate-uuid',B['uuid']])
    def test_no_cli(self): self.assertFalse(hasattr(handoff,'main'))
if __name__=='__main__': unittest.main(verbosity=2)
