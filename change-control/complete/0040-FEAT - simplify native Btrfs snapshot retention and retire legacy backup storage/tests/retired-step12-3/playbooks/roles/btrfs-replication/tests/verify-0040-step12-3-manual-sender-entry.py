#!/usr/bin/env python3
"""Source regressions for fixed, manual-only production sender launcher."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-sender-command.py'
spec = importlib.util.spec_from_file_location('manual_sender', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Fixed:
    SSH = ('ssh', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=yes',
           '-o', 'ConnectTimeout=15', '-T', '-p', '39263', 'richard@10.254.22.1')
    def receipt_command(self, a, b):
        return [*self.SSH, 'sudo', '-n', '/usr/local/bin/btrfs-agreed-parent-receiver', '--receipt']

class Tests(unittest.TestCase):
    def test_fixed_identity_drop(self):
        cmd = m.ExistingSSHIdentity(Fixed()).receipt_command({}, {})
        self.assertEqual(cmd[:4], ['/usr/sbin/runuser','-u','richard','--'])
        self.assertEqual(cmd[4:4+len(Fixed.SSH)], list(Fixed.SSH))
    def test_wrong_peer_refused(self):
        obj=Fixed(); obj.SSH=(*Fixed.SSH[:-1], 'other.example')
        with self.assertRaises(m.OperatorRefused): m.ExistingSSHIdentity(obj)
    def test_missing_or_unprepared_refuses(self):
        class State:
            def load(self, *a, **kw): return {'established':None,'pending':None,'previous':None,'schema':1}
            def validate(self, state): return state
        with self.assertRaises(m.OperatorRefused): m.run('execute',modules={'state':State()})
    def test_installer_is_manual_only(self):
        text=(P.parents[1]/'tasks'/'agreed-parent-runtime.yaml').read_text()
        self.assertIn('/usr/local/bin/btrfs-agreed-parent-sender',text)
        self.assertNotIn('systemd', text)
    def test_workflow_module_installed(self):
        text=(P.parents[1]/'tasks'/'agreed-parent-runtime.yaml').read_text()
        self.assertIn('    - sender-workflow',text)

if __name__ == '__main__':
    unittest.main(verbosity=2)
