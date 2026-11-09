#!/usr/bin/python3
"""Offline installation and privilege-surface regression for 0040 3H.5q."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
TASK=(ROOT/'btrfs-replication/tasks/native.yaml').read_text()
DEFAULT=(ROOT/'btrfs-replication/defaults/main.yaml').read_text()
ENDPOINT=(ROOT/'snapshots/files/btrfs-agreed-parent-prepare-endpoint.py').read_text()
VERIFIER=(ROOT/'snapshots/files/btrfs-agreed-parent-prepare-verifier.py').read_text()
SECTION=TASK.split('# 0040 3H.5q:',1)[1]
class Tests(unittest.TestCase):
 def test_default_off(self): self.assertIn('btrfs_agreed_parent_receiver_prepare_install_enabled: false',DEFAULT)
 def test_boolean_receiver_gate(self):
  self.assertIn('btrfs_agreed_parent_receiver_prepare_install_enabled is boolean',SECTION)
  self.assertIn("btrfs_native_endpoint_role == 'receiver'",SECTION)
 def test_isolated_tag(self):
  self.assertIn('tags: [agreed-parent-receiver-prepare]',SECTION)
  self.assertNotIn('tags: [native-btrfs',SECTION)
 def test_only_expected_files(self):
  self.assertEqual(SECTION.count("{name:"),3)
  for item in ('transition','prepare-verifier','prepare-endpoint'): self.assertIn("{name: '"+item+"'",SECTION)
  self.assertNotIn("{name: 'transition-endpoint'",SECTION)
 def test_dependency_permissions(self):
  self.assertIn("{name: 'transition', mode: '0644'}",SECTION)
  self.assertIn("{name: 'prepare-verifier', mode: '0644'}",SECTION)
  self.assertIn("{name: 'prepare-endpoint', mode: '0755'}",SECTION)
 def test_no_authorization_or_execution(self):
  for bad in ('sudoers','systemd','service:', 'command:', 'shell:', 'ansible.builtin.systemd','btrfs send','btrfs receive'):
   self.assertNotIn(bad,SECTION)
 def test_no_general_endpoint_import(self):
  self.assertIn("load('prepare-verifier').verify_snapshot",ENDPOINT)
  self.assertNotIn("load('transition-endpoint')",ENDPOINT)
  self.assertNotIn('def main(',VERIFIER)
  self.assertNotIn('def dispatch(',VERIFIER)
if __name__=='__main__': unittest.main(verbosity=2)
