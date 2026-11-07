#!/usr/bin/env python3
import importlib.util
import unittest
from pathlib import Path
from unittest.mock import Mock

path = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-workflow.py'
spec = importlib.util.spec_from_file_location('workflow0040', path)
w = importlib.util.module_from_spec(spec); spec.loader.exec_module(w)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261101-140039Z','uuid':'69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'}
PRE = {'schema':1,'established':A,'pending':B,'previous':None}
POST = {'schema':1,'established':B,'pending':None,'previous':A}
class Harness:
    def __init__(self, state=PRE):
        self.state = dict(state)
        self.observer = Mock(lock=Mock())
        self.states = Mock(snapshot=lambda x: x, validate=lambda x: x, load=lambda *a, **k: self.state)
        self.states.promote.side_effect=lambda s: dict(POST)
        def save(*args, **kwargs): self.state = dict(args[1])
        self.states.save.side_effect=save
        self.evidence = Mock(verify_source=lambda x: dict(x,verified=True))
        self.commands = object()
        self.execution = Mock(return_value={'status':'receiver-committed-promotion-pending','parent':A,'candidate':B,
                                            'authorizes_prune':False,'authorizes_release':False,'authorizes_transition':False})
        self.receipt = Mock(return_value=True)
        self.promote = Mock()
        self.promote.receiver_readback.return_value=dict(POST)
        self.promote.promote_source_locked.side_effect=lambda *a,**k: (save(None,POST), dict(POST))[1]
    def run(self, mode):
        return w.run(A,B, mode=mode, observer=self.observer, state_module=self.states, evidence=self.evidence,
                     execution=self.execution, receipt_reader=self.receipt,
                     promotion_runtime=self.promote, commands=self.commands)
class Cases(unittest.TestCase):
    def test_execute_order_and_pins(self):
        h=Harness(); result=h.run('execute'); self.assertEqual(result['source_state'], POST)
        self.assertFalse(result['authorizes_prune']); self.assertFalse(result['authorizes_release'])
        h.execution.assert_called_once(); h.promote.receiver_promote.assert_called_once()
        self.assertEqual(h.promote.receiver_readback.call_count,1)
    def test_resume_does_not_send(self):
        h=Harness(); self.assertEqual(h.run('resume-committed')['status'],'both-promoted-previous-pinned')
        h.execution.assert_not_called()
    def test_source_already_promoted_only_reads(self):
        h=Harness(POST); self.assertEqual(h.run('resume-committed')['status'],'both-promoted-previous-pinned')
        h.execution.assert_not_called(); h.promote.receiver_promote.assert_not_called(); h.promote.promote_source_locked.assert_not_called()
    def test_ambiguous_source_state_rejected(self):
        h=Harness(dict(PRE,pending=None)); self.assertRaises(w.WorkflowRefused,h.run,'execute'); h.execution.assert_not_called()
    def test_lost_receipt_refuses_mutations(self):
        h=Harness(); h.receipt.return_value=False
        self.assertRaises(w.WorkflowRefused,h.run,'resume-committed'); h.promote.receiver_promote.assert_not_called()
    def test_peer_uncertain_does_not_promote_source(self):
        h=Harness(); h.promote.receiver_readback.return_value=dict(PRE)
        self.assertRaises(w.WorkflowRefused,h.run,'resume-committed'); h.promote.promote_source_locked.assert_not_called()
    def test_resume_requires_prepared_or_promoted(self):
        h=Harness(dict(PRE,established=B)); self.assertRaises(w.WorkflowRefused,h.run,'resume-committed')
    def test_no_automatic_retry_after_transfer_uncertain(self):
        h=Harness(); h.execution.side_effect=RuntimeError('lost ssh')
        self.assertRaises(RuntimeError,h.run,'execute'); h.execution.assert_called_once(); h.promote.receiver_promote.assert_not_called()
    def test_noncanonical_path_rejected(self):
        h=Harness(); self.assertRaises(w.WorkflowRefused,w.run,A,B,mode='execute',observer=h.observer,state_module=h.states,evidence=h.evidence,
          execution=h.execution,receipt_reader=h.receipt,promotion_runtime=h.promote,commands=h.commands,state_path='/tmp/state')
if __name__=='__main__': unittest.main(verbosity=2)
