import importlib.util,sys,unittest,io,json
from importlib.machinery import SourceFileLoader
from pathlib import Path
paths=list(map(Path,sys.argv[1:]))
def load(path,name):
 loader=SourceFileLoader(name,str(path));spec=importlib.util.spec_from_loader(name,loader);mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;loader.exec_module(mod);return mod
sender=load(paths[0],'candidate_sender')
receiver=load(paths[1],'candidate_receiver')
P='20261023-030037Z';C='20261020-030026Z';U='fdcabd00-aa98-7647-bd3a-de5e23186d38'
def plan(*a):return {'candidates':[C], 'authorizes_prune':False,'deletion_executed':False}
def response(nonce='a'*64,candidate=C):return io.StringIO(json.dumps({'kind':'candidate-pin-response','nonce':nonce,'snapshot':P,'source_uuid':U,'candidate':candidate})+'\n')
class Contract(unittest.TestCase):
 def test_valid_session(self):
  original=receiver.secrets.token_hex;receiver.secrets.token_hex=lambda n:'a'*(n*2)
  try:
   output=io.StringIO(); result=receiver.candidate_session_check(P,U,C,incoming=response(),outgoing=output,planner=plan)
   self.assertFalse(result['authorizes_prune']);self.assertFalse(result['deletion_executed']);self.assertEqual(len(output.getvalue().splitlines()),2)
  finally:receiver.secrets.token_hex=original
 def test_candidate_not_retained_policy(self):
  with self.assertRaises(RuntimeError):receiver.candidate_session_check(P,U,C,incoming=response(),outgoing=io.StringIO(),planner=lambda *a:{'candidates':[],'authorizes_prune':False,'deletion_executed':False})
 def test_candidate_equal_parent_rejected(self):
  with self.assertRaises(RuntimeError):receiver.candidate_session_check(P,U,P,incoming=response(),outgoing=io.StringIO(),planner=plan)
 def test_wrong_response_rejected(self):
  original=receiver.secrets.token_hex;receiver.secrets.token_hex=lambda n:'a'*(n*2)
  try:
   with self.assertRaises(RuntimeError):receiver.candidate_session_check(P,U,C,incoming=response(candidate='20261019-030038Z'),outgoing=io.StringIO(),planner=plan)
  finally:receiver.secrets.token_hex=original
 def test_changed_retention_rejected(self):
  calls=[0]
  def shifting(*a):
   calls[0]+=1
   return {'candidates':[C] if calls[0]==1 else [],'authorizes_prune':False,'deletion_executed':False}
  original=receiver.secrets.token_hex;receiver.secrets.token_hex=lambda n:'a'*(n*2)
  try:
   with self.assertRaises(RuntimeError):receiver.candidate_session_check(P,U,C,incoming=response(),outgoing=io.StringIO(),planner=shifting)
  finally:receiver.secrets.token_hex=original
 def test_sender_rejects_wrong_nonce(self):
  with self.assertRaises(RuntimeError):sender.validate_candidate_challenge({'kind':'candidate-pin-challenge','nonce':'abc','candidate':C,'snapshot':P,'source_uuid':U},P,U,C)
 def test_sender_rejects_wrong_candidate(self):
  with self.assertRaises(RuntimeError):sender.validate_candidate_challenge({'kind':'candidate-pin-challenge','nonce':'a'*64,'candidate':P,'snapshot':P,'source_uuid':U},P,U,C)
 def test_privileged_delete_not_called(self):
  for f in (sender,receiver):
   text=Path(f.__file__).read_text()
   self.assertNotIn("local('delete-receiver'",text)
   self.assertNotIn("'--role', 'delete-receiver'",text)
 def test_no_executor_flag(self):
  self.assertNotIn('--execute-prune',paths[0].read_text()+paths[1].read_text())
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
