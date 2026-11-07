#!/usr/bin/env python3
"""Opt-in scoped receive integration: no Btrfs/systemd side effects."""
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch
P=Path(__file__).resolve().parents[1]/'files'/'btrfs-agreed-parent-receive-core.py'
spec=importlib.util.spec_from_file_location('receive_core',P)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
UNIT='btrfs-agreed-receive-'+B['timestamp']+'-0123456789abcdef.scope'
class Tests(unittest.TestCase):
 def test_scoped_requires_real_executor(self):
  with self.assertRaisesRegex(RuntimeError,'real bounded executor'):
   self.call(scoped=True,runner=lambda *a,**k:None,scope_query=lambda u:None)
 def test_scoped_requires_observer(self):
  with self.assertRaisesRegex(RuntimeError,'trusted scope observer'):
   self.call(scoped=True)
 def call(self,**kw):
  with patch.object(m,'receive_prepared_candidate_reserved') as reserved:
   reserved.return_value={'status':'receiver-provisional-only'}
   result=m.receive_prepared_candidate_integrated(A,B,input_stream=object(),state_module=object(),absence_module=object(),endpoint_module=object(),journal_module=object(),manager_lock=Path('/run/lock/btrfs-snapshot-manager.lock'),writer_lock=m.LOCK,state_dir=m.STATE,verify_parent=lambda *args:True,**kw)
   return result,reserved.call_args
 def test_scoped_flag_reaches_reservation(self):
  _,arg=self.call(scoped=True,scope_query=lambda u:None)
  self.assertTrue(arg.kwargs['scoped'])
  self.assertTrue(arg.kwargs['inherit_receive_locks'])
 def test_unscoped_is_default(self):
  _,arg=self.call()
  self.assertFalse(arg.kwargs['scoped'])
 def test_passes_reserved_scope_to_bounded_receive(self):
  _,arg=self.call(scoped=True,scope_query=lambda u:None)
  callback=arg.kwargs['receive_stream']
  seen=[]
  def capture(*args,**kw):
   seen.append(kw);return True
  with patch.object(m,'receive_prepared_binary_stream',capture):
   callback(A,B,lock_fds=(3,4),scope_unit=UNIT)
  self.assertEqual(seen[0]['scope_unit'],UNIT)
  self.assertEqual(seen[0]['lock_fds'],(3,4))
 def test_scope_observation_must_include_identity(self):
  class Proc:
   pid=999991
   returncode=0
   def communicate(self,timeout=None):return b'',b''
  def no_group(*args):raise ProcessLookupError()
  with self.assertRaisesRegex(RuntimeError,'not independently empty'):
   m.run_bounded_receive_group(['receiver'],stdin=object(),timeout=10,popen=lambda *a,**k:Proc(),kill_group=no_group,clock=lambda:0,scope_unit=UNIT,scope_query=lambda u:{'active_state':'inactive','tasks_current':0})
if __name__=='__main__':unittest.main(verbosity=2)
