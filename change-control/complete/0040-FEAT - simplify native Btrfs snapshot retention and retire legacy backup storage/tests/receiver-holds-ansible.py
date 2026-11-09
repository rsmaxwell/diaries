import json, unittest, sys
from pathlib import Path
import yaml
ROOT=Path(sys.argv.pop(1)) if len(sys.argv)>1 else Path(__file__).resolve().parent/'playbook-sources-20261023-170120'/'playbooks'
role=ROOT/'roles/btrfs-replication'
class Tests(unittest.TestCase):
 def setUp(self):
  self.defaults=yaml.safe_load((role/'defaults/main.yaml').read_text())
  self.tasks=yaml.safe_load((role/'tasks/native.yaml').read_text())
  self.template=(role/'templates/btrfs-receiver-manager.json.j2').read_text()
 def task(self,part):return next(t for t in self.tasks if part in t['name'])
 def test_required_checkpoint_ids(self):
  holds=self.defaults['btrfs_native_receiver_checkpoint_holds'];self.assertEqual(set(holds),{'20261013-171228Z','20261018-165453Z'});self.assertEqual(holds['20261013-171228Z']['source_uuids']['@data'],'340674cc-d02c-244e-b7ec-e3ea5a6b151f')
 def test_config_default_off(self):
  self.assertIn('"receiver_prune_enabled": false',self.template)
 def test_independent_root_controlled_path(self):
  self.assertIn('"path": "/etc/btrfs-receiver-checkpoint-holds.json"',self.template)
 def test_holds_required(self):self.assertIn('"required": true',self.template)
 def test_initialization_preserves_existing(self):
  t=self.task('Initialise receiver checkpoint holds');self.assertIs(t['ansible.builtin.copy']['force'],False);self.assertEqual(t['ansible.builtin.copy']['mode'],'0600')
 def test_existing_holds_checked_not_rewritten(self):
  self.assertIn('slurp',str(self.task('Read existing hold state without altering it')));self.assertIn('assert',str(self.task('Validate mandatory checkpoints in existing hold state')))
 def test_identity_verified_from_receipts(self):
  t=self.task('Validate mandatory receiver checkpoint receipt identities');s=' '.join(t['ansible.builtin.assert']['that']);self.assertIn('receipt.received_uuid',s);self.assertIn('receipt.read_only_verified',s)
 def test_receiver_only_opt_in(self):
  for fragment in ('Inspect independent receiver checkpoint holds','Initialise receiver checkpoint holds','Read mandatory receiver checkpoint receipts'):
   cond=str(self.task(fragment)['when']);self.assertIn("btrfs_native_endpoint_role == 'receiver'",cond);self.assertIn('btrfs_native_receiver_manager_install_enabled',cond)
if __name__=='__main__':unittest.main(verbosity=2)
