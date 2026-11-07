#!/usr/bin/env python3
"""Disposable same-parent publication tests; no Btrfs operations."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-staging-storage.py'
spec = importlib.util.spec_from_file_location('staging_private', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STAMP = '20261103-010000Z'
NONCE = 'c' * 64

class Cases(unittest.TestCase):
    def setUp(self):
        if os.geteuid() != 0:
            self.skipTest('requires root-owned disposable publication directory')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.old = m.ROOT, m.FINAL
        m.ROOT = Path(self.tmp.name)
        m.FINAL = m.ROOT / '@data'
        m.FINAL.mkdir()
        self.addCleanup(self.restore)
    def restore(self): m.ROOT, m.FINAL = self.old
    def reserve(self): return m.reserve(STAMP, NONCE, locks_held=True)
    def publish(self, evidence, **changes):
        return m.publish(STAMP, NONCE, directory_dev=evidence['directory_dev'],
            directory_ino=evidence['directory_ino'], locks_held=True,
            verified_receive=True, sender_authenticated=True,
            btrfs_identity_verified=True, **changes)
    def test_same_parent_reservation(self):
        record = self.reserve()
        self.assertEqual(Path(record['staged_subvolume']).parent, m.FINAL)
        self.assertEqual(Path(record['published_subvolume']).parent, m.FINAL)
        self.assertFalse(Path(record['staged_subvolume']).exists())
    def test_private_publish_and_duplicate_refusal(self):
        record = self.reserve()
        stage = Path(record['staged_subvolume'])
        stage.mkdir()
        result = self.publish(record)
        self.assertEqual(result['status'], 'published-awaiting-receipt')
        self.assertFalse(stage.exists())
        self.assertTrue(Path(record['published_subvolume']).is_dir())
        with self.assertRaises(m.Refused): self.publish(record)
    def test_no_overwrite(self):
        record = self.reserve()
        Path(record['staged_subvolume']).mkdir()
        Path(record['published_subvolume']).mkdir()
        with self.assertRaises(m.Refused): self.publish(record)
        self.assertTrue(Path(record['staged_subvolume']).exists())
    def test_wrong_identity_refuses(self):
        record = self.reserve()
        Path(record['staged_subvolume']).mkdir()
        record['directory_ino'] += 1
        with self.assertRaises(m.Refused): self.publish(record)
    def test_untrusted_flags_refuse(self):
        record = self.reserve()
        Path(record['staged_subvolume']).mkdir()
        with self.assertRaises(m.Refused):
            m.publish(STAMP, NONCE, directory_dev=record['directory_dev'],
                      directory_ino=record['directory_ino'], locks_held=True)
    def test_duplicate_nonce_refused(self):
        record = self.reserve()
        Path(record['staged_subvolume']).mkdir()
        with self.assertRaises(m.Refused): self.reserve()

if __name__ == '__main__': unittest.main(verbosity=2)
