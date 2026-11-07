#!/usr/bin/env python3
"""0040 Step 12.3: installation isolation regression."""
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
TASK = (ROOT/'roles/btrfs-replication/tasks/native.yaml').read_text()
DEFAULT = (ROOT/'roles/btrfs-replication/defaults/main.yaml').read_text()
class Tests(unittest.TestCase):
    def test_default_off(self):
        self.assertIn('btrfs_agreed_parent_checkpoint_install_enabled: false', DEFAULT)
    def test_isolated_tag(self):
        self.assertEqual(TASK.count('tags: [agreed-parent-preparation-checkpoint]'), 2)
    def test_source_only(self):
        block=TASK[TASK.index('# 0040-FEAT Step 12.3 integration 01'):]
        self.assertGreaterEqual(block.count("btrfs_native_endpoint_role == 'source'"), 2)
        self.assertIn('btrfs_agreed_parent_checkpoint_install_enabled | bool',block)
    def test_five_files(self):
        block=TASK[TASK.index('# 0040-FEAT Step 12.3 integration 01'):]
        self.assertEqual(block.count("name: '"), 5)
        for name, role in [('prepare-transport','btrfs-replication'),('recovery-decision','btrfs-replication'),('source-recovery-integration','btrfs-replication'),('source-transition','snapshots'),('preparation-checkpoint','btrfs-replication')]:
            self.assertTrue((ROOT/f'roles/{role}/files/btrfs-agreed-parent-{name}.py').is_file())
    def test_no_execute(self):
        block=TASK[TASK.index('# 0040-FEAT Step 12.3 integration 01'):]
        self.assertNotIn('ansible.builtin.command:',block)
        self.assertNotIn('ansible.builtin.shell:',block)
        self.assertNotIn('systemd:',block)
        self.assertNotIn('release-source',block)
if __name__=='__main__': unittest.main(verbosity=2)
