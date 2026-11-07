#!/usr/bin/env python3
"""Durable witness file test; requires root, uses only disposable directories."""
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-provisional-journal.py'
spec = importlib.util.spec_from_file_location('journal', MODULE)
journal = importlib.util.module_from_spec(spec); spec.loader.exec_module(journal)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE = 'a' * 64
BOOT = 'e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'
WITNESS = {'subvolume_uuid':'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb', 'received_uuid':B['uuid']}

class Tests(unittest.TestCase):
    def setUp(self):
        if os.geteuid() != 0:
            self.skipTest('run as root using sudo -n; production journal is root owned')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / journal.NAME
        self.data = {'schema':1,'status':'receiving','parent':A,'candidate':B,
            'nonce':NONCE,'scope_unit':'btrfs-agreed-receive-'+B['timestamp']+'-'+NONCE[:16]+'.scope',
            'scope_binding':'reserved-not-termination-evidence','receiver_boot_id':BOOT,
            'staging':{'directory_dev':11,'directory_ino':234}}
        self.path.write_text(json.dumps(self.data)+'\n');self.path.chmod(0o600)
    def save(self, witness=WITNESS, locked=True):
        return journal.record_publication_witness(self.path,A,B,NONCE,witness,
            manager_lock_held=locked,writer_lock_held=locked)
    def test_atomic_witness_persistence(self):
        self.save()
        self.assertEqual(json.loads(self.path.read_text())['publication_witness'],WITNESS)
        self.assertEqual(self.path.stat().st_mode & 0o777,0o600)
    def test_no_rebind(self):
        self.save()
        with self.assertRaises(journal.Refused):self.save()
    def test_no_unauthorised_witness(self):
        with self.assertRaises(journal.Refused):self.save(locked=False)
        self.assertEqual(json.loads(self.path.read_text()),self.data)
    def test_wrong_uuid_refused(self):
        with self.assertRaises(journal.Refused):
            self.save({'subvolume_uuid':WITNESS['subvolume_uuid'],'received_uuid':A['uuid']})
    def test_changed_pending_refused(self):
        self.data['candidate']=A
        self.path.write_text(json.dumps(self.data)); self.path.chmod(0o600)
        with self.assertRaises(journal.Refused):self.save()

if __name__=='__main__':unittest.main(verbosity=2)
