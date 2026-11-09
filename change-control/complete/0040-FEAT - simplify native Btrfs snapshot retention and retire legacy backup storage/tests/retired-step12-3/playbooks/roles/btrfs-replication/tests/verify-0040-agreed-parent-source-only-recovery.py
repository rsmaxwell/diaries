#!/usr/bin/python3
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
P=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-source-only-recovery.py'
s=importlib.util.spec_from_file_location('source_only_recovery',P)
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
R=dict(S,pending=B)
AUTH={k:False for k in m.AUTH}
class Tests(unittest.TestCase):
 def fixture(self,source=None,receiver=None):
  events=[]; src=source if source is not None else S; peer=receiver if receiver is not None else R
  def acquire(stack,path): events.append('lock:'+path.name)
  def read(tid,source_lock_held=False):
   self.assertTrue(source_lock_held); events.append('read-receiver')
   return {'schema':1,'receiver':peer,**AUTH}
  def decide(source,reply,candidate,vc,vp,validate):
   events.append('decide');self.assertEqual(source,S);self.assertEqual(reply['receiver'],R)
   return {'status':'receiver-prepared-source-unprepared','receiver':R,**{k:False for k in ('authorizes_source_prepare','authorizes_receiver_prepare','authorizes_transfer','authorizes_promote','authorizes_prune','authorizes_release')}}
  def prepare_source(**kw):
   events.append('source-prepare');self.assertTrue(kw['push_lock_held']);self.assertEqual(kw['source_before'],S)
   self.assertEqual(kw['read_receiver'](B['timestamp'])['receiver'],R)
   return {'status':'source-prepared-verified','source':R}
  deps={'locked-get-state':SimpleNamespace(acquire=acquire),
        'state':SimpleNamespace(load=lambda *a,**k:src,validate=lambda x:None,prepare=lambda a,b:dict(a,pending=b)),
        'source-evidence':SimpleNamespace(verify_source=lambda x:dict(x,verified=True)),
        'transfer-plan':SimpleNamespace(target_identity=lambda x: B),
        'get-state-transport':SimpleNamespace(get_state=read),
        'source-transition':object(),
        'source-recovery-integration':SimpleNamespace(prepare_source=prepare_source),
        'recovery-decision':SimpleNamespace(decide=decide)}
  return deps,events
 def test_review_only(self):
  d,e=self.fixture(); result=m.recover(B['timestamp'],deps=d)
  self.assertEqual(result['status'],'source-only-recovery-review');self.assertFalse(result['state_changed'])
  self.assertEqual(e.count('read-receiver'),1);self.assertNotIn('source-prepare',e)
 def test_execute_only_source(self):
  d,e=self.fixture(); result=m.recover(B['timestamp'],execute=True,deps=d)
  self.assertEqual(result['status'],'source-only-recovery-prepared');self.assertFalse(result['authorizes_release'])
  self.assertEqual(e.count('read-receiver'),2);self.assertEqual(e.count('source-prepare'),1)
 def test_refuse_source_already_pending(self):
  d,e=self.fixture(source=R)
  with self.assertRaisesRegex(RuntimeError,'already in transition'):m.recover(B['timestamp'],execute=True,deps=d)
  self.assertNotIn('read-receiver',e);self.assertNotIn('source-prepare',e)
 def test_refuse_different_receiver(self):
  d,e=self.fixture(receiver=S)
  with self.assertRaises(AssertionError):m.recover(B['timestamp'],execute=True,deps=d)
  self.assertNotIn('source-prepare',e)
 def test_refuse_untrusted_authority(self):
  d,e=self.fixture();d['recovery-decision'].decide=lambda *a,**k:dict(status='receiver-prepared-source-unprepared',authorizes_source_prepare=True)
  with self.assertRaisesRegex(RuntimeError,'unsafe'):m.recover(B['timestamp'],execute=True,deps=d)
  self.assertNotIn('source-prepare',e)
 def test_refuse_source_unconfirmed(self):
  d,e=self.fixture();d['source-recovery-integration'].prepare_source=lambda **k:dict(status='unknown',source=R)
  with self.assertRaisesRegex(RuntimeError,'not confirmed'):m.recover(B['timestamp'],execute=True,deps=d)
 def test_no_receiver_prepare_or_transfer(self):
  text=P.read_text();self.assertNotIn('prepare-transport',text);self.assertNotIn('btrfs send',text);self.assertNotIn('subprocess',text)
if __name__=='__main__':unittest.main(verbosity=2)
