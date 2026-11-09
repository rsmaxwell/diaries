#!/usr/bin/env python3
"""Source checks for opt-in dormant receiver promotion installation."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
TASKS=(ROOT/'tasks/native.yaml').read_text()
DEFAULT=(ROOT/'defaults/main.yaml').read_text()
NAMES=['receiver-entry', 'receive-core', 'provisional-journal', 'finalisation-core', 'finalisation-storage', 'finalisation-transaction', 'session-proof', 'receiver-promotion-adapter', 'receiver-promoted-readback', 'receiver-promotion-binding', 'receiver-operation-contract']
class Gate(unittest.TestCase):
    def test_gate_off(self):
        self.assertIn('btrfs_agreed_parent_promotion_modules_install_enabled: false',DEFAULT)
    def test_all_modules_present(self):
        for n in NAMES:
            with self.subTest(n=n):
                self.assertTrue((ROOT/'files'/('btrfs-agreed-parent-'+n+'.py')).is_file())
    def test_install_block_gated(self):
        section=TASKS.split('- name: Agreed parent | Install dormant receiver promotion modules only',1)[1].split('  tags: [agreed-parent-dormant-promotion]',1)[0]
        self.assertIn('btrfs_agreed_parent_promotion_modules_install_enabled | bool',section)
        self.assertIn("btrfs_native_endpoint_role == 'receiver'",section)
        self.assertIn("mode: '0644'",section)
        for n in NAMES:self.assertIn('    - '+n+'\n',section)
    def test_no_legacy_overwrite(self):
        section=TASKS.split('- name: Agreed parent | Install dormant receiver promotion modules only',1)[1].split('  tags: [agreed-parent-dormant-promotion]',1)[0]
        listed=[x.strip()[2:] for x in section.split('  become: true',1)[0].splitlines() if x.startswith('    - ')]
        self.assertEqual(listed,NAMES)
        self.assertNotIn('    - receiver\n',section)
        self.assertNotIn('    - state\n',section)
        self.assertNotIn('    - endpoint\n',section)
    def test_no_command_or_sudo_permission(self):
        section=TASKS.split('# 0040-FEAT Step 12.3 Gate A:',1)[1].split('# 0040-FEAT Step 12.3: install-only',1)[0]
        for fragment in ('/usr/local/bin/', 'authorized_keys', 'sudoers', 'systemd', 'command:','shell:'):
            self.assertNotIn(fragment,section)
if __name__=='__main__': unittest.main(verbosity=2)
