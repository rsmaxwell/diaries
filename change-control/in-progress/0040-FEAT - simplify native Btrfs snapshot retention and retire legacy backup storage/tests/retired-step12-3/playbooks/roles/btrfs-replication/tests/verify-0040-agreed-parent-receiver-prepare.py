#!/usr/bin/python3
"""Offline checks for dormant 3H.5d receiver preparation adapter."""
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / 'files/btrfs-agreed-parent-receiver-prepare.py'
spec = importlib.util.spec_from_file_location('prepare_adapter', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
o = m.load_orchestrator()
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S = {'schema':1,'established': A,'pending':None,'previous':None}
AFTER = o.expected_receiver_after('prepare', S, B)

def reply(op, state):
    return json.dumps({'schema':1,'operation':op,'transaction_id':B['timestamp'],
                       'status':'success','state':state})

class Tests(unittest.TestCase):
    def execute(self, invoke, recover=lambda req: (0,reply('get-state',AFTER)), **kwargs):
        return m.prepare(source=S, receiver=S, candidate=B, source_verified=True,
                         invoke=invoke, recover=recover, orchestrator=o, **kwargs)

    def test_happy(self):
        payload=[]
        x=self.execute(lambda req:(payload.append(json.loads(req)) or 0,reply('prepare',AFTER)))
        self.assertEqual(x['status'],'receiver-prepared-verified')
        self.assertEqual(payload[0]['expected_before'],S)
        self.assertEqual(payload[0]['candidate'],B)
        self.assertFalse(x['authorizes_source_prepare'])
        self.assertFalse(x['authorizes_release'])

    def test_lost_ack_recovered(self):
        x=self.execute(lambda req: (255,''))
        self.assertEqual(x['status'],'receiver-prepared-recovered')

    def test_timeout_recovered(self):
        def timeout(req): raise TimeoutError()
        self.assertEqual(self.execute(timeout)['status'],'receiver-prepared-recovered')

    def test_nonzero_with_valid_json_not_trusted(self):
        x=self.execute(lambda req:(1,reply('prepare',AFTER)))
        self.assertEqual(x['status'],'receiver-prepared-recovered')

    def test_uncommitted_blocks_retry(self):
        calls=[]
        with self.assertRaises(m.PrepareUncertain):
            self.execute(lambda req:(calls.append('prepare') or 255,''),
                         lambda req:(calls.append('get-state') or 0,reply('get-state',S)))
        self.assertEqual(calls,['prepare','get-state'])

    def test_recovery_failure(self):
        with self.assertRaises(m.PrepareUncertain):
            self.execute(lambda req:(255,''),lambda req:(255,''))

    def test_diverged_recovery(self):
        C=dict(S, established=B)
        with self.assertRaises(m.PrepareUncertain):
            self.execute(lambda req:(255,''),lambda req:(0,reply('get-state',C)))

    def test_malformed_success_recovered(self):
        self.assertEqual(self.execute(lambda req:(0,'{}'))['status'],'receiver-prepared-recovered')

    def test_stale_reply_recovered(self):
        bad=json.loads(reply('prepare', AFTER)); bad['transaction_id']='20261029-000000Z'
        self.assertEqual(self.execute(lambda req:(0,json.dumps(bad)))['status'],'receiver-prepared-recovered')

    def test_no_verified_source(self):
        with self.assertRaises(ValueError):
            m.prepare(source=S,receiver=S,candidate=B,source_verified=False,
                      invoke=lambda req: self.fail('must not invoke'),
                      recover=lambda req:self.fail('must not recover'), orchestrator=o)

    def test_pending_blocks(self):
        with self.assertRaises(ValueError):
            m.prepare(source=dict(S,pending=B),receiver=dict(S,pending=B),candidate=B,
                      source_verified=True,invoke=lambda req:self.fail('invoked'),
                      recover=lambda req:self.fail('recovered'),orchestrator=o)

    def test_source_ahead_blocks(self):
        with self.assertRaises(Exception):
            m.prepare(source=dict(S,pending=B),receiver=S,candidate=B,
                      source_verified=True,invoke=lambda req:self.fail('invoked'),
                      recover=lambda req:self.fail('recovered'),orchestrator=o)

    def test_does_not_include_live_io(self):
        source=P.read_text()
        for fragment in ('subprocess.run(', 'fcntl.flock(', 'state.save(', 'btrfs send', 'acknowledge-previous'):
            self.assertNotIn(fragment,source)

if __name__=='__main__': unittest.main(verbosity=2)
