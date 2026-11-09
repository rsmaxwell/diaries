import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-cycle-entry.py'
spec = importlib.util.spec_from_file_location('cycle_entry', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp':'20261030-170009Z', 'uuid':'a'}
B = {'timestamp':'20261101-140039Z', 'uuid':'b'}

class Tests(unittest.TestCase):
    def test_review_does_not_mutate(self):
        calls=[]
        def invoke(args):
            calls.append(args)
            if '--inspect' in args:return {'status':'local-source-state-only','authorizes_transfer':False,'state':{'established':A,'pending':None,'previous':None}}
            return {'status':'review-only','state_changed':False}
        self.assertEqual(m.cycle(B['timestamp'],call=invoke)['status'],'cycle-review-only')
        self.assertEqual(len(calls),2)
    def test_full_prepared_cycle(self):
        actions=[]
        def invoke(args):
            actions.append(args[-1] if args[0] == m.SENDER else args[-1] if '--review-only' in args else 'prepare')
            if '--inspect' in args:return {'status':'local-source-state-only','authorizes_transfer':False,'state':{'established':A,'pending':None,'previous':None}}
            if '--review-only' in args:return {'status':'review-only','state_changed':False}
            if '--execute-preparation' in args:return {'status':'prepared-checkpoint','source':{'ok':1},'receiver':{'ok':1}}
            state={'established':B,'pending':None,'previous':None}
            return {'status':'prepared-cycle-ready','source_state':state,'receiver_state':state,'authorizes_prune':False,'authorizes_release':False}
        self.assertEqual(m.cycle(B['timestamp'],execute=True,call=invoke)['status'],'cycle-ready')
        self.assertEqual(len(actions),4)
    def test_pending_refuses_without_transfer(self):
        def invoke(args):return {'status':'local-source-state-only','authorizes_transfer':False,'state':{'established':A,'pending':B,'previous':None}}
        with self.assertRaisesRegex(m.Refused,'no resend'):m.cycle(B['timestamp'],execute=True,call=invoke)
    def test_invalid_target_refuses(self):
        with self.assertRaisesRegex(m.Refused,'invalid'):m.cycle('../bad')
    def test_previous_needs_ack(self):
        def invoke(args):return {'status':'local-source-state-only','authorizes_transfer':False,'state':{'established':A,'pending':None,'previous':B}}
        self.assertEqual(m.cycle(B['timestamp'],call=invoke)['status'],'previous-acknowledgement-required')

if __name__=='__main__':unittest.main(verbosity=2)
