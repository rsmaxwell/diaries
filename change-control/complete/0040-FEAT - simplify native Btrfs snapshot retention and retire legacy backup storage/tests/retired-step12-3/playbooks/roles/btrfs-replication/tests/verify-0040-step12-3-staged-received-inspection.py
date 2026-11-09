#!/usr/bin/env python3
"""Read-only staged Btrfs inspection regression (root-run disposable paths)."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock

SOURCE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-receive-core.py'
spec = importlib.util.spec_from_file_location('receive_core', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
STAMP = '20261102-180000Z'
UUID = 'a9b78fb9-4da6-cf4f-b242-13909f574193'
NONCE = 'b' * 64
CANDIDATE = {'timestamp': STAMP, 'uuid': UUID}

class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.oldroot, self.oldstate = mod.RECEIVER_ROOT, mod.STATE
        mod.RECEIVER_ROOT, mod.STATE = self.root, self.root / '.replication-state'
        self.addCleanup(self.restore)
        (self.root / '@data').mkdir()
        self.txn = self.root / '@data'
        self.stage = self.txn / ('.receive-' + NONCE)
        self.stage.mkdir()
        mod.STATE.mkdir()
        statinfo = self.txn.stat()
        self.journal = mod.STATE / '.agreed-parent-transfer-pending.json'
        self.journal.write_text(json.dumps({'schema': 1, 'status': 'receiving', 'nonce': NONCE,
          'candidate': CANDIDATE, 'staging': {'directory_dev': statinfo.st_dev, 'directory_ino': statinfo.st_ino}}))
        os.chmod(self.journal, 0o600)
        self.runner = Mock(return_value=Mock(returncode=0, stdout=f'UUID: {UUID}\nReceived UUID: {UUID}\nFlags: readonly\n'))

    def restore(self):
        mod.RECEIVER_ROOT, mod.STATE = self.oldroot, self.oldstate

    def inspect(self):
        return mod.inspect_staged_received(CANDIDATE, NONCE, state_dir=mod.STATE, runner=self.runner)

    def test_verified_is_evidence_only(self):
        if os.geteuid() != 0: self.skipTest('requires root-owned disposable staging directory')
        out = self.inspect()
        self.assertEqual(out['status'], 'staged-received-verified')
        self.assertFalse(out['publication_authorized'])
        self.assertFalse(out['cleanup_authorized'])
        self.runner.assert_called_once()

    def test_wrong_nonce_fails_closed(self):
        with self.assertRaises(RuntimeError):
            mod.inspect_staged_received(CANDIDATE, 'x'*64, state_dir=mod.STATE, runner=self.runner)

    def test_wrong_received_uuid_fails_closed(self):
        if os.geteuid() != 0: self.skipTest('requires root-owned disposable staging directory')
        self.runner.return_value.stdout = f'UUID: {UUID}\nReceived UUID: 00000000-0000-0000-0000-000000000000\nFlags: readonly\n'
        with self.assertRaises(RuntimeError): self.inspect()

    def test_published_candidate_fails_closed(self):
        if os.geteuid() != 0: self.skipTest('requires root-owned disposable staging directory')
        (self.root / '@data' / STAMP).mkdir()
        with self.assertRaises(RuntimeError): self.inspect()

    def test_staging_identity_mismatch(self):
        if os.geteuid() != 0: self.skipTest('requires root-owned disposable staging directory')
        info = json.loads(self.journal.read_text())
        info['staging']['directory_ino'] += 1
        self.journal.write_text(json.dumps(info))
        with self.assertRaises(RuntimeError): self.inspect()

if __name__ == '__main__': unittest.main(verbosity=2)
