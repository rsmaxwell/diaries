#!/usr/bin/env python3
"""Internal receive adapter regressions; never invokes Btrfs or sudo."""
import importlib.util
from pathlib import Path
import subprocess
import unittest
from types import SimpleNamespace

PATH = Path(__file__).resolve().parents[1] / 'files/btrfs-native-push-receiver.py'
spec = importlib.util.spec_from_file_location('receiver_internal_0040', PATH)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp':'20261030-030033Z', 'uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z', 'uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Stream:
    def read(self): return b''
class Tests(unittest.TestCase):
    def run_receive(self, *, rc=0, observed=None, runner=None, **kw):
        calls=[]
        def fake_run(cmd, **options):
            calls.append((cmd,options))
            return SimpleNamespace(returncode=rc)
        inspect=lambda stamp: observed if observed is not None else {'flags':'readonly','received_uuid':B['uuid']}
        result=mod.receive_prepared_binary_stream(A,B,input_stream=Stream(),runner=runner or fake_run,inspect_received=inspect,**kw)
        return result,calls
    def test_success_is_only_local(self):
        result,calls=self.run_receive()
        self.assertIs(result,True)
        self.assertEqual(calls[0][0],['sudo','-n',mod.ENDPOINT,'--role','receiver','--snapshot',B['timestamp']])
        self.assertEqual(calls[0][1]['timeout'],1800)
        self.assertNotIn('stdout',calls[0][1])
    def test_nonzero_refused(self):
        with self.assertRaisesRegex(RuntimeError,'journal retained'):
            self.run_receive(rc=1)
    def test_timeout_refused(self):
        def timed_out(cmd,**kwargs): raise subprocess.TimeoutExpired(cmd,kwargs['timeout'])
        with self.assertRaisesRegex(RuntimeError,'manual reconciliation'):
            self.run_receive(runner=timed_out)
    def test_mismatched_identity_refused(self):
        with self.assertRaisesRegex(RuntimeError,'journal retained'):
            self.run_receive(observed={'flags':'readonly','received_uuid':A['uuid']})
    def test_not_readonly_refused(self):
        with self.assertRaises(RuntimeError):
            self.run_receive(observed={'flags':'none','received_uuid':B['uuid']})
    def test_no_invalid_deadline(self):
        with self.assertRaises(RuntimeError): self.run_receive(timeout_seconds=0)
    def test_no_unsafe_endpoint(self):
        with self.assertRaises(RuntimeError): self.run_receive(endpoint='/bin/bash')
    def test_no_public_cli_route(self):
        source=PATH.read_text()
        main=source[source.index('def main():'):]
        self.assertNotIn('receive_prepared_binary_stream(',main)
        self.assertNotIn('receive_prepared_candidate_reserved(',main)
if __name__=='__main__': unittest.main(verbosity=2)
