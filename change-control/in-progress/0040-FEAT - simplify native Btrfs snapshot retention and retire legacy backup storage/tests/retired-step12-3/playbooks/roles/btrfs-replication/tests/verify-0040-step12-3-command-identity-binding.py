#!/usr/bin/env python3
"""0040-FEAT Step 12.3: fixed commands carry exact A/B UUID identities."""
import importlib.util
from pathlib import Path
import unittest
BASE = Path(__file__).resolve().parents[1] / 'files'
spec = importlib.util.spec_from_file_location('fixed_commands', BASE / 'btrfs-agreed-parent-fixed-commands.py')
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class IdentityBinding(unittest.TestCase):
    def test_receive_exact_identity(self):
        _, ssh = mod.receive_commands(A, B)
        self.assertEqual(ssh[-9:], ['--receive', '--parent', A['timestamp'], '--parent-uuid', A['uuid'], '--candidate', B['timestamp'], '--candidate-uuid', B['uuid']])
    def test_privileged_identity_queries(self):
        for command in [mod.receive_commands(A, B)[1], mod.finalise_command(A, B),
                        mod.session_command(A,B), mod.receipt_command(A,B)]:
            self.assertEqual(command[len(mod.SSH):len(mod.SSH)+3],
                             ['sudo','-n',mod.RECEIVER_ENTRY])
    def test_finalise_exact_identity(self):
        ssh = mod.finalise_command(A, B)
        self.assertEqual(ssh[-9:], ['--finalise', '--parent', A['timestamp'], '--parent-uuid', A['uuid'], '--candidate', B['timestamp'], '--candidate-uuid', B['uuid']])
    def test_uuid_change_changes_both_commands(self):
        other = dict(B, uuid='a9b78fb9-4da6-cf4f-b242-13909f574194')
        self.assertNotEqual(mod.receive_commands(A, B)[1], mod.receive_commands(A, other)[1])
        self.assertNotEqual(mod.finalise_command(A, B), mod.finalise_command(A, other))
    def test_untrusted_shape_refused(self):
        for changed in (dict(A, unexpected='yes'), dict(A, uuid='bad')):
            with self.assertRaises(mod.CommandRefused): mod.receive_commands(changed, B)
            with self.assertRaises(mod.CommandRefused): mod.finalise_command(changed, B)
    def test_no_executable_receiver_cli_yet(self):
        self.assertFalse(hasattr(mod, 'main'))
if __name__ == '__main__': unittest.main(verbosity=2)
