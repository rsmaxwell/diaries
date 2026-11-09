#!/usr/bin/env python3
"""Static install-only gate regression. Does not contact production."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
DEFAULTS=(ROOT/'defaults/main.yaml').read_text()
TASKS=(ROOT/'tasks/native.yaml').read_text()
class InstallOnly(unittest.TestCase):
    def test_default_off(self):
        self.assertIn('btrfs_agreed_parent_receiver_core_install_enabled: false',DEFAULTS)
    def test_receiver_only(self):
        self.assertIn("btrfs_native_endpoint_role == 'receiver'", TASKS.split('Check receiver core installation gate')[-1])
    def test_no_executable_receive_entry(self):
        fragment=TASKS.split('- name: Agreed parent | Install dormant agreed-parent receiver core and dependencies')[-1]
        self.assertIn("mode: '0644'",fragment)
        self.assertNotIn('ansible.builtin.command:',fragment)
        self.assertNotIn('ansible.builtin.shell:',fragment)
        self.assertNotIn('systemd:',fragment)
    def test_all_dependencies_exist(self):
        entries=[('btrfs-replication', n) for n in ('receiver-entry','receive-core','provisional-journal','receive-boundary')] + [('snapshots',n) for n in ('receiver','endpoint','state','transfer-absence','transfer-attestation')]
        for role,name in entries:
            self.assertTrue((ROOT.parent/role/'files'/f'btrfs-agreed-parent-{name}.py').is_file(), (role,name))
            self.assertIn(f"name: '{name}'",TASKS)
    def test_old_receiver_unchanged(self):
        self.assertIn('btrfs-native-push-receiver.py',TASKS)
if __name__=='__main__': unittest.main(verbosity=2)
