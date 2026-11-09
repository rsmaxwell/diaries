import importlib.util, unittest, sys
from unittest.mock import patch
from pathlib import Path
source=Path(sys.argv[1])
spec=importlib.util.spec_from_file_location('sender_plan',source)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
STAMP='20261023-030037Z';UID='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
class Tests(unittest.TestCase):
 def test_valid_plan(self):
  p={'snapshot':STAMP,'source_uuid':UID,'receiver_verified_under_lock':True,'authorizes_prune':False,'deletion_executed':False,'candidates':['20261020-030000Z'],'retained':3,'total':4}
  with patch.object(m,'prepare_prune_parent',return_value={'snapshot':STAMP,'source_uuid':UID}),patch.object(m,'remote',return_value=__import__('json').dumps(p)):
   self.assertEqual(m.protected_prune_plan()['candidates'],['20261020-030000Z'])
 def test_deny_parent_candidate(self):
  p={'snapshot':STAMP,'source_uuid':UID,'receiver_verified_under_lock':True,'authorizes_prune':False,'deletion_executed':False,'candidates':[STAMP]}
  with patch.object(m,'prepare_prune_parent',return_value={'snapshot':STAMP,'source_uuid':UID}),patch.object(m,'remote',return_value=__import__('json').dumps(p)):
   with self.assertRaises(RuntimeError): m.protected_prune_plan()
 def test_deny_claimed_authority(self):
  p={'snapshot':STAMP,'source_uuid':UID,'receiver_verified_under_lock':True,'authorizes_prune':True,'deletion_executed':False,'candidates':[]}
  with patch.object(m,'prepare_prune_parent',return_value={'snapshot':STAMP,'source_uuid':UID}),patch.object(m,'remote',return_value=__import__('json').dumps(p)):
   with self.assertRaises(RuntimeError):m.protected_prune_plan()
 def test_pin_failure(self):
  with patch.object(m,'prepare_prune_parent',side_effect=RuntimeError('pin failure')):
   with self.assertRaises(RuntimeError):m.protected_prune_plan()
 def test_cli_deletion_not_enabled(self):
  self.assertNotIn('--execute-prune',source.read_text())
  self.assertIn("selection.add_argument('--protected-prune-plan'",source.read_text())
if __name__=='__main__':unittest.main(verbosity=2,argv=[sys.argv[0]])
