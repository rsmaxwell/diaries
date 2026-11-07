#!/usr/bin/env python3
"""Verify consolidated 0040 runtime manifest and safety boundaries."""
import pathlib, unittest, yaml
ROOT=pathlib.Path(__file__).resolve().parents[1]
class RuntimeTest(unittest.TestCase):
 def test_opt_in_off(self):
  self.assertIs(yaml.safe_load((ROOT/'defaults/main.yaml').read_text())['btrfs_agreed_parent_runtime_install_enabled'],False)
 def test_no_operational_overwrite(self):
  body=(ROOT/'tasks/agreed-parent-runtime.yaml').read_text()
  self.assertNotIn('btrfs-native-push-receiver',body)
  self.assertNotIn('/usr/local/libexec/btrfs-native-endpoint',body)
  self.assertNotIn('systemd',body)
  self.assertNotIn('sudoers',body)
 def test_manifest_is_well_formed(self):
  tasks=yaml.safe_load((ROOT/'tasks/agreed-parent-runtime.yaml').read_text())
  self.assertEqual(len(tasks),6)
  self.assertTrue(any(t.get('ansible.builtin.copy',{}).get('dest')=='/usr/local/bin/btrfs-agreed-parent-sender' and t.get('when')=="inventory_hostname == 'mars'" for t in tasks))
  self.assertTrue(any(t.get('ansible.builtin.copy',{}).get('dest')=='/usr/local/bin/btrfs-agreed-parent-receiver' for t in tasks))
 def test_source_files_exist(self):
  tasks=yaml.safe_load((ROOT/'tasks/agreed-parent-runtime.yaml').read_text())
  for task in tasks:
   if 'ansible.builtin.copy' not in task: continue
   for stem in task.get('loop',[]):
    if stem in ('receiver','state','endpoint','transfer-absence','transfer-attestation','source-observer','source-evidence'): continue
    self.assertTrue((ROOT/'files'/f'btrfs-agreed-parent-{stem}.py').is_file(),stem)
if __name__=='__main__': unittest.main(verbosity=2)
