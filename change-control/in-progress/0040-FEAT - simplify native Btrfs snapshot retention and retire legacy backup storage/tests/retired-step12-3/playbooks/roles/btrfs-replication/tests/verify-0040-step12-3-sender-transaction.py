#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest

f=pathlib.Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-sender-transaction.py'
spec=importlib.util.spec_from_file_location('txn',f); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
class Test(unittest.TestCase):
 def setUp(self):
  self.calls=[]
  self.pin=lambda a,b:self.calls.append('pin') or True
  self.transfer=lambda a,b:self.calls.append('transfer') or {'source_send_exit':0,'ssh_exit':0}
  self.finish=lambda a,b:self.calls.append('finalise') or {'status':'receiver-receipt-committed-promotion-pending','parent':a,'candidate':b,'receipt_committed':True,'state_changed':False,'authorizes_prune':False,'authorizes_release':False}
  self.verify=lambda a,b:self.calls.append('verify') or True
 def go(self,**kw):
  k=dict(pinned_parent_verified=self.pin,receive_transfer=self.transfer,finalise_authenticated=self.finish,verify_final_receipt=self.verify);k.update(kw)
  return m.send_then_finalize(A,B,**k)
 def test_success_is_not_promotion(self):
  r=self.go();self.assertEqual(self.calls,['pin','transfer','finalise','verify']);self.assertFalse(r['authorizes_transition']);self.assertFalse(r['authorizes_prune']);self.assertTrue(r['source_pin_retained'])
 def test_pin_failure_no_transfer(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(pinned_parent_verified=lambda a,b:False)
  self.assertEqual(self.calls,[])
 def test_sender_failure_no_finalise(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(receive_transfer=lambda a,b:{'source_send_exit':1,'ssh_exit':0})
  self.assertNotIn('finalise',self.calls)
 def test_ssh_failure_no_finalise(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(receive_transfer=lambda a,b:{'source_send_exit':0,'ssh_exit':1})
  self.assertNotIn('finalise',self.calls)
 def test_boolean_exit_rejected(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(receive_transfer=lambda a,b:{'source_send_exit':False,'ssh_exit':0})
 def test_uncertain_transfer_never_finalises(self):
  def fail(a,b):raise TimeoutError()
  with self.assertRaises(m.SenderTransactionRefused): self.go(receive_transfer=fail)
  self.assertEqual(self.calls,['pin'])
 def test_finalisation_exception_uncertain(self):
  def fail(a,b):raise OSError()
  with self.assertRaises(m.SenderTransactionRefused): self.go(finalise_authenticated=fail)
 def test_unsafe_acknowledgement(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(finalise_authenticated=lambda a,b:{'status':'done'})
 def test_final_receipt_readback_required(self):
  with self.assertRaises(m.SenderTransactionRefused): self.go(verify_final_receipt=lambda a,b:False)
 def test_invalid_identities(self):
  with self.assertRaises(m.SenderTransactionRefused): m.send_then_finalize(B,A,pinned_parent_verified=self.pin,receive_transfer=self.transfer,finalise_authenticated=self.finish,verify_final_receipt=self.verify)
 def test_no_public_main(self):self.assertFalse(hasattr(m,'main'))
if __name__=='__main__':unittest.main(verbosity=2)
