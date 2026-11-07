import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-cycle-entry.py'
spec=importlib.util.spec_from_file_location('entry_cycle',path)
entry=importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
A={'timestamp':'20261030-170009Z','uuid':'a'}
B={'timestamp':'20261101-140039Z','uuid':'b'}

class Cases(unittest.TestCase):
    def exercise(self, preparation=None, completion=None, initial=None):
        calls=[]
        idle={'established':A,'pending':None,'previous':None}
        prepared={'schema':1,'established':A,'pending':B,'previous':None}
        final={'schema':1,'established':B,'pending':None,'previous':None}
        def call(args):
            calls.append(args)
            if '--inspect' in args:return {'status':'local-source-state-only','authorizes_transfer':False,'state':initial or idle}
            if '--execute-preparation' in args:return preparation if preparation is not None else {
                'status':'prepared-checkpoint','source':prepared,'receiver':prepared,
                'authorizes_transfer':False,'authorizes_prune':False,'authorizes_release':False}
            if '--complete-prepared' in args:return completion if completion is not None else {
                'status':'prepared-cycle-ready','source_state':final,'receiver_state':final,
                'authorizes_prune':False,'authorizes_release':False}
            if '--complete-committed' in args: raise entry.Refused('no verified committed receipt; no resend')
            self.fail('unexpected command')
        return calls,call
    def test_cycle(self):
        calls,call=self.exercise()
        result=entry.auto_cycle(execute=True,call=call)
        self.assertEqual(result['status'],'cycle-ready')
        self.assertEqual(result['target'],B['timestamp'])
        self.assertEqual([a[-1] for a in calls],['--inspect','--execute-preparation','--complete-prepared'])
        self.assertEqual(calls[1],[entry.PREPARE,'--auto-target','--execute-preparation'])
    def test_none(self):
        calls,call=self.exercise(preparation={'status':'no-eligible-candidate','state_changed':False,'transfer_executed':False})
        self.assertEqual(entry.auto_cycle(execute=True,call=call)['status'],'no-eligible-candidate')
        self.assertEqual(len(calls),2)
    def test_no_send_after_ambiguous_prepare(self):
        calls,call=self.exercise(preparation={'status':'prepared-checkpoint','source':{},'receiver':{}})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),2)
    def test_no_send_after_unauthorised_preparation(self):
        calls,call=self.exercise(preparation={'status':'prepared-checkpoint','source':{'pending':B},'receiver':{'pending':B},'authorizes_transfer':True})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),2)
    def test_stale_preparation_refused(self):
        p={'schema':1,'established':A,'pending':A,'previous':None}
        calls,call=self.exercise(preparation={'status':'prepared-checkpoint','source':p,'receiver':p,'authorizes_transfer':False,'authorizes_prune':False,'authorizes_release':False})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),2)
    def test_uncertain_completion_no_retry(self):
        calls,call=self.exercise(completion={'status':'uncertain'})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),3)
    def test_wrong_final_refused(self):
        wrong={'established':A,'pending':None,'previous':None}
        calls,call=self.exercise(completion={'status':'prepared-cycle-ready','source_state':wrong,'receiver_state':wrong,'authorizes_prune':False,'authorizes_release':False})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
    def test_pending_refuses_before_checkpoint(self):
        calls,call=self.exercise(initial={'established':A,'pending':B,'previous':None})
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),2)
        self.assertEqual(calls[-1],[entry.SENDER,'--complete-committed'])

if __name__=='__main__':unittest.main(verbosity=2)
