#!/usr/bin/python3
"""Offline 0040 3H.5l integration regressions; no network or production IO."""
import importlib.util
import json
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-prepare-integration.py'
spec = importlib.util.spec_from_file_location('integration', MODULE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
AFTER=dict(S,pending=B)

def reply(op, state=AFTER, transaction=B['timestamp']):
    return json.dumps({'schema':1,'operation':op,'transaction_id':transaction,'status':'success','state':state})

class Tests(unittest.TestCase):
    def go(self, prep=(0,None), get=(0,None), **changes):
        count={'prepare':0,'get':0}
        def invoke(request):
            count['prepare']+=1
            self.assertEqual(json.loads(request)['operation'],'prepare')
            return prep[0], prep[1] if prep[1] is not None else reply('prepare')
        def read(request):
            count['get']+=1
            self.assertEqual(json.loads(request)['operation'],'get-state')
            return get[0], get[1] if get[1] is not None else reply('get-state')
        kwargs={'source_state':S,'receiver_state':S,'candidate':B,'source_verified':True,
                'invoke_prepare':invoke,'read_receiver':read}
        kwargs.update(changes)
        return m.coordinate(**kwargs), count
    def test_happy(self):
        result, calls=self.go(); self.assertEqual((calls['prepare'],calls['get']),(1,0)); self.assertEqual(result['status'],'receiver-prepared-verified')
    def test_lost_ack_recovered(self):
        result,calls=self.go(prep=(255,'')); self.assertEqual((calls['prepare'],calls['get']),(1,1)); self.assertEqual(result['status'],'receiver-prepared-recovered')
    def test_timeout_recovered(self):
        def timeout(_): raise TimeoutError('simulated')
        # Coordinator treats transport exceptions as uncertain.
        result=m.coordinate(source_state=S,receiver_state=S,candidate=B,source_verified=True,invoke_prepare=timeout,
                            read_receiver=lambda _: (0,reply('get-state')))
        self.assertEqual(result['recovery_reads'],1)
    def test_malformed_recovered(self):
        result,calls=self.go(prep=(0,'not json')); self.assertEqual(calls['get'],1)
    def test_stale_recovered(self):
        result,calls=self.go(prep=(0,reply('prepare',transaction=A['timestamp']))); self.assertEqual(calls['get'],1)
    def test_uncommitted_rejected(self):
        with self.assertRaises(m.IntegrationRefused): self.go(prep=(255,''),get=(0,reply('get-state',S)))
    def test_divergence_rejected(self):
        with self.assertRaises(m.IntegrationRefused): self.go(receiver_state=dict(S,pending=B))
    def test_previous_rejected(self):
        with self.assertRaises(m.IntegrationRefused): self.go(receiver_state=dict(S,previous=B),source_state=dict(S,previous=B))
    def test_missing_verification(self):
        with self.assertRaises(m.IntegrationRefused): self.go(source_verified=False)
    def test_invalid_candidate(self):
        with self.assertRaises(m.IntegrationRefused): self.go(candidate=A)
    def test_bad_recovery_rejected(self):
        with self.assertRaises(m.IntegrationRefused): self.go(prep=(255,''),get=(1,reply('get-state')))
    def test_no_authorities(self):
        result,_=self.go(); self.assertTrue(all(result[k] is False for k in result if k.startswith('authorizes_')))
    def test_no_cli_or_remote_io(self):
        text=MODULE.read_text(); self.assertNotIn('subprocess',text); self.assertNotIn('if __name__',text)

if __name__=='__main__': unittest.main(verbosity=2)
