#!/usr/bin/env python3
"""Read-only published-absence checks; run as root with disposable directories."""
import importlib.util
from pathlib import Path
import os
import tempfile
import unittest

FILES = Path(__file__).resolve().parents[1] / 'files'
spec = importlib.util.spec_from_file_location('staging_storage', FILES / 'btrfs-agreed-parent-staging-storage.py')
storage = importlib.util.module_from_spec(spec)
spec.loader.exec_module(storage)
STAMP = '20261101-140039Z'


class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / '@data').mkdir()
        self.old = (storage.ROOT, storage.FINAL)
        storage.ROOT = self.root
        storage.FINAL = self.root / '@data'
        self.addCleanup(self.restore)

    def restore(self):
        storage.ROOT, storage.FINAL = self.old

    def test_absent(self):
        self.assertTrue(storage.published_absent(STAMP, locks_held=True))

    def test_existing_final(self):
        (storage.FINAL / STAMP).mkdir()
        self.assertFalse(storage.published_absent(STAMP, locks_held=True))

    def test_symlink_is_not_absent(self):
        (storage.FINAL / STAMP).symlink_to(self.root / 'missing')
        self.assertFalse(storage.published_absent(STAMP, locks_held=True))

    def test_requires_locks(self):
        with self.assertRaises(storage.Refused):
            storage.published_absent(STAMP)

    def test_invalid_stamp(self):
        with self.assertRaises(storage.Refused):
            storage.published_absent('../other', locks_held=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
