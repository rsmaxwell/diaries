#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-session-proof.py'
spec = importlib.util.spec_from_file_location('sender_proof', path)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
KEY = b'x' * 32
NONCE = '1' * 64


def proof(**kwargs):
    args = dict(key=KEY, send_exit=0, ssh_exit=0, receiver_exit=0)
    args.update(kwargs)
    return m.create_proof(A, B, NONCE, **args)


class Tests(unittest.TestCase):
    def test_success(self):
        self.assertEqual(m.verify_proof(proof(), A, B, NONCE, key=KEY)['authenticated_session'], True)

    def test_sender_failure(self):
        with self.assertRaises(m.ProofRefused): proof(send_exit=1)

    def test_ssh_failure(self):
        with self.assertRaises(m.ProofRefused): proof(ssh_exit=1)

    def test_receiver_failure(self):
        with self.assertRaises(m.ProofRefused): proof(receiver_exit=1)

    def test_boolean_exit(self):
        with self.assertRaises(m.ProofRefused): proof(send_exit=False)

    def test_wrong_session(self):
        with self.assertRaises(m.ProofRefused): m.verify_proof(proof(), A, B, '2'*64, key=KEY)

    def test_wrong_key(self):
        with self.assertRaises(m.ProofRefused): m.verify_proof(proof(), A, B, NONCE, key=b'y'*32)

    def test_tamper(self):
        p = proof(); p['payload']['ssh_exit'] = 1
        with self.assertRaises(m.ProofRefused): m.verify_proof(p, A, B, NONCE, key=KEY)

    def test_changed_candidate(self):
        modified = dict(B, uuid='f'*36)
        with self.assertRaises(m.ProofRefused): m.verify_proof(proof(), A, modified, NONCE, key=KEY)

    def test_no_key(self):
        with self.assertRaises(m.ProofRefused): proof(key=b'')

    def test_no_cli(self):
        self.assertNotIn('def main(', path.read_text())


if __name__ == '__main__':
    unittest.main(verbosity=2)
