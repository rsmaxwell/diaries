#!/usr/bin/env python3
"""Read-only nonce-bound staged incident classification regression."""
import importlib.util
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
FILE = BASE / 'files/btrfs-agreed-parent-staged-recovery.py'
spec = importlib.util.spec_from_file_location('stage_recovery', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
P = {'timestamp':'20261102-010000Z','uuid':'11111111-1111-1111-1111-111111111111'}
C = {'timestamp':'20261103-010000Z','uuid':'22222222-2222-2222-2222-222222222222'}
N = 'a'*64
SCOPE = 'btrfs-agreed-receive-'+C['timestamp']+'-'+N[:16]+'.scope'

class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.final=self.root/'@data'
        self.final.mkdir()
        self.patch_root=patch.object(m, 'ROOT', self.root)
        self.patch_final=patch.object(m, 'FINAL', self.final)
        self.patch_root.start();self.patch_final.start()
        self.addCleanup(self.patch_root.stop);self.addCleanup(self.patch_final.stop)
        stat=self.final.stat()
        self.j={'schema':1,'status':'receiving','parent':P,'candidate':C,'nonce':N,
                'scope_unit':SCOPE,'scope_binding':'reserved-not-termination-evidence',
                'receiver_boot_id':'33333333-3333-3333-3333-333333333333',
                'staging':{'directory_dev':stat.st_dev,'directory_ino':stat.st_ino}}
        self.state={'schema':1,'established':P,'pending':C,'previous':None}
        self.fence={'termination_proven':True,'fencing':'receiver-reboot','nonce':N,
                    'scope_unit':SCOPE,'cleanup_authorized':False,'retransmit_authorized':False}
        # The test process may run non-root; simulate the root-owned receiver mount.
        self.real_dir=m._directory
        def fake_dir(path):
            st=self.real_dir(path)
            if path == self.final:
                return SimpleNamespace(st_dev=st.st_dev,st_ino=st.st_ino,st_uid=0)
            return st
        self.patch_dir=patch.object(m,'_directory',fake_dir)
        self.patch_dir.start(); self.addCleanup(self.patch_dir.stop)

    def assess(self, **kw):
        args=dict(state=self.state,receipt_absent=True,previous_boot_fence=self.fence,
                  locks_held=True,root=self.root,final=self.final)
        args.update(kw)
        return m.assess(P,C,self.j,**args)

    def mock_btrfs(self, uuid='44444444-4444-4444-4444-444444444444', received=C['uuid'], flags='readonly'):
        def run(cmd, **kw):
            self.assertEqual(cmd, ['btrfs','subvolume','show','--',str(self.final/('.receive-'+N))])
            return SimpleNamespace(returncode=0,stdout=f'UUID: {uuid}\nReceived UUID: {received}\nFlags: {flags}\n')
        return run

    def test_absent_does_not_authorize_retry(self):
        result=self.assess()
        self.assertEqual(result['status'],'private-stage-absent-unresolved')
        self.assertIs(result['retransmit_authorized'],False)

    def test_complete_still_requires_sender_proof(self):
        (self.final/('.receive-'+N)).mkdir()
        result=self.assess(runner=self.mock_btrfs())
        self.assertEqual(result['status'],'private-stage-complete-awaiting-sender-proof')
        self.assertFalse(result['publication_authorized'])

    def test_incomplete_does_not_authorize_deletion(self):
        (self.final/('.receive-'+N)).mkdir()
        result=self.assess(runner=self.mock_btrfs(received='-',flags='-'))
        self.assertEqual(result['status'],'private-stage-incomplete-manual-recovery')
        self.assertFalse(result['cleanup_authorized'])

    def test_same_boot_or_missing_fence_refused(self):
        with self.assertRaises(m.Refused):
            self.assess(previous_boot_fence=dict(self.fence,termination_proven=False))

    def test_witnessed_missing_staging_refused(self):
        self.j['publication_witness']={'subvolume_uuid':'44444444-4444-4444-4444-444444444444',
                                       'received_uuid':C['uuid']}
        with self.assertRaises(m.Refused):self.assess()

    def test_published_name_refused(self):
        (self.final/C['timestamp']).mkdir()
        with self.assertRaises(m.Refused):self.assess()

    def test_symlink_stage_refused(self):
        (self.final/('.receive-'+N)).symlink_to(self.root)
        with self.assertRaises(m.Refused):self.assess()

    def test_changed_parent_inode_refused(self):
        self.j['staging']['directory_ino']+=1
        with self.assertRaises(m.Refused):self.assess()

    def test_ambiguous_identity_refused(self):
        (self.final/('.receive-'+N)).mkdir()
        with self.assertRaises(m.Refused):
            self.assess(runner=self.mock_btrfs(received=C['uuid'],flags='-'))

    def test_no_sender_supplied_paths_or_deletion(self):
        import inspect
        source=inspect.getsource(m.assess)
        self.assertNotIn('subvolume delete',source)
        self.assertNotIn('unlink(',source)
        self.assertNotIn('rmtree(',source)

    def test_entry_and_installer_wired(self):
        source=(BASE/'files/btrfs-agreed-parent-receiver-entry.py').read_text()
        install=(BASE/'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertIn('--assess-staged-recovery',source)
        self.assertIn("loader('staged-recovery')",source)
        self.assertIn('    - staged-recovery',install)

if __name__=='__main__':
    unittest.main(verbosity=2)
