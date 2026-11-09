import importlib.util
from pathlib import Path
import unittest

path=Path(__file__).resolve().parents[1]/'files/btrfs-agreed-parent-cycle-entry.py'
spec=importlib.util.spec_from_file_location('entry_recovery',path)
entry=importlib.util.module_from_spec(spec); spec.loader.exec_module(entry)
A={'timestamp':'20261030-170009Z','uuid':'a'}
B={'timestamp':'20261101-140039Z','uuid':'b'}

class Recovery(unittest.TestCase):
    def initial(self, pending=None, previous=None):
        return {'schema':1,'established':A if pending else B,'pending':pending,'previous':previous}
    def harness(self, state, response=None):
        calls=[]
        def call(args):
            calls.append(args)
            if args==[entry.SENDER,'--inspect']:
                return {'status':'local-source-state-only','authorizes_transfer':False,'state':state}
            if response is None: raise entry.Refused('receiver has no authenticated committed receipt')
            return response
        return calls,call
    def done(self, expected, status):
        final={'schema':1,'established':expected,'pending':None,'previous':None}
        return {'status':status,'source_state':final,'receiver_state':final,
                'authorizes_prune':False,'authorizes_release':False}
    def test_committed_pending_recovers_without_send(self):
        calls,call=self.harness(self.initial(pending=B),self.done(B,'committed-cycle-ready'))
        result=entry.auto_cycle(execute=True,call=call)
        self.assertEqual(result['status'],'recovered-cycle-ready')
        self.assertEqual(calls,[[entry.SENDER,'--inspect'],[entry.SENDER,'--complete-committed']])
    def test_previous_ack_recovers_without_send(self):
        calls,call=self.harness(self.initial(previous=A),self.done(B,'both-previous-acknowledged'))
        self.assertEqual(entry.auto_cycle(execute=True,call=call)['status'],'recovered-cycle-ready')
        self.assertEqual(calls[-1],[entry.SENDER,'--acknowledge-previous'])
    def test_uncommitted_pending_stops_without_retry(self):
        calls,call=self.harness(self.initial(pending=B))
        with self.assertRaises(entry.Refused): entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),2)
    def test_mismatched_peer_refused(self):
        response=self.done(B,'committed-cycle-ready'); response['receiver_state']={}
        _,call=self.harness(self.initial(pending=B),response)
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
    def test_wrong_candidate_refused(self):
        _,call=self.harness(self.initial(pending=B),self.done(A,'committed-cycle-ready'))
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
    def test_unauthorized_prune_refused(self):
        response=self.done(B,'committed-cycle-ready');response['authorizes_prune']=True
        _,call=self.harness(self.initial(pending=B),response)
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
    def test_both_pending_previous_refused(self):
        calls,call=self.harness(self.initial(pending=B,previous=A))
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),1)
    def test_recovery_review_only(self):
        calls,call=self.harness(self.initial(pending=B))
        result=entry.recovery_cycle(execute=False,call=call)
        self.assertEqual(result['status'],'recovery-review-only')
        self.assertEqual(len(calls),1)
    def test_recovery_idle_no_mutation(self):
        calls,call=self.harness(self.initial())
        self.assertEqual(entry.recovery_cycle(execute=True,call=call)['status'],'already-idle')
        self.assertEqual(len(calls),1)
    def test_missing_uuid_refused(self):
        calls,call=self.harness(self.initial(pending={'timestamp':B['timestamp']}))
        with self.assertRaises(entry.Refused):entry.auto_cycle(execute=True,call=call)
        self.assertEqual(len(calls),1)

if __name__=='__main__':unittest.main(verbosity=2)
