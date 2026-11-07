#!/usr/bin/env python3
import ast
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1] / 'files'
def load(name):
    spec = importlib.util.spec_from_file_location('staged_'+name, ROOT/name)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
class Tests(unittest.TestCase):
    def test_endpoint_has_explicit_role(self):
        text = (ROOT/'btrfs-native-endpoint.py').read_text()
        self.assertIn("'staged-receiver'",text)
        self.assertIn("receive_staged(args.snapshot, args.transaction_nonce)",text)
        self.assertIn("elif args.role == 'receiver':\n        receive(args.snapshot)",text)
    def test_endpoint_requires_journal_and_identity(self):
        text=(ROOT/'btrfs-native-endpoint.py').read_text()
        for marker in ('record.get(\'nonce\') == nonce', "record.get('status') == 'receiving'", "binding['directory_dev']", "binding['directory_ino']", "os.execvp('btrfs'", 'Candidate already exists'):
            self.assertIn(marker,text)
    def test_binding_refuses_missing_locks(self):
        mod=load('btrfs-agreed-parent-provisional-journal.py')
        with self.assertRaises(mod.Refused):
            mod.bind_staging('/x',{},'a'*64,{},manager_lock_held=False)
    def test_binding_writes_identity_and_refuses_rebind(self):
        mod=load('btrfs-agreed-parent-provisional-journal.py')
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/mod.NAME
            candidate={'timestamp':'20261101-140039Z','uuid':'69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'}
            nonce='a'*64
            path.write_text(json.dumps({'schema':1,'status':'receiving','nonce':nonce,'candidate':candidate}))
            mod.bind_staging(path,candidate,nonce,{'directory_dev':123,'directory_ino':456},manager_lock_held=True,writer_lock_held=True)
            self.assertEqual(json.loads(path.read_text())['staging'],{'directory_dev':123,'directory_ino':456})
            with self.assertRaises(mod.Refused):
                mod.bind_staging(path,candidate,nonce,{'directory_dev':123,'directory_ino':456},manager_lock_held=True,writer_lock_held=True)
    def test_compile(self):
        for name in ('btrfs-native-endpoint.py','btrfs-agreed-parent-provisional-journal.py'):
            ast.parse((ROOT/name).read_text())
if __name__=='__main__': unittest.main(verbosity=2)
