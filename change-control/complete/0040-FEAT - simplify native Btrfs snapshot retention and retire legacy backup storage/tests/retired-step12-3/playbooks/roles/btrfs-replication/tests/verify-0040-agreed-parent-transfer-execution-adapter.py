#!/usr/bin/python3
"""Isolated no-live-transfer regression for 0040 Integration 04F."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'files'
def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), ROOT / ('btrfs-agreed-parent-' + name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

adapter = load('transfer-execution-adapter')
contract = load('transfer-transport-contract')
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class FakeProcess:
    def __init__(self, code=0, *, source=False):
        self.code = code
        self.stdout = FakePipe() if source else None
    def wait(self): return self.code
    def poll(self): return self.code

class FakePipe:
    def close(self): pass

class Tests(unittest.TestCase):
    def setUp(self): self.commands = contract.exact_incremental_commands(A, B)
    def test_exact_commands(self):
        s,r=adapter.exact_argv(self.commands,A,B)
        self.assertIn('incremental-source',s)
        self.assertEqual(r[-1], '--accept')
    def test_disabled(self):
        with self.assertRaises(adapter.TransferExecutionRefused):
            adapter.transfer_once(self.commands,A,B,push_lock_held=True)
    def test_requires_lock(self):
        with self.assertRaises(adapter.TransferExecutionRefused):
            adapter.transfer_once(self.commands,A,B,execution_enabled=True)
    def test_reject_mutating_contract(self):
        self.commands['authorizes_release']=True
        with self.assertRaises(adapter.TransferExecutionRefused): adapter.exact_argv(self.commands,A,B)
    def test_reject_wrong_destination(self):
        self.commands['receiver_accept']=('ssh','other-host')
        with self.assertRaises(adapter.TransferExecutionRefused): adapter.exact_argv(self.commands,A,B)
    def test_success_one_pipeline(self):
        calls=[]
        def popen(argv, **kw):
            calls.append((argv, kw))
            return FakeProcess(source=len(calls)==1)
        result=adapter.transfer_once(self.commands,A,B,push_lock_held=True,execution_enabled=True,popen=popen)
        self.assertEqual(result,{'source_send_exit':0,'receiver_receive_exit':0})
        self.assertEqual(len(calls),2)
        self.assertNotIn('shell',calls[0][1])
        self.assertIsInstance(calls[1][1]['stdin'], FakePipe)
    def test_nonzero_source(self):
        counter=iter([1,0])
        with self.assertRaises(adapter.TransferExecutionRefused):
            adapter.transfer_once(self.commands,A,B,push_lock_held=True,execution_enabled=True,
                popen=lambda argv,**kw:FakeProcess(next(counter),source='stdout' in kw))
    def test_nonzero_receiver(self):
        counter=iter([0,1])
        with self.assertRaises(adapter.TransferExecutionRefused):
            adapter.transfer_once(self.commands,A,B,push_lock_held=True,execution_enabled=True,
                popen=lambda argv,**kw:FakeProcess(next(counter),source='stdout' in kw))
    def test_spawn_failure_no_retry(self):
        calls=[]
        def popen(argv, **kw):
            calls.append(argv)
            if len(calls)==2: raise OSError('failed')
            return FakeProcess(source=True)
        with self.assertRaises(adapter.TransferExecutionRefused):
            adapter.transfer_once(self.commands,A,B,push_lock_held=True,execution_enabled=True,popen=popen)
        self.assertEqual(len(calls),2)
    def test_no_entrypoint(self):
        self.assertFalse(hasattr(adapter,'main'))

if __name__=='__main__': unittest.main(verbosity=2)
