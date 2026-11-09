#!/usr/bin/env python3
"""0040 Step 12.3: opt-in durable transaction/scope binding regression."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'files'
def load(name):
    spec=importlib.util.spec_from_file_location('test_'+name.replace('-','_'),ROOT/name)
    mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod);return mod
journal=load('btrfs-agreed-parent-provisional-journal.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Tests(unittest.TestCase):
    def test_scoped_reservation_is_durable_and_bound(self):
        with tempfile.TemporaryDirectory() as td:
            p=journal.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True)
            d=json.loads(p.read_text())
            self.assertEqual(d['scope_unit'],'btrfs-agreed-receive-'+B['timestamp']+'-'+d['nonce'][:16]+'.scope')
            self.assertEqual(d['scope_binding'],'reserved-not-termination-evidence')
            self.assertEqual(p.stat().st_mode&0o777,0o600)
            with self.assertRaises(journal.Refused):
                journal.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True)
    def test_unique_scope_identity(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            x=json.loads(journal.reserve(a,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True).read_text())
            y=json.loads(journal.reserve(b,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True).read_text())
            self.assertNotEqual(x['scope_unit'],y['scope_unit'])
    def test_default_schema_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            d=json.loads(journal.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True).read_text())
            self.assertNotIn('scope_unit',d)
            self.assertNotIn('scope_binding',d)
    def test_no_creation_without_locks(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(journal.Refused):journal.reserve(td,A,B,scoped=True)
            self.assertFalse((Path(td)/journal.NAME).exists())
    def test_not_termination_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            d=json.loads(journal.reserve(td,A,B,manager_lock_held=True,writer_lock_held=True,scoped=True).read_text())
            self.assertNotIn('terminated',d)
            self.assertNotIn('cleanup_authorized',d)
if __name__=='__main__':unittest.main(verbosity=2)
