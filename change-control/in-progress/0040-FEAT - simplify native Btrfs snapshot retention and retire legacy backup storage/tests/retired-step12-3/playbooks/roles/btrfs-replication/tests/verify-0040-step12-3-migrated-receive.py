#!/usr/bin/env python3
"""Offline integration tests: real journal and lock sequencing, fake Btrfs runner."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import types
import unittest
from unittest.mock import patch

FILES = Path(__file__).resolve().parent.parent / 'files'
def load(name):
    path=FILES/name
    spec=importlib.util.spec_from_file_location('test_integrated_'+name.replace('-','_').replace('.','_'),path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

receiver=load('btrfs-agreed-parent-receive-core.py')
journal=load('btrfs-agreed-parent-provisional-journal.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        root=Path(self.temp.name)
        self.state=root/'state'; self.state.mkdir()
        self.manager=root/'manager.lock'; self.manager.touch()
        self.writer=self.state/'writer.lock'; self.writer.touch()
        self.patch_state=patch.object(receiver,'STATE',self.state)
        self.patch_lock=patch.object(receiver,'LOCK',self.writer)
        self.patch_manager=patch.object(receiver,'Path',Path)  # no behaviour change
        self.patch_state.start();self.patch_lock.start()
        self.events=[]
    def tearDown(self):
        self.patch_lock.stop();self.patch_state.stop();self.temp.cleanup()
    def run_integrated(self, *, fail=None, returncode=0, received=None):
        events=self.events
        class State:
            def load(self, path):
                events.append('state')
                return {'established':A,'pending':B,'previous':None,'schema':1}
        class Absence:
            def verify(self, a,b,current,*,state):
                events.append('absence')
                if fail=='absence': raise RuntimeError('bad absence')
                return {'destination_absent':True,'receipt_absent':True,'state_changed':False}
        class Endpoint:
            def validate_filesystem(self):
                events.append('endpoint')
                if fail=='endpoint': raise RuntimeError('bad filesystem')
        def parent(*args):
            events.append('parent')
            if fail=='parent': raise RuntimeError('bad parent')
            return {'receiver_verified_under_lock':True,'snapshot':A['timestamp'],'source_uuid':A['uuid']}
        def run(command, *, stdin, timeout, check):
            events.append('receive')
            self.assertTrue((self.state/journal.NAME).is_file())
            self.assertEqual(command[0:3],['sudo','-n',receiver.ENDPOINT])
            if fail=='receive': raise subprocess.TimeoutExpired(command,timeout)
            return types.SimpleNamespace(returncode=returncode)
        def inspect(stamp):
            events.append('inspect')
            return {'flags':'readonly','received_uuid': received or B['uuid']}
        with patch.object(receiver,'Path',lambda v: self.manager if str(v)=='/run/lock/btrfs-snapshot-manager.lock' else Path(v)):
            return receiver.receive_prepared_candidate_integrated(
                A,B,input_stream=types.SimpleNamespace(read=lambda: b''),
                state_module=State(),absence_module=Absence(),endpoint_module=Endpoint(),
                journal_module=journal,manager_lock=self.manager,writer_lock=self.writer,
                state_dir=self.state,verify_parent=parent,runner=run,inspect_received=inspect)
    def test_success_reserves_before_receive_no_final_receipt(self):
        result=self.run_integrated()
        self.assertEqual(result['status'],'receiver-provisional-only')
        self.assertEqual(self.events,['endpoint','state','absence','parent','receive','inspect'])
        self.assertTrue((self.state/journal.NAME).is_file())
        self.assertFalse((self.state/(B['timestamp']+'.json')).exists())
    def test_bad_preflight_prevents_reservation(self):
        for fail in ('endpoint','absence','parent'):
            with self.subTest(fail=fail):
                self.events.clear()
                with self.assertRaises(RuntimeError): self.run_integrated(fail=fail)
                self.assertFalse((self.state/journal.NAME).exists())
                self.assertNotIn('receive',self.events)
    def test_timeout_retains_journal(self):
        with self.assertRaisesRegex(RuntimeError,'timed out'):
            self.run_integrated(fail='receive')
        self.assertTrue((self.state/journal.NAME).exists())
    def test_failed_exit_retains_journal(self):
        with self.assertRaisesRegex(RuntimeError,'receive failed'):
            self.run_integrated(returncode=5)
        self.assertTrue((self.state/journal.NAME).exists())
    def test_wrong_identity_retains_journal(self):
        with self.assertRaisesRegex(RuntimeError,'identity'):
            self.run_integrated(received=A['uuid'])
        self.assertTrue((self.state/journal.NAME).exists())
    def test_duplicate_refused_before_receive(self):
        self.run_integrated()
        self.events.clear()
        with self.assertRaises(journal.Refused): self.run_integrated()
        self.assertNotIn('receive',self.events)
    def test_default_parent_verifier_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError, 'not configured'):
            receiver.check_protected_parent(A['timestamp'], A['uuid'])
    def test_no_legacy_import(self):
        import inspect
        source=inspect.getsource(receiver)
        self.assertNotIn('import btrfs-native-push-receiver',source)
    def test_not_publicly_exposed(self):
        import inspect
        self.assertFalse(hasattr(receiver, 'main'))
if __name__ == '__main__': unittest.main(verbosity=2)
