#!/usr/bin/python3
import importlib.util
import pathlib
import unittest
P=pathlib.Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-transfer-session.py'
s=importlib.util.spec_from_file_location('transfer04o',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
GOOD=dict(source_lock=True,receiver_locks=True,data_authenticated=True,control_authenticated=True,peer_binding_verified=True,deadline_active=True)
DONE=dict(sender_rc=0,receiver_rc=0,stream_verified=True,challenge_consumed=True,receiver_locks=True,receipt_committed=True)
class Tests(unittest.TestCase):
 def test_ssh_identity(self):
  d=m.argv_pair(A,B,data_endpoint='/usr/local/libexec/btrfs-agreed-parent-receive-data-session.py',control_endpoint='/usr/local/libexec/btrfs-agreed-parent-receive-control-session.py')
  for cmd in d.values():self.assertEqual(cmd[:len(m.SSH)],m.SSH);self.assertNotEqual(cmd[0],'ssh');self.assertEqual(cmd[len(m.SSH):len(m.SSH)+2],('sudo','-n'))
 def test_remote_command_rejected(self):
  with self.assertRaises(m.SessionRefused):m.argv_pair(A,B,data_endpoint='/bin/sh',control_endpoint='anything')
 def test_wrong_identity(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle({'timestamp':'bad','uuid':'a'},B)
 def test_wrong_order(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle(B,A)
 def test_new_token(self):self.assertNotEqual(m.Lifecycle(A,B).token,m.Lifecycle(A,B).token)
 def test_bad_token(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle(A,B,token='test')
 def test_missing_source_lock(self):
  x=m.Lifecycle(A,B);p=dict(GOOD,source_lock=False)
  with self.assertRaises(m.SessionRefused):x.start(**p)
  self.assertEqual(x.phase,'failed')
 def test_missing_peer_binding(self):
  x=m.Lifecycle(A,B)
  with self.assertRaises(m.SessionRefused):x.start(**dict(GOOD,peer_binding_verified=False))
 def test_missing_deadline(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle(A,B).start(**dict(GOOD,deadline_active=False))
 def test_missing_receiver_lock(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle(A,B).start(**dict(GOOD,receiver_locks=False))
 def test_repeated_start(self):
  x=m.Lifecycle(A,B);x.start(**GOOD)
  with self.assertRaises(m.SessionRefused):x.start(**GOOD)
 def test_complete_success(self):
  x=m.Lifecycle(A,B);x.start(**GOOD);result=x.complete(**DONE)
  self.assertEqual(x.phase,'completed');self.assertFalse(result['authorizes_release'])
 def test_completion_missing_receipt(self):
  x=m.Lifecycle(A,B);x.start(**GOOD)
  with self.assertRaises(m.SessionRefused):x.complete(**dict(DONE,receipt_committed=False))
 def test_completion_failed_sender(self):
  x=m.Lifecycle(A,B);x.start(**GOOD)
  with self.assertRaises(m.SessionRefused):x.complete(**dict(DONE,sender_rc=1))
 def test_bool_rc_rejected(self):
  x=m.Lifecycle(A,B);x.start(**GOOD)
  with self.assertRaises(m.SessionRefused):x.complete(**dict(DONE,sender_rc=False))
 def test_completion_before_start(self):
  with self.assertRaises(m.SessionRefused):m.Lifecycle(A,B).complete(**DONE)
 def test_no_retry_after_failure(self):
  x=m.Lifecycle(A,B);x.fail()
  with self.assertRaises(m.SessionRefused):x.start(**GOOD)
if __name__=='__main__':unittest.main(verbosity=2)
