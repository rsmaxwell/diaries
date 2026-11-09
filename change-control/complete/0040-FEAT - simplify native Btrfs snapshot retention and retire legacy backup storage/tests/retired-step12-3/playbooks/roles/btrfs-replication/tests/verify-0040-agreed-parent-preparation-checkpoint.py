#!/usr/bin/python3
import importlib.util
from pathlib import Path
import unittest
from types import SimpleNamespace
P=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-preparation-checkpoint.py'
s=importlib.util.spec_from_file_location('checkpoint',P); m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
S={'schema':1,'established':A,'pending':None,'previous':None}
AFTER=dict(S,pending=B)
class Stack:
 def __init__(self):self.events=[]
 def acquire(self, stack,path): self.events.append(('lock',path.name));return object()
class Tests(unittest.TestCase):
 def make(self, scenario='normal'):
  events=[]; lk=Stack(); local=dict(S)
  remote=dict(S)
  def get(tid,source_lock_held=False):
   self.assertTrue(source_lock_held);events.append('get');return dict(schema=1,receiver=dict(remote),**{k:False for k in ('authorizes_prepare','authorizes_promote','authorizes_transfer','authorizes_prune','authorizes_release')})
  def invoke(req,**kw):
   events.append('prepare'); self.assertTrue(kw['locks_held']); remote.update(AFTER)
   if scenario=='lost-ack':raise uncertain('lost acknowledgement')
  uncertain=type('Uncertain',(RuntimeError,),{})
  def source_prepare(**kw):
   events.append('source'); self.assertTrue(kw['push_lock_held']);self.assertEqual(remote,AFTER)
   self.assertEqual(kw['read_receiver'](B['timestamp'])['receiver'],AFTER)
   return {'status':'source-prepared-verified','source':AFTER}
  d={'locked-get-state':lk,'state':SimpleNamespace(load=lambda *a,**k:dict(local),validate=lambda x:x,prepare=lambda a,b:dict(a,pending=b)),
     'source-evidence':SimpleNamespace(verify_source=lambda x:dict(x,verified=True)),
     'transfer-plan':SimpleNamespace(target_identity=lambda x:dict(B)),
     'get-state-transport':SimpleNamespace(get_state=get),
     'prepare-transport':SimpleNamespace(invoke=invoke,PrepareUncertain=uncertain),
     'prepare-transport-contract':SimpleNamespace(prepare_request=lambda a,b,c:dict(schema=1,operation='prepare',transaction_id=c['timestamp'],expected_before=b,candidate=c),expected_after=lambda r:dict(r['expected_before'],pending=r['candidate'])),
     'source-recovery-integration':SimpleNamespace(prepare_source=source_prepare),
     'source-transition':object(),'recovery-decision':object()}
  return d,events,lk,remote
 def test_review_never_mutates(self):
  d,e,l,r=self.make(); result=m.checkpoint(B['timestamp'],deps=d)
  self.assertEqual(result['status'],'review-only');self.assertEqual(e,['get']);self.assertEqual(r,S)
 def test_execute_checkpoint(self):
  d,e,l,r=self.make();result=m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertEqual(result['status'],'prepared-checkpoint');self.assertEqual(e,['get','prepare','get','source','get']);self.assertFalse(result['authorizes_release'])
 def test_lost_ack_reconcile(self):
  d,e,l,r=self.make('lost-ack');result=m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertEqual(result['status'],'prepared-checkpoint');self.assertEqual(e.count('prepare'),1)
 def test_receiver_not_prepared_no_source(self):
  d,e,l,r=self.make();d['prepare-transport'].invoke=lambda *a,**k:None
  with self.assertRaisesRegex(RuntimeError,'not confirmed'):m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertNotIn('source',e)
 def test_receiver_diff_no_prepare(self):
  d,e,l,r=self.make();d['get-state-transport'].get_state=lambda *a,**k:dict(schema=1,receiver=dict(S,pending=B),**{k:False for k in ('authorizes_prepare','authorizes_promote','authorizes_transfer','authorizes_prune','authorizes_release')})
  with self.assertRaisesRegex(RuntimeError,'differ'):m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertNotIn('prepare',e)
 def test_source_unfinished_no_prepare(self):
  d,e,l,r=self.make();d['state'].load=lambda *a,**k:dict(S,pending=B)
  with self.assertRaisesRegex(RuntimeError,'already active'):m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertEqual(e,[])
 def test_no_release_or_transfer_calls(self):
  src=P.read_text();self.assertNotIn('release-source',src);self.assertNotIn('btrfs send',src);self.assertNotIn('subprocess.run',src)
 def test_manager_lock_released_before_source(self):
  d,e,l,r=self.make();m.checkpoint(B['timestamp'],execute=True,deps=d)
  self.assertEqual([p for kind,p in l.events],['.native-push.lock','btrfs-snapshot-manager.lock'])
if __name__=='__main__':unittest.main(verbosity=2)
