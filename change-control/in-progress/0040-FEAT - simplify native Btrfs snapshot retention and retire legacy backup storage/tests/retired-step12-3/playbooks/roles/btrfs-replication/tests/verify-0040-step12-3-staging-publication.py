#!/usr/bin/env python3
"""Filesystem tests of atomic no-overwrite staging publication (no Btrfs needed)."""
import importlib.util
import tempfile
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-staging-storage.py'
spec = importlib.util.spec_from_file_location('storage', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
STAMP = '20261102-101500Z'
NONCE = 'a' * 64

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        mod.ROOT = Path(self.tmp.name)
        mod.FINAL = mod.ROOT / '@data'
        mod.FINAL.mkdir()

    def prepared(self):
        identity = mod.reserve(STAMP, NONCE, locks_held=True)
        stage = Path(identity['staged_subvolume'])
        stage.mkdir()
        return identity, stage

    def publish(self, identity):
        return mod.publish(STAMP, NONCE, directory_dev=identity['directory_dev'],
                           directory_ino=identity['directory_ino'], locks_held=True,
                           verified_receive=True, sender_authenticated=True,
                           btrfs_identity_verified=True)

    def test_publishes_without_receipt(self):
        identity, stage = self.prepared()
        (stage / 'payload').write_text('example')
        result = self.publish(identity)
        self.assertEqual(result['status'], 'published-awaiting-receipt')
        self.assertFalse(result['receipt_committed'])
        self.assertFalse(result['cleanup_authorized'])
        self.assertFalse(stage.exists())
        self.assertEqual((mod.FINAL / STAMP / 'payload').read_text(), 'example')

    def test_existing_final_never_overwritten(self):
        identity, stage = self.prepared()
        final = mod.FINAL / STAMP
        final.mkdir()
        (final / 'original').write_text('protected')
        with self.assertRaises(mod.Refused):
            self.publish(identity)
        self.assertTrue(stage.is_dir())
        self.assertEqual((final / 'original').read_text(), 'protected')

    def test_missing_authority_refused(self):
        identity, stage = self.prepared()
        with self.assertRaises(mod.Refused):
            mod.publish(STAMP, NONCE, directory_dev=identity['directory_dev'],
                        directory_ino=identity['directory_ino'], locks_held=True)
        self.assertTrue(stage.is_dir())

    def test_wrong_identity_refused(self):
        identity, stage = self.prepared()
        identity['directory_ino'] += 1
        with self.assertRaises(mod.Refused):
            self.publish(identity)
        self.assertTrue(stage.is_dir())

    def test_repeat_publication_refused(self):
        identity, _ = self.prepared()
        self.publish(identity)
        with self.assertRaises(mod.Refused):
            self.publish(identity)
        self.assertTrue((mod.FINAL / STAMP).is_dir())

if __name__ == '__main__':
    unittest.main(verbosity=2)
