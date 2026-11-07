#!/usr/bin/env python3
"""Fail-closed combined committed-cycle completion tests."""
import importlib.util
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-sender-command.py'
spec = importlib.util.spec_from_file_location('fixed_sender', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
A={'timestamp':'20261030-030033Z','uuid':'a'*36}
B={'timestamp':'20261030-170009Z','uuid':'b'*36}
pinned={'schema':1,'established':B,'previous':A,'pending':None}
ready={'schema':1,'established':B,'previous':None,'pending':None}

def result(status,state):
    return {'status':status,'source_state':state,'receiver_state':state,
            'authorizes_prune':False,'authorizes_release':False}

class Tests(unittest.TestCase):
    def test_complete_two_stages(self):
        calls=[]
        def invoke(mode):
            calls.append(mode)
            return result('both-promoted-previous-pinned',pinned) if mode=='resume-committed' else result('both-previous-acknowledged',ready)
        self.assertEqual(mod.complete_committed(invoke=invoke)['status'],'committed-cycle-ready')
        self.assertEqual(calls,['resume-committed','acknowledge-previous'])
    def test_refuses_before_second_stage_on_uncertain_promotion(self):
        calls=[]
        def invoke(mode):
            calls.append(mode)
            return result('unknown',pinned)
        with self.assertRaises(mod.OperatorRefused):mod.complete_committed(invoke=invoke)
        self.assertEqual(calls,['resume-committed'])
    def test_connection_failure_propagates(self):
        def invoke(_):raise OSError('peer offline')
        with self.assertRaises(OSError):mod.complete_committed(invoke=invoke)
    def test_refuse_receiver_mismatch(self):
        def invoke(mode):
            d=result('both-promoted-previous-pinned',pinned)
            d['receiver_state']=ready
            return d
        with self.assertRaises(mod.OperatorRefused):mod.complete_committed(invoke=invoke)
    def test_refuse_release_authority(self):
        def invoke(mode):
            d=result('both-promoted-previous-pinned',pinned)
            d['authorizes_release']=True
            return d
        with self.assertRaises(mod.OperatorRefused):mod.complete_committed(invoke=invoke)
    def test_ack_failure_propagates(self):
        def invoke(mode):
            if mode=='acknowledge-previous':raise RuntimeError('SSH lost')
            return result('both-promoted-previous-pinned',pinned)
        with self.assertRaises(RuntimeError):mod.complete_committed(invoke=invoke)
    def test_refuse_post_ack_pending(self):
        def invoke(mode):
            return result('both-promoted-previous-pinned',pinned) if mode=='resume-committed' else result('both-previous-acknowledged',pinned)
        with self.assertRaises(mod.OperatorRefused):mod.complete_committed(invoke=invoke)
    def test_cli_gated_not_scheduled(self):
        self.assertIn("--complete-committed",SOURCE.read_text())
        manifest=(SOURCE.parents[1]/'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertNotIn('systemd',manifest)

if __name__=='__main__':unittest.main(verbosity=2)
