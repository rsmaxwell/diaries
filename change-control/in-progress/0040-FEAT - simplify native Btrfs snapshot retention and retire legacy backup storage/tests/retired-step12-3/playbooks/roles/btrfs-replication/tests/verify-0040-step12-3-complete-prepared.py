#!/usr/bin/env python3
"""A prepared cycle must not be repeated after an uncertain send."""
import importlib.util
from pathlib import Path
import unittest

SOURCE=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-sender-command.py'
spec=importlib.util.spec_from_file_location('sender',SOURCE)
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
A={'timestamp':'20261030-030033Z','uuid':'a'*36}
B={'timestamp':'20261030-170009Z','uuid':'b'*36}
PROMOTED={'schema':1,'established':B,'pending':None,'previous':A}
READY={'schema':1,'established':B,'pending':None,'previous':None}

def outcome(status,state):
    return {'status':status,'source_state':state,'receiver_state':state,'authorizes_prune':False,'authorizes_release':False}

class Tests(unittest.TestCase):
    def test_complete_prepared_cycle(self):
        calls=[]
        def invoke(mode):
            calls.append(mode)
            return outcome('both-promoted-previous-pinned',PROMOTED) if mode=='execute' else outcome('both-previous-acknowledged',READY)
        self.assertEqual(mod.complete_prepared(invoke=invoke)['status'],'prepared-cycle-ready')
        self.assertEqual(calls,['execute','acknowledge-previous'])
    def test_no_ack_after_uncertain_transfer(self):
        calls=[]
        def invoke(mode):
            calls.append(mode)
            raise OSError('network lost')
        with self.assertRaises(OSError):mod.complete_prepared(invoke=invoke)
        self.assertEqual(calls,['execute'])
    def test_reject_unpromoted(self):
        calls=[]
        def invoke(mode):
            calls.append(mode)
            return outcome('other',PROMOTED)
        with self.assertRaises(mod.OperatorRefused):mod.complete_prepared(invoke=invoke)
        self.assertEqual(calls,['execute'])
    def test_reject_mismatched_receiver(self):
        def invoke(mode):
            result=outcome('both-promoted-previous-pinned',PROMOTED)
            result['receiver_state']=READY
            return result
        with self.assertRaises(mod.OperatorRefused):mod.complete_prepared(invoke=invoke)
    def test_no_prune_authority(self):
        def invoke(mode):
            r=outcome('both-promoted-previous-pinned',PROMOTED)
            r['authorizes_prune']=True
            return r
        with self.assertRaises(mod.OperatorRefused):mod.complete_prepared(invoke=invoke)
    def test_bad_final_state_refused(self):
        def invoke(mode):
            return outcome('both-promoted-previous-pinned',PROMOTED) if mode=='execute' else outcome('both-previous-acknowledged',PROMOTED)
        with self.assertRaises(mod.OperatorRefused):mod.complete_prepared(invoke=invoke)
    def test_not_scheduled(self):
        self.assertIn('--complete-prepared',SOURCE.read_text())
        manifest=(SOURCE.parents[1]/'tasks/agreed-parent-runtime.yaml').read_text()
        self.assertNotIn('systemd',manifest)
if __name__=='__main__':unittest.main(verbosity=2)
