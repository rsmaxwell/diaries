#!/usr/bin/python3
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace

P = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-get-state-transport.py'
spec = importlib.util.spec_from_file_location('get_state_transport', P)
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
T = '20261030-170009Z'
S = {'schema':1,'established':{'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'},'pending':None,'previous':None}

def reply(**kw):
    return json.dumps(dict(schema=1,operation='get-state',transaction_id=T,status='success',state=S,**kw))

class Tests(unittest.TestCase):
    def call(self, output=None, code=0, **kwargs):
        def fake(argv, **params):
            self.assertEqual(tuple(argv), m.SSH)
            self.assertEqual(json.loads(params['input'])['operation'], 'get-state')
            self.assertEqual(json.loads(params['input'])['expected_before'], None)
            self.assertEqual(params['timeout'], 60)
            return SimpleNamespace(returncode=code, stdout=reply() if output is None else output)
        return m.get_state(T, run=fake, source_lock_held=True, **kwargs)
    def test_good(self):
        r=self.call(); self.assertEqual(r['receiver'],S)
        self.assertTrue(all(v is False for k,v in r.items() if k.startswith('authorizes_')))
    def test_no_lock(self):
        with self.assertRaises(m.ObservationFailure):m.get_state(T,run=lambda *a,**kw:self.fail('ran'))
    def test_bad_tid(self):
        with self.assertRaises(m.ObservationFailure):m.get_state('../abc',source_lock_held=True,run=lambda *a,**kw:self.fail('ran'))
    def test_nonzero(self):
        with self.assertRaises(m.ObservationFailure): self.call(code=255)
    def test_malformed(self):
        with self.assertRaises(m.ObservationFailure): self.call(output='not-json')
    def test_stale(self):
        raw=json.loads(reply());raw['transaction_id']='20261030-030033Z'
        with self.assertRaises(m.ObservationFailure): self.call(output=json.dumps(raw))
    def test_extra_fields(self):
        raw=json.loads(reply());raw['extra']=1
        with self.assertRaises(m.ObservationFailure): self.call(output=json.dumps(raw))
    def test_divergent_state_is_observed_not_mutated(self):
        raw=json.loads(reply());raw['state']['previous']={'timestamp':'20261030-010000Z','uuid':'e901ddd2-66c7-0b42-b26c-ab6886273b7a'}
        self.assertIsNotNone(self.call(output=json.dumps(raw))['receiver']['previous'])
    def test_timeout(self):
        def timeout(*a,**kw): raise subprocess.TimeoutExpired('ssh',60)
        with self.assertRaises(m.ObservationFailure):m.get_state(T,run=timeout,source_lock_held=True)
    def test_no_mutation_surface(self):
        self.assertNotIn('prepare', m.__dict__)
        self.assertEqual(m.SSH[-1],'--request')
        self.assertIn('/usr/local/libexec/btrfs-agreed-parent-get-state-endpoint.py', m.SSH)
        self.assertNotIn('/usr/local/libexec/btrfs-agreed-parent-transition-endpoint.py', m.SSH)
        self.assertEqual(m.SSH[:4],('/usr/sbin/runuser','-u','richard','--'))
    def test_invalid_state(self):
        raw=json.loads(reply());raw['state']['schema']=True
        with self.assertRaises(m.ObservationFailure):self.call(output=json.dumps(raw))

if __name__=='__main__':unittest.main(verbosity=2)
