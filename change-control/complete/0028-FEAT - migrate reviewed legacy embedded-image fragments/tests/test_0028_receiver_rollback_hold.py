#!/usr/bin/env python3
"""Offline tests for receiver hold helper; never touches Btrfs."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from unittest import TestCase, main, mock

SCRIPT = Path(__file__).resolve().parents[1] / 'tools/0028-receiver-rollback-hold.py'
spec = importlib.util.spec_from_file_location('receiver_hold_0028', SCRIPT)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class FakeLock:
    def close(self): pass

class FakeManager:
    SnapshotError = RuntimeError
    def __init__(self, holds=None):
        self.holds = holds or {}
        self.wrote = False
    def with_lock(self, *args, **kwargs): return FakeLock()
    def receiver_simple_validate(self, config): return None
    def receiver_simple_identity(self, path):
        return {'Received UUID':'11111111-2222-3333-4444-555555555555'}
    def read_checkpoint_holds(self, config): return dict(self.holds)
    def receiver_simple_plan(self, config):
        return {'holds':list(self.holds)}
    def write_checkpoint_holds(self, config, holds):
        self.holds = holds
        self.wrote = True

class Tests(TestCase):
    def setUp(self):
        self.config = SimpleNamespace(lock_path=Path('/lock'), writer_lock_path=Path('/writer'))
        self.m = FakeManager()
    def test_add_hold_binds_received_uuid(self):
        with mock.patch.object(m, 'runtime', return_value=(self.m,self.config)):
            m.operate('hold','20261124-164500Z')
        self.assertTrue(self.m.wrote)
        self.assertEqual(self.m.holds['20261124-164500Z']['source_uuids']['@data'],
                         '11111111-2222-3333-4444-555555555555')
    def test_verify_absent_refused_without_write(self):
        with mock.patch.object(m, 'runtime', return_value=(self.m,self.config)), self.assertRaises(RuntimeError):
            m.operate('verify','20261124-164500Z')
        self.assertFalse(self.m.wrote)
    def test_verify_existing_hold(self):
        self.m.holds['20261124-164500Z'] = {'source_uuids':{'@data':'11111111-2222-3333-4444-555555555555'},'reason':'rollback'}
        with mock.patch.object(m, 'runtime', return_value=(self.m,self.config)):
            m.operate('verify','20261124-164500Z')
        self.assertFalse(self.m.wrote)
    def test_conflicting_hold_refused(self):
        self.m.holds['20261124-164500Z'] = {'source_uuids':{'@data':'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee'},'reason':'other'}
        with mock.patch.object(m, 'runtime', return_value=(self.m,self.config)), self.assertRaises(RuntimeError):
            m.operate('hold','20261124-164500Z')
        self.assertFalse(self.m.wrote)
    def test_invalid_stamp_refused(self):
        with self.assertRaises(RuntimeError): m.operate('hold','../anything')
    def test_no_snapshot_or_hold_deletion(self):
        s=SCRIPT.read_text()
        for forbidden in ('subvolume delete','hold-release','os.unlink(','shutil.rmtree('):
            self.assertNotIn(forbidden,s)
    def test_runtime_fixed_receiver_paths(self):
        s=SCRIPT.read_text()
        self.assertIn('/etc/btrfs-receiver-checkpoint-holds.json',s)
        self.assertIn("identity['Received UUID']",s)
        self.assertIn('receiver_simple_plan',s)

if __name__ == '__main__': main(verbosity=2)
