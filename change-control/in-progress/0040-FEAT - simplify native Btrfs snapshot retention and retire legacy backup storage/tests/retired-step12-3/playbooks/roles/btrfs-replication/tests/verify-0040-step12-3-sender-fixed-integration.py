#!/usr/bin/env python3
"""Source-level integration: fixed commands -> independent exits -> finalise gate."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock

BASE=Path(__file__).resolve().parents[1]/'files'
def load(filename):
    spec=importlib.util.spec_from_file_location('integration_'+filename.replace('-','_'),BASE/filename)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module
sender=load('btrfs-agreed-parent-sender-transaction.py')
commands=load('btrfs-agreed-parent-fixed-commands.py')
A={'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B={'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
ACK={'status':'receiver-receipt-committed-promotion-pending', 'parent':A,'candidate':B,
     'receipt_committed':True,'state_changed':False,'authorizes_prune':False,'authorizes_release':False}

class Tests(unittest.TestCase):
    def setUp(self):
        self.stream=Mock()
        self.stream.run_binary_send_ssh.return_value={'source_send_exit':0,'ssh_exit':0}
        self.finalise=Mock(return_value=ACK)
        self.receipt=Mock(return_value=True)
        self.pin=Mock(return_value=True)
    def execute(self):
        return sender.send_then_finalize_fixed(A,B,pinned_parent_verified=self.pin,
            command_builder=commands,stream_adapter=self.stream,
            finalise_ssh=self.finalise,verify_final_receipt=self.receipt)
    def test_fixed_order_and_commands(self):
        result=self.execute()
        send,ssh=commands.receive_commands(A,B)
        self.stream.run_binary_send_ssh.assert_called_once_with(send,ssh,timeout_seconds=1800)
        self.finalise.assert_called_once_with(commands.finalise_command(A,B),A,B)
        self.receipt.assert_called_once_with(A,B)
        self.assertEqual(result['status'],'receiver-committed-promotion-pending')
        self.assertFalse(result['authorizes_prune'])
    def test_sender_failure_blocks_finalise(self):
        self.stream.run_binary_send_ssh.return_value={'source_send_exit':1,'ssh_exit':0}
        with self.assertRaises(sender.SenderTransactionRefused): self.execute()
        self.finalise.assert_not_called()
    def test_transport_uncertainty_blocks_finalise(self):
        self.stream.run_binary_send_ssh.side_effect=RuntimeError('timed out')
        with self.assertRaises(sender.SenderTransactionRefused): self.execute()
        self.finalise.assert_not_called()
    def test_bad_ack_fails_closed(self):
        self.finalise.return_value={'status':'success'}
        with self.assertRaises(sender.SenderTransactionRefused): self.execute()
        self.receipt.assert_not_called()
    def test_pin_failure_no_transfer(self):
        self.pin.return_value=False
        with self.assertRaises(sender.SenderTransactionRefused): self.execute()
        self.stream.run_binary_send_ssh.assert_not_called()
    def test_receipt_failure_blocks_promotion(self):
        self.receipt.return_value=False
        with self.assertRaises(sender.SenderTransactionRefused): self.execute()
    def test_no_public_cli(self):
        self.assertFalse(hasattr(sender,'main'))
if __name__=='__main__': unittest.main(verbosity=2)
