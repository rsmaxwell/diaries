#!/usr/bin/env python3
"""Fail-closed no-delete staging storage regression."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

MODULE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-staging-storage.py'
spec = importlib.util.spec_from_file_location('staging_storage', MODULE)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)

class Cases(unittest.TestCase):
    def test_invalid_nonce_refuses(self):
        with self.assertRaises(s.Refused): s.reserve('20261101-140039Z','../oops',locks_held=True)
    def test_invalid_stamp_refuses(self):
        with self.assertRaises(s.Refused): s.reserve('../oops','a'*64,locks_held=True)
    def test_locks_required(self):
        with self.assertRaises(s.Refused): s.reserve('20261101-140039Z','a'*64)
    def test_publish_no_authority(self):
        with self.assertRaises(s.Refused): s.publish('20261101-140039Z','a'*64,directory_dev=1,directory_ino=2)
    def test_no_delete(self):
        source=MODULE.read_text()
        self.assertNotIn('subvolume delete',source)
        self.assertNotIn('shutil.rmtree',source)
    def test_no_cli(self):
        self.assertFalse(hasattr(s,'main'))
if __name__ == '__main__': unittest.main(verbosity=2)
