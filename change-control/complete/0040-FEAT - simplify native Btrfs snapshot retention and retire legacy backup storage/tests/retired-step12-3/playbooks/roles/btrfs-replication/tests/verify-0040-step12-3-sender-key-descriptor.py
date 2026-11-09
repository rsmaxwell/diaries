#!/usr/bin/env python3
"""Disposable, nonproduction regression of sender key descriptor handling."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-proof-handoff.py'
spec = importlib.util.spec_from_file_location('key_descriptor', P)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class Tests(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.path = Path(self.t.name) / 'sender.key'
        self.path.write_bytes(b'A' * 32)
        self.path.chmod(0o600)
        self.p = patch.object(mod, 'KEY', self.path)
        self.p.start()
        self.addCleanup(self.p.stop)
        self.root = patch.object(mod.os, 'geteuid', return_value=0)
        self.root.start()
        self.addCleanup(self.root.stop)
    def test_valid_descriptor(self):
        # test owner may not be root in disposable container: spoof only fstat uid
        real = mod.os.fstat
        class Info:
            def __init__(self, x): self.st_mode=x.st_mode; self.st_uid=0; self.st_nlink=x.st_nlink
        with patch.object(mod.os, 'fstat', side_effect=lambda fd: Info(real(fd))):
            self.assertEqual(mod.read_sender_key(self.path), b'A'*32)
    def test_symlink_refused(self):
        target = Path(self.t.name) / 'target'
        target.write_bytes(b'A'*32)
        self.path.unlink()
        self.path.symlink_to(target)
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
    def test_nonroot_refused(self):
        with patch.object(mod.os, 'geteuid', return_value=1000):
            with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
    def test_wrong_path_refused(self):
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(Path(self.t.name)/'wrong')
    def test_world_readable_refused(self):
        self.path.chmod(0o644)
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
    def test_wrong_length_refused(self):
        self.path.write_bytes(b'A'*33)
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
    def test_invalid_alphabet_refused(self):
        self.path.write_bytes(b'+'*32)
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
    def test_directory_refused(self):
        self.path.unlink()
        self.path.mkdir()
        with self.assertRaises(mod.HandoffRefused): mod.read_sender_key(self.path)
if __name__=='__main__': unittest.main(verbosity=2)
