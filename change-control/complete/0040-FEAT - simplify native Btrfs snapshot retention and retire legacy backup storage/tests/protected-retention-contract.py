import json,sys,unittest
from pathlib import Path
paths=list(map(Path,sys.argv[1:]))
class Contract(unittest.TestCase):
 def test_policy_matches_root_config(self):
  raw=json.loads(paths[0].read_text())
  template=json.loads(paths[1].read_text())
  self.assertEqual(raw['retention'],template['retention'])
  self.assertFalse(template['receiver_prune_enabled'])
 def test_receiver_lock_scope(self):
  source=paths[2].read_text()
  self.assertLess(source.index('fcntl.flock(handle, fcntl.LOCK_EX'),source.index('if args.protected_retention_plan:'))
  self.assertIn('authorizes_prune\': False',source)
 def test_ansible_opt_in(self):
  source=paths[3].read_text()
  self.assertIn('Install public receiver retention policy (opt in)',source)
  self.assertIn('btrfs_native_receiver_manager_install_enabled | bool',source)
 def test_no_receiver_delete_role(self):
  source=paths[2].read_text()
  self.assertNotIn('delete-receiver',source)
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
