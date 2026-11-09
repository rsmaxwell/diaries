#!/usr/bin/env python3
"""Disposable-only tests of the real receiver finalisation storage adapter."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

source = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-finalisation-storage.py'
spec = importlib.util.spec_from_file_location('finalstorage', source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STAMP = '20261030-170009Z'

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.dir = Path(self.tmp.name)
        (self.dir / '.agreed-parent.json').write_text('{"schema":1}')
        (self.dir / m.JOURNAL).write_text('{"status":"receiving"}')
        self.receipt = {'schema':1,'snapshot':STAMP,'verified':True}

    def test_existing_readers(self):
        self.assertEqual(m.read_state(self.dir), {'schema':1})
        self.assertEqual(m.read_journal(self.dir), {'status':'receiving'})

    def test_exclusive_durable_commit(self):
        self.assertTrue(m.receipt_absent(STAMP,self.dir))
        path=m.commit_receipt(STAMP,self.receipt,directory=self.dir,locks_held=True)
        self.assertEqual(json.loads(path.read_text()),self.receipt)
        self.assertFalse(m.receipt_absent(STAMP,self.dir))
        with self.assertRaises(FileExistsError):
            m.commit_receipt(STAMP,self.receipt,directory=self.dir,locks_held=True)
        self.assertEqual(json.loads(path.read_text()),self.receipt)

    def test_lock_required(self):
        with self.assertRaises(m.StorageRefused):
            m.commit_receipt(STAMP,self.receipt,directory=self.dir)
        self.assertTrue(m.receipt_absent(STAMP,self.dir))

    def test_dangling_receipt_symlink_not_absent(self):
        (self.dir/(STAMP+'.json')).symlink_to(self.dir/'missing')
        self.assertFalse(m.receipt_absent(STAMP,self.dir))
        with self.assertRaises(FileExistsError):
            m.commit_receipt(STAMP,self.receipt,directory=self.dir,locks_held=True)

    def test_symlinked_journal_rejected(self):
        (self.dir/m.JOURNAL).unlink()
        (self.dir/m.JOURNAL).symlink_to(self.dir/'.agreed-parent.json')
        with self.assertRaises(m.StorageRefused):m.read_journal(self.dir)

    def test_symlinked_state_directory_rejected(self):
        link=self.dir/'link';link.symlink_to(self.dir,target_is_directory=True)
        with self.assertRaises(m.StorageRefused):m.read_state(link)

    def test_wrong_receipt_identity_rejected(self):
        with self.assertRaises(m.StorageRefused):
            m.commit_receipt(STAMP,{'snapshot':'other'},directory=self.dir,locks_held=True)

    def test_receipt_path_is_fixed(self):
        with self.assertRaises(m.StorageRefused):m.receipt_absent('../escape',self.dir)

    def test_durable_journal_untouched(self):
        before=(self.dir/m.JOURNAL).read_bytes()
        m.commit_receipt(STAMP,self.receipt,directory=self.dir,locks_held=True)
        self.assertEqual((self.dir/m.JOURNAL).read_bytes(),before)

if __name__ == '__main__':unittest.main(verbosity=2)
