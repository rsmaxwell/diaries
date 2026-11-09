#!/usr/bin/python3
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def test_default_off(self):
        self.assertIn('btrfs_agreed_parent_get_state_install_enabled: false', (ROOT/'defaults/main.yaml').read_text())
    def test_isolated_tag(self):
        tasks=(ROOT/'tasks/native.yaml').read_text()
        tail=tasks[tasks.index('# 0040 3H.5g:'):]
        self.assertIn('tags: [agreed-parent-get-state]',tail)
        self.assertNotIn('native-btrfs,',tail)
    def test_receiver_only(self):
        tail=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5g:')[1]
        self.assertEqual(tail.count("btrfs_native_endpoint_role == 'receiver'"),3)
    def test_install_only(self):
        tail=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5g:')[1]
        self.assertNotIn('ansible.builtin.systemd',tail)
        self.assertNotIn('sudoers.d',tail.split('- name: Agreed parent | Validate')[1])
        self.assertIn('btrfs_agreed_parent_get_state_install_enabled | bool',tail)
    def test_one_file(self):
        tail=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5g:')[1]
        self.assertIn('btrfs-agreed-parent-get-state-endpoint.py',tail)
        self.assertNotIn('transition-endpoint.py',tail)
if __name__=='__main__':unittest.main(verbosity=2)
