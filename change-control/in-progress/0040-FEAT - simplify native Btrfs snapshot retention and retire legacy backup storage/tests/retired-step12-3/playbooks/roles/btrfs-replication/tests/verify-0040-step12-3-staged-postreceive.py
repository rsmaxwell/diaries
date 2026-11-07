#!/usr/bin/env python3
"""Post-receive staged inspection dispatch; disposable root-owned fixtures only."""
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

SOURCE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-receive-core.py'
spec = importlib.util.spec_from_file_location('receive_core_staged', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
STAMP = '20261102-180000Z'
PARENT = {'timestamp':'20261101-180000Z', 'uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
CANDIDATE = {'timestamp':STAMP, 'uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE = 'b'*64
SCOPE = 'btrfs-agreed-receive-20261102-180000Z.scope'

class Cases(unittest.TestCase):
    def setUp(self):
        if os.geteuid() != 0:
            self.skipTest('requires root for disposable root-owned staging directory')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.oldroot, self.oldstate = mod.RECEIVER_ROOT, mod.STATE
        mod.RECEIVER_ROOT, mod.STATE = self.root, self.root / '.replication-state'
        self.addCleanup(self.restore)
        (self.root / '@data').mkdir()
        txn = self.root / '@data'
        (txn / ('.receive-' + NONCE)).mkdir()
        mod.STATE.mkdir()
        st = txn.stat()
        journal = mod.STATE / '.agreed-parent-transfer-pending.json'
        journal.write_text(json.dumps({'schema':1,'status':'receiving','candidate':CANDIDATE,
            'nonce':NONCE,'staging':{'directory_dev':st.st_dev,'directory_ino':st.st_ino}}))
        journal.chmod(0o600)
    def restore(self):
        mod.RECEIVER_ROOT, mod.STATE = self.oldroot, self.oldstate
    def execute(self, inspect_stdout):
        def fake_btrfs(cmd, **kwargs):
            return Mock(returncode=0, stdout=inspect_stdout)
        def fake_completed(cmd, **kwargs):
            self.assertIn('staged-receiver', cmd)
            self.assertIn(NONCE, cmd)
            return Mock(returncode=0)
        with patch.object(mod, 'run_bounded_receive_group', side_effect=fake_completed):
            # The real inspector uses module subprocess.run; never run a real btrfs command.
            with patch.object(mod.subprocess, 'run', side_effect=fake_btrfs):
                return mod.receive_prepared_binary_stream(PARENT, CANDIDATE,
                    input_stream=io.BytesIO(b'dummy'), lock_fds=(10,11),
                    scope_unit=SCOPE, scope_query=lambda name: {},
                    staging_nonce=NONCE)
    def test_staged_verify_returns_local_only(self):
        out = self.execute(f'UUID: {PARENT["uuid"]}\nReceived UUID: {CANDIDATE["uuid"]}\nFlags: readonly\n')
        self.assertIs(out, True)
    def test_bad_btrfs_identity_refuses(self):
        with self.assertRaisesRegex(RuntimeError, 'Staged Btrfs received identity'):
            self.execute(f'UUID: {PARENT["uuid"]}\nReceived UUID: {PARENT["uuid"]}\nFlags: readonly\n')
    def test_untrusted_inspector_refuses(self):
        with patch.object(mod, 'run_bounded_receive_group', return_value=Mock(returncode=0)):
            with self.assertRaisesRegex(RuntimeError, 'Untrusted staged Btrfs inspector'):
                mod.receive_prepared_binary_stream(PARENT, CANDIDATE, input_stream=io.BytesIO(),
                    lock_fds=(10,11), scope_unit=SCOPE, scope_query=lambda _: {},
                    staging_nonce=NONCE, staged_inspector=lambda *_: {'status':'staged-received-verified'})

if __name__ == '__main__': unittest.main(verbosity=2)
