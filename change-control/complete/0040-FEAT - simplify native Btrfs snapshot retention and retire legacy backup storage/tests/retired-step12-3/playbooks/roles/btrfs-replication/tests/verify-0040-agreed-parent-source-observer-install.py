#!/usr/bin/env python3
"""Static deployment gating regression for 0040 3H.4i."""
from pathlib import Path
import unittest
ROOT = Path(__file__).resolve().parents[3]
class Tests(unittest.TestCase):
    def test_default_disabled(self):
        s=(ROOT/'roles/btrfs-replication/defaults/main.yaml').read_text()
        self.assertIn('btrfs_agreed_parent_source_observer_install_enabled: false',s)
    def test_isolated_tag(self):
        s=(ROOT/'roles/btrfs-replication/tasks/native.yaml').read_text()
        block=s[s.index('# 0040 Increment 3H.4i:'):]
        self.assertIn('tags: [agreed-parent-source-observer]',block)
        self.assertNotIn('tags: [native-btrfs',block)
        self.assertIn('source-observer, state, source-evidence, observation-bridge',block)
        self.assertNotIn('sudoers',block.split('- name: Agreed parent | Install dormant source observation modules')[1])
    def test_exact_receiver_command(self):
        src=(ROOT/'roles/snapshots/files/btrfs-agreed-parent-source-observer.py').read_text()
        self.assertIn("'/usr/local/libexec/btrfs-agreed-parent-endpoint.py'",src)
        self.assertNotIn("'/usr/local/sbin/btrfs-agreed-parent-observe'",src)
    def test_no_timer_commands(self):
        s=(ROOT/'roles/btrfs-replication/tasks/native.yaml').read_text().split('# 0040 Increment 3H.4i:')[1]
        self.assertNotIn('ansible.builtin.systemd',s)
        self.assertNotIn('ansible.builtin.command',s)
if __name__ == '__main__': unittest.main(verbosity=2)
