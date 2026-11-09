#!/usr/bin/python3
"""Regression tests for 0040 04T dormant kernel peer credential adapter."""
import importlib.util
import os
from pathlib import Path
import socket
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-local-peer.py'
spec = importlib.util.spec_from_file_location('local_peer_04t', FILE)
m = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = m
spec.loader.exec_module(m)


class Cases(unittest.TestCase):
    def setUp(self):
        self.a, self.b = socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)

    def tearDown(self):
        self.a.close()
        self.b.close()

    def test_kernel_peer(self):
        p = m.verify_local_peer(self.a, expected_uid=os.geteuid(), expected_gid=os.getegid())
        self.assertEqual((p.pid, p.uid, p.gid), (os.getpid(), os.geteuid(), os.getegid()))

    def test_wrong_uid(self):
        with self.assertRaises(m.LocalPeerRefused):
            m.verify_local_peer(self.a, expected_uid=os.geteuid() + 1)

    def test_wrong_gid(self):
        with self.assertRaises(m.LocalPeerRefused):
            m.verify_local_peer(self.a, expected_uid=os.geteuid(), expected_gid=os.getegid() + 1)

    def test_reject_boolean_uid(self):
        with self.assertRaises(m.LocalPeerRefused):
            m.verify_local_peer(self.a, expected_uid=True)

    def test_reject_boolean_gid(self):
        with self.assertRaises(m.LocalPeerRefused):
            m.verify_local_peer(self.a, expected_uid=os.geteuid(), expected_gid=False)

    def test_reject_untrusted_fake_socket(self):
        with self.assertRaises(m.LocalPeerRefused):
            m.verify_local_peer({'pid': os.getpid(), 'uid': os.geteuid()}, expected_uid=os.geteuid())

    def test_reject_tcp(self):
        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            with self.assertRaises(m.LocalPeerRefused):
                m.verify_local_peer(tcp, expected_uid=os.geteuid())
        finally:
            tcp.close()

    def test_reject_datagram(self):
        a, b = socket.socketpair(socket.AF_UNIX, socket.SOCK_DGRAM)
        try:
            with self.assertRaises(m.LocalPeerRefused):
                m.verify_local_peer(a, expected_uid=os.geteuid())
        finally:
            a.close(); b.close()

    def test_review_socketpair(self):
        self.assertEqual(m.review_current_process_peer().uid, os.geteuid())

    def test_no_cli_or_network_listener(self):
        source = FILE.read_text()
        self.assertNotIn('if __name__', source)
        self.assertNotIn('.bind(', source)
        self.assertNotIn('.listen(', source)
        self.assertNotIn('TransportProof(', source)
        self.assertNotIn('subprocess', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
