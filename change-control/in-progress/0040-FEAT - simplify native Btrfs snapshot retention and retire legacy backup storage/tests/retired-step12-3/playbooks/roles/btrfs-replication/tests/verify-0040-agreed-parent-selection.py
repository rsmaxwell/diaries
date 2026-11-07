#!/usr/bin/env python3
"""Offline 0040-FEAT parent-selection contract regression."""
import importlib.util
from pathlib import Path
import unittest
p=Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-selection.py'
spec=importlib.util.spec_from_file_location('agreed_selection',p)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-080033Z','uuid':'a901ddd2-66c7-0b42-b26c-ab6886273b7a'}
C={'timestamp':'20261030-090033Z','uuid':'b901ddd2-66c7-0b42-b26c-ab6886273b7a'}
def st(a=A):return {'schema':1,'established':dict(a),'pending':None,'previous':None}
def receipts(extra=()):return [{'snapshot':A['timestamp'],'source_uuid':A['uuid']},*extra]
def kwargs():return dict(source_state=st(),receiver_state=st(),target=B,source_parent=A,receiver_receipts=receipts())
class Tests(unittest.TestCase):
 def test_established_selected(self):
  x=m.select(**kwargs()); self.assertEqual((x['parent'],x['parent_uuid']),(A['timestamp'],A['uuid'])); self.assertFalse(x['authorizes_transfer']); self.assertFalse(x['authorizes_release'])
 def test_newer_common_is_not_selected(self):
  k=kwargs();k['receiver_receipts']=receipts([{'snapshot':C['timestamp'],'source_uuid':C['uuid']}]);self.assertEqual(m.select(**k)['parent'],A['timestamp'])
 def test_different_states(self):
  k=kwargs();k['receiver_state']=st(B);self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_pending(self):
  k=kwargs();k['source_state']['pending']=dict(B);k['receiver_state']['pending']=dict(B);self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_previous(self):
  k=kwargs();k['source_state']['previous']=dict(C);k['receiver_state']['previous']=dict(C);self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_missing_receipt(self):
  k=kwargs();k['receiver_receipts']=[];self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_wrong_receipt_uuid(self):
  k=kwargs();k['receiver_receipts']=[{'snapshot':A['timestamp'],'source_uuid':B['uuid']}];self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_duplicate_receipt(self):
  k=kwargs();k['receiver_receipts']=receipts(receipts());self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_wrong_source(self):
  k=kwargs();k['source_parent']=C;self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_old_target(self):
  k=kwargs();k['target']=A;self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_bool_schema(self):
  k=kwargs();k['source_state']['schema']=True;self.assertRaises(m.ParentSelectionError,m.select,**k)
 def test_no_side_effect_io(self):
  content=p.read_text();self.assertNotIn('subprocess',content);self.assertNotIn('os.remove',content)
if __name__=='__main__':unittest.main(verbosity=2)
