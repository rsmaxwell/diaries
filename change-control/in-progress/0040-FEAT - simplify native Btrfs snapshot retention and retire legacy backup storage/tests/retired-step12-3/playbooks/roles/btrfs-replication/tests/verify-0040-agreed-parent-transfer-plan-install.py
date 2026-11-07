#!/usr/bin/env python3
"""Offline 0040 3H.5c install contract. No Ansible execution."""
from pathlib import Path
import unittest
BASE = Path(__file__).resolve().parents[1]
class TestInstall(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tasks = (BASE/'tasks/native.yaml').read_text()
        cls.defaults = (BASE/'defaults/main.yaml').read_text()
    def test_default_off(self):
        self.assertIn('btrfs_agreed_parent_transfer_plan_install_enabled: false',self.defaults)
    def test_boolean_gate(self):
        self.assertIn('btrfs_agreed_parent_transfer_plan_install_enabled is boolean',self.tasks)
    def test_source_only(self):
        self.assertIn("- btrfs_native_endpoint_role == 'source'",self.tasks)
    def test_isolated_tag(self):
        segment=self.tasks.split('# 0040 Increment 3H.5c:',1)[1]
        self.assertEqual(segment.count('tags: [agreed-parent-transfer-plan]'),2)
        self.assertNotIn('native-btrfs]',segment)
    def test_install_only(self):
        segment=self.tasks.split('# 0040 Increment 3H.5c:',1)[1]
        for forbidden in ('systemd:', 'service:', 'command:', 'shell:', 'sudoers', 'state: absent', 'btrfs send', 'btrfs receive'):
            self.assertNotIn(forbidden,segment)
    def test_exact_files(self):
        segment=self.tasks.split('# 0040 Increment 3H.5c:',1)[1]
        self.assertIn('loop: [selection, transfer-plan]',segment)
        self.assertIn("mode: '0755'",segment)
if __name__ == '__main__': unittest.main(verbosity=2)
