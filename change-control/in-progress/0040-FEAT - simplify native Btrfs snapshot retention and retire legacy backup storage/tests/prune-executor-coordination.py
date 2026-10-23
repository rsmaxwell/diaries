import importlib.util, importlib.machinery, unittest, sys
from pathlib import Path
module_path=Path(sys.argv[1])
loader=importlib.machinery.SourceFileLoader('receiver_under_test',str(module_path))
spec=importlib.util.spec_from_loader(loader.name,loader)
m=importlib.util.module_from_spec(spec);loader.exec_module(m)
P='20261023-030037Z'; U='fdcabd00-aa98-7647-bd3a-de5e23186d38'; C='20261009-170001Z'
def plan(s=P,u=U):
 return {'snapshot':s,'source_uuid':u,'candidates':[C], 'authorizes_prune':False,'deletion_executed':False}
class Tests(unittest.TestCase):
 def run_candidate(self,planner=plan,verify=None,transaction=None,stamp=P,uuid=U,candidate=C):
  events=[]
  def v(*args): events.append('pin')
  def t(*args,**kw): events.append('transaction');kw['verify_source_pin']()
  result=m.execute_candidate_transaction_locked(stamp,uuid,candidate,planner=planner,verify_pin=verify or v,transaction=transaction or t)
  return result,events
 def test_success_order(self):
  result,events=self.run_candidate();self.assertEqual(events,['pin','transaction','pin']);self.assertTrue(result['transaction_completed'])
 def test_retained_refused(self):
  with self.assertRaisesRegex(RuntimeError,'Candidate not approved'):
   self.run_candidate(planner=lambda *a:{**plan(),'candidates':[]})
 def test_parent_refused(self):
  with self.assertRaisesRegex(RuntimeError,'Invalid candidate'):
   self.run_candidate(candidate=P)
 def test_changed_plan_refused_before_transaction(self):
  n=[0];events=[]
  def p(*args):
   n[0]+=1
   return plan() if n[0]==1 else {**plan(),'candidates':[]}
  with self.assertRaisesRegex(RuntimeError,'changed'):
   self.run_candidate(planner=p,transaction=lambda *a,**kw:events.append('called'))
  self.assertEqual(events,[])
 def test_missing_pin_refuses_transaction(self):
  events=[]
  def v(*a):raise RuntimeError('source unavailable')
  with self.assertRaisesRegex(RuntimeError,'source unavailable'):
   self.run_candidate(verify=v,transaction=lambda *a,**k:events.append('called'))
  self.assertEqual(events,[])
 def test_transaction_failure_propagates(self):
  def fail(*a,**kw):raise RuntimeError('pending journal preserved')
  with self.assertRaisesRegex(RuntimeError,'pending journal preserved'):
   self.run_candidate(transaction=fail)
 def test_authority_claim_refused(self):
  with self.assertRaisesRegex(RuntimeError,'not approved'):
   self.run_candidate(planner=lambda *a:{**plan(),'authorizes_prune':True})
 def test_no_cli_executor(self):
  text=module_path.read_text();self.assertNotIn("parser.add_argument('--execute-prune'",text)
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
