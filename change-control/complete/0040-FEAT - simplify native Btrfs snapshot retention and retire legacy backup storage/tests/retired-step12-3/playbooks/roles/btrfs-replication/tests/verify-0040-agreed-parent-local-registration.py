#!/usr/bin/python3
import importlib.util
import os
from pathlib import Path
import socket
import stat
import tempfile
import threading
import unittest

P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-local-registration.py'
spec = importlib.util.spec_from_file_location('local_registration', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'private'
        self.root.mkdir(mode=0o700)
        self.p = self.root / 'session.sock'
    def listen(self):
        return m.temporary_listener(self.p, directory=self.root, locks_held=True, owner_uid=os.geteuid())
    def test_requires_locks(self):
        with self.assertRaises(m.RegistrationRefused):
            with m.temporary_listener(self.p,directory=self.root,owner_uid=os.geteuid()): pass
    def test_reject_bad_directory(self):
        self.root.chmod(0o755)
        with self.assertRaises(m.RegistrationRefused):
            with self.listen(): pass
    def test_reject_existing_path(self):
        self.p.write_text('preserve')
        with self.assertRaises(m.RegistrationRefused):
            with self.listen(): pass
        self.assertEqual(self.p.read_text(),'preserve')
    def test_reject_symlink(self):
        self.p.symlink_to(self.root / 'missing')
        with self.assertRaises(m.RegistrationRefused):
            with self.listen(): pass
        self.assertTrue(self.p.is_symlink())
    def test_lifecycle(self):
        with self.listen():
            self.assertTrue(stat.S_ISSOCK(self.p.stat().st_mode))
            self.assertEqual(stat.S_IMODE(self.p.stat().st_mode),0o600)
        self.assertFalse(self.p.exists())
    def test_exception_cleanup(self):
        with self.assertRaises(ValueError):
            with self.listen(): raise ValueError('test')
        self.assertFalse(self.p.exists())
    def test_real_kernel_peer(self):
        with self.listen() as server:
            def client():
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c: c.connect(str(self.p))
            t = threading.Thread(target=client)
            t.start()
            result=m.review_one_connection(server,expected_uid=os.geteuid())
            t.join()
        self.assertEqual(result['status'],'local-peer-review')
        self.assertFalse(result['ssh_identity_verified'])
        self.assertEqual(result['channels_registered'],[])
    def test_wrong_uid(self):
        with self.listen() as server:
            def client():
                with socket.socket(socket.AF_UNIX,socket.SOCK_STREAM) as c: c.connect(str(self.p))
            t=threading.Thread(target=client); t.start()
            with self.assertRaises(RuntimeError):
                m.review_one_connection(server,expected_uid=os.geteuid()+1)
            t.join()
    def test_reject_timeout(self):
        with self.listen() as server:
            with self.assertRaises(m.RegistrationRefused):
                m.review_one_connection(server,expected_uid=os.geteuid(),timeout=0.01)
    def test_invalid_deadline(self):
        with self.listen() as server:
            with self.assertRaises(m.RegistrationRefused):
                m.review_one_connection(server,expected_uid=os.geteuid(),timeout=True)
    def test_no_cli_or_transfer(self):
        s=P.read_text()
        self.assertNotIn('subprocess',s)
        self.assertNotIn('if __name__',s)
        self.assertNotIn('btrfs receive',s.lower())

if __name__=='__main__': unittest.main(verbosity=2)
