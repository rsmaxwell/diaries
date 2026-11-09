#!/usr/bin/env python3
"""Offline fixed-command binding regression; no SSH/Btrfs execution."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-fixed-commands.py'
spec = importlib.util.spec_from_file_location('fixed_commands', FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = dict(timestamp='20261030-030033Z', uuid='d901ddd2-66c7-0b42-b26c-ab6886273b7a')
B = dict(timestamp='20261030-170009Z', uuid='a9b78fb9-4da6-cf4f-b242-13909f574193')

class Tests(unittest.TestCase):
    def test_fixed_incremental_source(self):
        send, ssh = mod.receive_commands(A,B)
        self.assertEqual(send, ['sudo','-n',mod.SOURCE_ENDPOINT,'--role','incremental-source','--snapshot', B['timestamp'],'--parent',A['timestamp']])
        self.assertEqual(ssh[-10:], [mod.RECEIVER_ENTRY,'--receive','--parent',A['timestamp'],'--parent-uuid',A['uuid'],'--candidate',B['timestamp'],'--candidate-uuid',B['uuid']])
    def test_finalise_is_separate_authenticated_command(self):
        receive = mod.receive_commands(A,B)[1]
        final = mod.finalise_command(A,B)
        self.assertEqual(receive[:len(mod.SSH)],list(mod.SSH))
        self.assertEqual(final[:len(mod.SSH)],list(mod.SSH))
        self.assertNotIn('--finalise',receive)
        self.assertIn('--finalise',final)
    def test_strict_ssh(self):
        self.assertIn('StrictHostKeyChecking=yes',mod.SSH)
        self.assertIn('BatchMode=yes',mod.SSH)
        self.assertIn('-T',mod.SSH)
        self.assertNotIn('-t',mod.SSH)
        self.assertEqual(mod.RECEIVER_PRIVILEGE, ('sudo', '-n'))
    def test_all_receiver_operations_use_fixed_privilege_boundary(self):
        commands = [mod.receive_commands(A,B)[1], mod.finalise_command(A,B),
                    mod.session_command(A,B), mod.receipt_command(A,B)]
        for command in commands:
            self.assertEqual(command[:len(mod.SSH)], list(mod.SSH))
            self.assertEqual(command[len(mod.SSH):len(mod.SSH)+3],
                             ['sudo','-n',mod.RECEIVER_ENTRY])
            self.assertEqual(command.count(mod.RECEIVER_ENTRY), 1)
    def test_bad_order(self):
        with self.assertRaises(mod.CommandRefused): mod.receive_commands(B,A)
    def test_injected_timestamp(self):
        with self.assertRaises(mod.CommandRefused): mod.receive_commands(A,dict(B,timestamp=B['timestamp']+';id'))
    def test_invalid_uuid(self):
        with self.assertRaises(mod.CommandRefused): mod.finalise_command(A,dict(B,uuid='not-a-uuid'))
    def test_extra_fields(self):
        with self.assertRaises(mod.CommandRefused): mod.receive_commands(dict(A, arbitrary='x'), B)
    def test_no_public_cli(self):
        self.assertFalse(hasattr(mod,'main'))

if __name__ == '__main__': unittest.main(verbosity=2)
