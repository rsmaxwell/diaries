#!/usr/bin/env python3
"""04xx receiver reserve-before-receive; no live streams."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent.parent / 'files'
def load(name):
    path=HERE/name
    spec=importlib.util.spec_from_file_location('test_'+name.replace('-','_').replace('.','_'),path)
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod
receiver=load('btrfs-native-push-receiver.py')
journal=load('btrfs-agreed-parent-provisional-journal.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        root=Path(self.tmp.name)
        self.manager=root/'manager.lock';self.manager.touch()
        self.writer=root/'writer.lock';self.writer.touch()
        self.state=root/'state';self.state.mkdir()
    def tearDown(self): self.tmp.cleanup()
    def execute(self, pre, run):
        return receiver.receive_prepared_candidate_reserved(A,B,
            manager_lock=self.manager,writer_lock=self.writer,state_dir=self.state,
            verify_prepared=pre,receive_stream=run,journal_module=journal)
    def marker(self): return self.state/journal.NAME
    def test_reserve_precedes_receive_and_remains(self):
        calls=[]
        def pre(*_): calls.append('pre');return True
        def run(*_):
            calls.append('receive');self.assertTrue(self.marker().is_file());return True
        result=self.execute(pre,run)
        self.assertEqual(calls,['pre','receive'])
        self.assertFalse(result['receipt_committed'])
        self.assertTrue(self.marker().is_file())
    def test_preflight_failure_never_reserves_or_receives(self):
        with self.assertRaises(RuntimeError):
            self.execute(lambda *_: False,lambda *_:self.fail('receive invoked'))
        self.assertFalse(self.marker().exists())
    def test_receive_failure_keeps_marker(self):
        def fail(*_):raise RuntimeError('injected interruption')
        with self.assertRaisesRegex(RuntimeError,'interruption'):
            self.execute(lambda *_:True,fail)
        self.assertTrue(self.marker().is_file())
    def test_second_attempt_refused(self):
        self.execute(lambda *_:True,lambda *_:True)
        with self.assertRaises(journal.Refused):
            self.execute(lambda *_:True,lambda *_:self.fail('double receive'))
    def test_incomplete_result_refused_and_preserved(self):
        with self.assertRaisesRegex(RuntimeError,'incomplete'):
            self.execute(lambda *_:True,lambda *_:False)
        self.assertTrue(self.marker().is_file())
    def test_public_cli_does_not_route_new_transaction(self):
        import inspect
        main=inspect.getsource(receiver.main)
        self.assertNotIn('receive_prepared_candidate_reserved(',main)

if __name__=='__main__':unittest.main(verbosity=2)
