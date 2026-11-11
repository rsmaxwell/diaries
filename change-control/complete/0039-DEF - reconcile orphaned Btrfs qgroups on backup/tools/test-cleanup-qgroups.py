import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
p=Path(__file__).resolve().with_name('cleanup-qgroups.py')
spec=importlib.util.spec_from_file_location('cleanup',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Test(unittest.TestCase):
 def test_field_spacing(self):
  self.assertEqual(m.field('    Subvolume ID:    55715\n','Subvolume ID'),'55715')
  self.assertEqual(m.field('Received UUID:\tfoo\n','Received UUID'),'foo')
 def test_targets(self):
  inv=(set(),{},[1,2,3],[4,5,6],set())
  self.assertEqual(m.planned(inv,4),[('unlimited',1),('limited',4),('unlimited',2),('limited',5)])
 def test_missing(self):
  with self.assertRaises(RuntimeError):m.planned((set(),{},[],[],set()),1)
 def test_journal_refusal(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   f=Path(d)/'stage-c-test.jsonl';f.write_text('{"event":"ATTEMPT"}\n')
   with self.assertRaisesRegex(RuntimeError,'unresolved'):m.unresolved_journal(Path(d))
   f.write_text('{"event":"PASS"}\n');m.unresolved_journal(Path(d))
 def test_parser_rejects_nonzero(self):
  import subprocess
  def fake(*args):
   if args[1]=='subvolume': return ''.join(f'ID {i} gen 1 top level 5 path x{i}\n' for i in range(100,233))
   return 'qgroupid rfer excl max_rfer max_excl parent child\n------- ---- ---- ---- ---- ---- ----\n' + ''.join(f'0/{i} 1.00B 1.00B none none --- ---\n' for i in range(100,233))+'0/5 1.00B 1.00B none none --- ---\n0/276 1.00B 0.00B none none --- ---\n'
  with patch.object(m,'command',side_effect=fake):
   with self.assertRaisesRegex(RuntimeError,'unverified candidate'):m.inventory()
 def test_parser_accepts_new_live_snapshot(self):
  def fake(*args):
   if args[1]=='subvolume': return ''.join(f'ID {i} gen 1 top level 5 path x{i}\n' for i in range(100,234))
   return 'qgroupid rfer excl max_rfer max_excl parent child\n------- ---- ---- ---- ---- ---- ----\n'+''.join(f'0/{i} 1.00B 1.00B none none --- ---\n' for i in range(100,234))+'0/5 1.00B 1.00B none none --- ---\n0/276 0.00B 0.00B none none --- ---\n'
  with patch.object(m,'command',side_effect=fake):
   inv=m.inventory()
   self.assertEqual(len(inv[0]),134)
   self.assertEqual(m.summary(inv),(1,0,136))
 def test_parser_rejects_new_subvolume_without_qgroup(self):
  def fake(*args):
   if args[1]=='subvolume': return ''.join(f'ID {i} gen 1 top level 5 path x{i}\n' for i in range(100,234))
   return 'qgroupid rfer excl max_rfer max_excl parent child\n------- ---- ---- ---- ---- ---- ----\n'+''.join(f'0/{i} 1.00B 1.00B none none --- ---\n' for i in range(100,233))+'0/5 1.00B 1.00B none none --- ---\n'
  with patch.object(m,'command',side_effect=fake):
   with self.assertRaisesRegex(RuntimeError,'active qgroup set mismatch'):m.inventory()
 def test_parser_happy(self):
  def fake(*args):
   if args[1]=='subvolume': return ''.join(f'ID {i} gen 1 top level 5 path x{i}\n' for i in range(100,233))
   return 'qgroupid rfer excl max_rfer max_excl parent child\n------- ---- ---- ---- ---- ---- ----\n'+''.join(f'0/{i} 1.00B 1.00B none none --- ---\n' for i in range(100,233))+'0/5 1.00B 1.00B none none --- ---\n0/276 0.00B 0.00B none none --- ---\n0/277 0.00B 0.00B 1.00TiB none --- ---\n'
  with patch.object(m,'command',side_effect=fake):
   self.assertEqual(m.summary(m.inventory()),(1,1,136))
 def test_stable_active_ignores_accounting_changes(self):
  before=({100,101},{100:('1.00GiB','10.00MiB','none','none','---','---'),101:('1.00GiB','10.00MiB','1.00TiB','none','---','---')},[],[],set())
  after=({100,101},{100:('1.50GiB','20.00MiB','none','none','---','---'),101:('2.00GiB','0.00B','1.00TiB','none','---','---')},[],[],set())
  self.assertEqual(m.stable_active(before), m.stable_active(after))
 def test_stable_active_detects_limit_change(self):
  before=({100},{100:('1.00GiB','1.00MiB','none','none','---','---')},[],[],set())
  changed=({100},{100:('1.00GiB','1.00MiB','1.00TiB','none','---','---')},[],[],set())
  self.assertNotEqual(m.stable_active(before),m.stable_active(changed))
 def test_stable_active_detects_relationship_change(self):
  before=({100},{100:('1.00GiB','1.00MiB','none','none','---','---')},[],[],set())
  changed=({100},{100:('1.00GiB','1.00MiB','none','none','1/2','---')},[],[],set())
  self.assertNotEqual(m.stable_active(before),m.stable_active(changed))
 def test_stable_active_detects_subvolume_change(self):
  before=({100},{100:('1.00GiB','1.00MiB','none','none','---','---')},[],[],set())
  changed=({101},{100:('1.00GiB','1.00MiB','none','none','---','---')},[],[],set())
  self.assertNotEqual(m.stable_active(before),m.stable_active(changed))

class TestAcknowledgement(unittest.TestCase):
 def fixture(self, directory):
  import json
  import hashlib
  path=Path(directory)/'stage-c-20261021-201036Z-598228.jsonl'
  ids=list(range(1000,1675))
  records=[{'event':'START','filesystem_uuid':m.UUID,'baseline':[15414,13901,29449], 'targets':[f'0/{i}' for i in range(1000,2000)]}]
  for qid in ids:
   records.extend([{'event':'ATTEMPT','id':f'0/{qid}'},{'event':'REMOVED','id':f'0/{qid}'}])
  records.append({'event':'FAIL','error':'active set changed','completed':ids})
  path.write_text(''.join(json.dumps(rec)+'\n' for rec in records))
  inv=(set(range(3000,3133)), {**{i:('1B','1B','none','none','---','---') for i in range(3000,3133)},5:('1B','1B','none','none','---','---')}, list(range(4000,4000+15076)),list(range(30000,30000+13564)),set(range(3000,3133))|{5}|set(range(4000,4000+15076))|set(range(30000,30000+13564)))
  return path,hashlib.sha256(path.read_bytes()).hexdigest(), inv
 def test_acknowledgement_and_gate(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path, digest, inv=self.fixture(d)
   with self.assertRaisesRegex(RuntimeError,'unresolved'):
    m.unresolved_journal(Path(d),inv)
   m.acknowledge(path,digest,inv)
   m.unresolved_journal(Path(d),inv)
   self.assertTrue(path.with_name(path.name+'.ack.json').exists())
 def test_acknowledgement_after_snapshot_arrival(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path,digest,inv=self.fixture(d)
   subvol=inv[0] | {55815}
   active=dict(inv[1]); active[55815]=('1B','1B','none','none','---','---')
   changed=(subvol,active,inv[2],inv[3],inv[4] | {55815})
   m.acknowledge(path,digest,changed)
   m.unresolved_journal(Path(d),changed)
 def test_acknowledgement_rejects_extra_candidate(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path,digest,inv=self.fixture(d)
   changed=(inv[0],inv[1],inv[2]+[99999],inv[3],inv[4]|{99999})
   with self.assertRaisesRegex(RuntimeError,'candidate baseline changed'):
    m.acknowledge(path,digest,changed)
 def test_wrong_sha_refused(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path, digest, inv=self.fixture(d)
   with self.assertRaisesRegex(RuntimeError,'SHA-256 mismatch'):
    m.acknowledge(path,'a'*64,inv)
 def test_live_removed_id_present_refused(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path, digest, inv=self.fixture(d)
   bad=(inv[0],inv[1],inv[2],inv[3],inv[4]|{1000})
   with self.assertRaisesRegex(RuntimeError,'deleted IDs present'):
    m.acknowledge(path,digest,bad)
 def test_ack_tamper_refused(self):
  from tempfile import TemporaryDirectory
  with TemporaryDirectory() as d:
   path,digest,inv=self.fixture(d)
   m.acknowledge(path,digest,inv)
   ack=path.with_name(path.name+'.ack.json')
   ack.write_text(ack.read_text().replace(digest,'0'*64))
   with self.assertRaisesRegex(RuntimeError,'acknowledgement mismatch'):
    m.unresolved_journal(Path(d),inv)

if __name__=='__main__': unittest.main()
