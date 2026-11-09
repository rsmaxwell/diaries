import importlib.machinery
import importlib.util
import io
import json
import sys
import unittest
from unittest.mock import patch

loader=importlib.machinery.SourceFileLoader('receiver', sys.argv[1]); spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec); loader.exec_module(m)
sys.argv = [sys.argv[0]]
P='20261023-030037Z'; U='fdcabd00-aa98-7647-bd3a-de5e23186d38'; C='20261012-100003Z'
def plan(p,u):
    return {'snapshot':p,'source_uuid':u,'authorizes_prune':False,'deletion_executed':False,'candidates':[C]}
class Duplex:
    def __init__(self,wrong=False,stop_after=2): self.wrong=wrong;self.stop_after=stop_after;self.requests=[];self.buf=""
    def write(self,line):
        self.buf += line
        while "\n" in self.buf:
            line,self.buf=self.buf.split("\n",1)
            if line: self.requests.append(json.loads(line))
    def flush(self): pass
    def readline(self,n):
        if len(self.requests)>self.stop_after: return ''
        req=self.requests[-1]
        return json.dumps({'kind':'transaction-pin-response','nonce':'bad' if self.wrong else req['nonce'],
                           'snapshot':P,'source_uuid':U,'candidate':C})+'\n'
class Tests(unittest.TestCase):
    def test_success_requires_two_distinct_roundtrips_and_manager_callback(self):
        d=Duplex();called=[]
        def trans(c,**kw):
            self.assertEqual(kw['expected_parent_uuid'],U)
            self.assertEqual(c,C)
            kw['verify_source_pin']();called.append('manager')
        result=m.run_source_held_transaction_locked(P,U,C,incoming=d,outgoing=d,planner=plan,transaction=trans)
        self.assertEqual(called,['manager']);self.assertEqual([x['kind'] for x in d.requests],['transaction-pin-challenge','transaction-pin-challenge','transaction-completed'])
        self.assertNotEqual(d.requests[0]['nonce'],d.requests[1]['nonce'])
        self.assertTrue(result['journal_transaction_completed'])
    def test_missing_second_challenge_fails_before_manager_completion(self):
        d=Duplex(stop_after=1)
        def trans(c,**kw): kw['verify_source_pin']()
        with self.assertRaisesRegex(RuntimeError,'Missing or oversized'):
            m.run_source_held_transaction_locked(P,U,C,incoming=d,outgoing=d,planner=plan,transaction=trans)
        self.assertFalse(any(x.get('kind')=='transaction-completed' for x in d.requests))
    def test_wrong_nonce_refused(self):
        d=Duplex(wrong=True);called=[]
        with self.assertRaisesRegex(RuntimeError,'Invalid source pin response'):
            m.run_source_held_transaction_locked(P,U,C,incoming=d,outgoing=d,planner=plan,transaction=lambda *a,**k:called.append(True))
        self.assertEqual(called,[])
    def test_retained_candidate_refused_before_challenge(self):
        d=Duplex()
        with self.assertRaisesRegex(RuntimeError,'Candidate not approved'):
            m.run_source_held_transaction_locked(P,U,C,incoming=d,outgoing=d,planner=lambda p,u:{**plan(p,u),'candidates':[]},transaction=lambda *a,**k:None)
        self.assertEqual(d.requests,[])
    def test_manager_exception_has_no_success_response(self):
        d=Duplex()
        def trans(c,**kw): raise RuntimeError('journal failure')
        with self.assertRaisesRegex(RuntimeError,'journal failure'):
            m.run_source_held_transaction_locked(P,U,C,incoming=d,outgoing=d,planner=plan,transaction=trans)
        self.assertFalse(any(x.get('kind')=='transaction-completed' for x in d.requests))
    def test_no_public_command_line_integration(self):
        import inspect
        source=inspect.getsource(m.main)
        self.assertNotIn('run_source_held_transaction_locked(',source)
        self.assertNotIn('delete-receiver',source)
if __name__=='__main__':unittest.main(verbosity=2)
