#!/usr/bin/env python3
"""Receiver stage ownership capture regressions (no Btrfs dataset mutation)."""
import importlib.util
import json
from pathlib import Path
import os
import tempfile
import types
import unittest
from unittest import mock

MODULE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-stage-ownership.py'
spec = importlib.util.spec_from_file_location('stage_ownership', MODULE)
ownership = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ownership)

PARENT = {'timestamp':'20261103-000000Z','uuid':'11111111-1111-1111-1111-111111111111'}
CANDIDATE = {'timestamp':'20261103-010000Z','uuid':'22222222-2222-2222-2222-222222222222'}
NONCE = 'a'*64
BOOT = '33333333-3333-3333-3333-333333333333'
SUBVOL = '44444444-4444-4444-4444-444444444444'

class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root/'state'; self.state.mkdir(mode=0o700)
        self.final = self.root/'final'; self.final.mkdir(mode=0o755)
        m = self.final.lstat()
        self.journal = {'schema':1,'status':'receiving','parent':PARENT,'candidate':CANDIDATE,
                        'nonce':NONCE,'scope_unit':'btrfs-agreed-receive-'+CANDIDATE['timestamp']+'-'+NONCE[:16]+'.scope',
                        'scope_binding':'reserved-not-termination-evidence','receiver_boot_id':BOOT,
                        'staging':{'directory_dev':m.st_dev,'directory_ino':m.st_ino}}
        self.journal_path=self.state/ownership.JOURNAL
        self.journal_path.write_text(json.dumps(self.journal))
        self.journal_path.chmod(0o600)
        self.root_patch = mock.patch.object(ownership.os, 'geteuid', return_value=0)
        self.root_patch.start()
        self.addCleanup(self.root_patch.stop)
        # stat ownership is root-only in production; test only mocks uid.
        self.lstat = Path.lstat
        def root_lstat(path):
            result = self.lstat(path)
            return types.SimpleNamespace(**{k:getattr(result,k) for k in
                 ('st_mode','st_nlink','st_dev','st_ino')}, **{'st_uid':0})
        self.stat_patch=mock.patch.object(ownership.Path,'lstat',root_lstat)
        self.stat_patch.start()
        self.addCleanup(self.stat_patch.stop)
        self.stage=self.final/('.receive-'+NONCE)
    def runner(self, argv, **kwargs):
        return types.SimpleNamespace(returncode=0,
                stdout='UUID: '+SUBVOL+'\nReceived UUID: -\nFlags: -\n')
    def capture(self, **kwargs):
        return ownership.capture(CANDIDATE, NONCE, state_dir=self.state,
             final_dir=self.final, locks_held=True, runner=self.runner,
             boot_id_reader=lambda:BOOT, **kwargs)
    def test_missing_stage_never_creates_witness(self):
        self.assertFalse(self.capture())
        self.assertFalse(ownership.sidecar_path(self.state,NONCE).exists())
    def test_created_subvolume_durable_identity(self):
        self.stage.mkdir()
        self.assertTrue(self.capture())
        record=ownership.load(CANDIDATE, NONCE,state_dir=self.state)
        self.assertEqual(record['subvolume_uuid'], SUBVOL)
        self.assertEqual(record['stage_ino'], self.stage.lstat().st_ino)
        self.assertTrue(self.capture())
    def test_existing_witness_mismatch_refused(self):
        self.stage.mkdir(); self.capture()
        old=self.runner
        self.runner=lambda *a,**k:types.SimpleNamespace(returncode=0,
            stdout='UUID: 55555555-5555-5555-5555-555555555555\nReceived UUID: -\nFlags: -\n')
        with self.assertRaises(ownership.Refused):
            self.capture()
        self.runner=old
    def test_wrong_boot_refused(self):
        self.stage.mkdir()
        with self.assertRaises(ownership.Refused):
            ownership.capture(CANDIDATE,NONCE,state_dir=self.state,
               final_dir=self.final,locks_held=True,runner=self.runner,
               boot_id_reader=lambda:'66666666-6666-6666-6666-666666666666')
    def test_symlink_refused(self):
        self.stage.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(ownership.Refused):
            self.capture()
    def test_without_locks_refused(self):
        self.stage.mkdir()
        with self.assertRaises(ownership.Refused):
            ownership.capture(CANDIDATE,NONCE,state_dir=self.state,
                final_dir=self.final,locks_held=False,runner=self.runner)
    def test_published_refused(self):
        self.stage.mkdir();(self.final/CANDIDATE['timestamp']).mkdir()
        with self.assertRaises(ownership.Refused):
            self.capture()
    def test_no_stream_files_mutated(self):
        self.stage.mkdir()
        self.capture()
        self.assertTrue(self.stage.exists())
        self.assertFalse((self.final/CANDIDATE['timestamp']).exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
