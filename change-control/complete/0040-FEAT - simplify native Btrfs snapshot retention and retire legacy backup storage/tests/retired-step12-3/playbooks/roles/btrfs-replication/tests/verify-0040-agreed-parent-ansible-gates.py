#!/usr/bin/env python3
"""Static safety contract for dormant agreed-parent receiver deployment."""
import pathlib
import unittest
R = pathlib.Path(__file__).resolve().parents[3]
class Gates(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.defaults = (R/'roles/btrfs-replication/defaults/main.yaml').read_text()
        cls.tasks = (R/'roles/btrfs-replication/tasks/native.yaml').read_text()
    def test_defaults_are_off(self):
        for key in ('install', 'sudo'):
            self.assertIn(f'btrfs_agreed_parent_receiver_observer_{key}_enabled: false',self.defaults)
    def test_receiver_only(self):
        part=self.tasks.split('# 0040 Increment 3E')[1]
        self.assertEqual(part.count("btrfs_native_endpoint_role == 'receiver'"), 4)
    def test_explicit_sudo_gate(self):
        self.assertIn('not btrfs_agreed_parent_receiver_observer_sudo_enabled or btrfs_agreed_parent_receiver_observer_install_enabled',self.tasks)
        self.assertIn('btrfs_agreed_parent_receiver_observer_sudo_enabled | bool',self.tasks)
        self.assertIn('visudo -cf %s',self.tasks)
    def test_no_auto_state_creation(self):
        part=self.tasks.split('# 0040 Increment 3E')[1]
        self.assertNotIn('.agreed-parent.json', part)
        self.assertNotIn('btrfs subvolume delete',part)
    def test_exact_no_wildcard_sudo_command(self):
        line=next(line for line in self.tasks.splitlines() if 'NOPASSWD: /usr/local/libexec/btrfs-agreed-parent' in line)
        self.assertNotIn('*',line)
        self.assertIn('--observe-receiver',line)
if __name__ == '__main__': unittest.main(verbosity=2)
