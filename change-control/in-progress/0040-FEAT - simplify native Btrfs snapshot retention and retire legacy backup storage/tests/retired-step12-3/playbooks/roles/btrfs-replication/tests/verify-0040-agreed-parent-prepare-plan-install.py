#!/usr/bin/env python3
"""0040 3H.5n offline installation contract tests."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[1]
class Tests(unittest.TestCase):
    def test_default_off(self):
        self.assertIn('btrfs_agreed_parent_prepare_plan_install_enabled: false', (ROOT/'defaults/main.yaml').read_text())
    def test_boolean_gate_and_host(self):
        text=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5n:')[1]
        self.assertIn('btrfs_agreed_parent_prepare_plan_install_enabled is boolean',text)
        self.assertIn("btrfs_native_endpoint_role == 'source'",text)
    def test_isolated_tag(self):
        text=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5n:')[1]
        self.assertEqual(text.count('tags: [agreed-parent-prepare-plan]'),2)
    def test_only_expected_files(self):
        text=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5n:')[1]
        self.assertIn('loop: [prepare-preflight, prepare-transport-contract, locked-prepare-plan]',text)
        self.assertIn("mode: '0755'",text)
    def test_no_execution_or_scheduler(self):
        text=(ROOT/'tasks/native.yaml').read_text().split('# 0040 3H.5n:')[1]
        for bad in ('systemd:', 'command:', 'shell:', 'service:', 'sudoers', 'btrfs send', 'btrfs receive'):
            self.assertNotIn(bad,text)
    def test_modules_exist(self):
        for item in ('prepare-preflight','prepare-transport-contract','locked-prepare-plan'):
            self.assertTrue((ROOT/'files'/f'btrfs-agreed-parent-{item}.py').is_file())
if __name__=='__main__': unittest.main(verbosity=2)
