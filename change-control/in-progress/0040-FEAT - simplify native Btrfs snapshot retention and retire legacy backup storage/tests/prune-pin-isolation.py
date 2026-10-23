#!/usr/bin/env python3
"""0040-FEAT prune pins survive ordinary sender transfer-pin release."""
import importlib.util, json, pathlib, sys, tempfile, unittest
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import patch

endpoint_file=pathlib.Path(sys.argv[1])
sender_file=pathlib.Path(sys.argv[2])
def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); sys.modules[name]=module; spec.loader.exec_module(module)
    return module
endpoint=load('endpoint_prune_pin_test',endpoint_file)
sender=load('sender_prune_pin_test',sender_file)
STAMP='20261023-030037Z'; UID='aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
@contextmanager
def fixture_protection_owner(protection, uid=0):
 """Mock only the fixture protection file's owner; preserve actual modes.

 Production protection_update still performs its strict ownership check.
 """
 original_stat = pathlib.Path.stat
 def isolated_stat(path, *args, **kwargs):
  metadata = original_stat(path, *args, **kwargs)
  if pathlib.Path(path) == protection:
   return SimpleNamespace(st_uid=uid, st_mode=metadata.st_mode)
  return metadata
 with patch.object(pathlib.Path, 'stat', isolated_stat):
  yield

class Tests(unittest.TestCase):
 def test_pin_survives_normal_release_and_repeat(self):
  with tempfile.TemporaryDirectory() as root:
   root=pathlib.Path(root); snapshots=root/'snapshots'; snapshots.mkdir()
   (snapshots/STAMP).mkdir()
   protection=root/'protection.json'; protection.write_text(json.dumps({'schema':1,'protected':{}})); protection.chmod(0o600)
   manager_lock=root/'manager.lock'; manager_lock.touch()
   def show(path): return {'Flags':'readonly','Parent UUID':endpoint.EXPECTED_ORIGIN,'UUID':UID}
   with patch.object(endpoint,'PROTECTION',protection),patch.object(endpoint,'MANAGER_LOCK',manager_lock),patch.object(endpoint,'SOURCE_DIR',snapshots),patch.object(endpoint,'fs_check',lambda *args:None),patch.object(endpoint,'show',show),fixture_protection_owner(protection):
    endpoint.protection_update(STAMP,operation='protect-prune')
    endpoint.protection_update(STAMP,operation='protect-prune')
    saved=json.loads(protection.read_text())
    self.assertEqual(saved['protected'][STAMP],UID)
    self.assertEqual(saved['prune_protected'][STAMP],UID)
    with self.assertRaisesRegex(RuntimeError,'protected for receiver pruning'):
     endpoint.protection_update(STAMP,operation='release',expected_uuid=UID)
    self.assertEqual(json.loads(protection.read_text())['protected'][STAMP],UID)
 def test_normal_transfer_pin_release_unchanged(self):
  with tempfile.TemporaryDirectory() as root:
   root=pathlib.Path(root); snapshots=root/'snapshots'; snapshots.mkdir(); (snapshots/STAMP).mkdir()
   protection=root/'protection.json'; protection.write_text(json.dumps({'schema':1,'protected':{}})); protection.chmod(0o600)
   manager_lock=root/'manager.lock'; manager_lock.touch()
   with patch.object(endpoint,'PROTECTION',protection),patch.object(endpoint,'MANAGER_LOCK',manager_lock),patch.object(endpoint,'SOURCE_DIR',snapshots),patch.object(endpoint,'fs_check',lambda *args:None),patch.object(endpoint,'show',lambda path:{'Flags':'readonly','Parent UUID':endpoint.EXPECTED_ORIGIN,'UUID':UID}),fixture_protection_owner(protection):
    endpoint.protection_update(STAMP,operation='protect')
    endpoint.protection_update(STAMP,operation='release',expected_uuid=UID)
    self.assertEqual(json.loads(protection.read_text())['protected'],{})
 def test_unsafe_protection_owner_rejected(self):
  with tempfile.TemporaryDirectory() as root:
   root=pathlib.Path(root); snapshots=root/'snapshots'; snapshots.mkdir(); (snapshots/STAMP).mkdir()
   protection=root/'protection.json'; protection.write_text(json.dumps({'schema':1,'protected':{}})); protection.chmod(0o600)
   manager_lock=root/'manager.lock'; manager_lock.touch()
   with patch.object(endpoint,'PROTECTION',protection),patch.object(endpoint,'MANAGER_LOCK',manager_lock),patch.object(endpoint,'SOURCE_DIR',snapshots),fixture_protection_owner(protection,uid=1000):
    with self.assertRaisesRegex(RuntimeError,'Unsafe protection permissions'):
     endpoint.protection_update(STAMP,operation='protect-prune')
   self.assertEqual(json.loads(protection.read_text()),{'schema':1,'protected':{}})
 def test_sender_uses_stronger_pin(self):
  operations=[]
  with patch.object(sender,'inspect_common_parent',side_effect=[{'snapshot':STAMP,'source_uuid':UID},{'snapshot':STAMP,'source_uuid':UID}]),patch.object(sender,'local',side_effect=lambda role,stamp: (operations.append(role) or {'source_uuid':UID})):
   result=sender.protect_common_parent()
  self.assertEqual(operations,['protect-prune-source'])
  self.assertFalse(result['authorizes_prune'])
 def test_deletion_still_disabled(self):
  manager=pathlib.Path(sys.argv[3]).read_text()
  self.assertIn('receiver pruning blocked: live common-parent coordination not implemented',manager)
  self.assertIn('"receiver_prune_enabled": false',pathlib.Path(sys.argv[4]).read_text())
if __name__=='__main__':
 unittest.main(verbosity=2,argv=[sys.argv[0]])
