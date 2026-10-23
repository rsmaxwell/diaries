import ast, unittest, io, json, sys
from pathlib import Path
p=Path(sys.argv[1]) if len(sys.argv) > 1 else Path('/home/richard/playbooks/roles/btrfs-replication/files/btrfs-native-push.py')
sys.argv=sys.argv[:1]
tree=ast.parse(p.read_text()); names=['answer_transaction_challenges','validate_session_challenge']
ns={'require':lambda x,m:None if x else (_ for _ in ()).throw(RuntimeError(m)),'STAMP':__import__('re').compile(r'^[0-9]{8}-[0-9]{6}Z$'),'re':__import__('re'),'json':json,'local':lambda *a:None}
exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name in names],type_ignores=[]),str(p),'exec'),ns)
S='20261023-030037Z'; U='fdcabd00-aa98-7647-bd3a-de5e23186d38'; C='20261022-030026Z'
class Proc:
 def __init__(self,lines,rc=0): self.stdout=io.StringIO(''.join(json.dumps(x)+'\n' for x in lines));self.stdin=io.StringIO();self.rc=rc
 def wait(self,timeout=None): return self.rc

def challenge(n):return dict(kind='transaction-pin-challenge',snapshot=S,source_uuid=U,candidate=C,nonce=n*64)
def done():return dict(kind='transaction-completed',snapshot=C,protected_parent=S,protected_parent_uuid=U,journal_transaction_completed=True)
class Tests(unittest.TestCase):
 def run_case(self,lines, pin=None, rc=0):
  p=Proc(lines,rc);calls=[]
  def cb(role,stamp):calls.append((role,stamp));return {'source_uuid':U} if pin is None else pin
  return p,calls,lambda:ns['answer_transaction_challenges'](p,S,U,C,protect_pin=cb)
 def test_success_two_roundtrips(self):
  p,c,run=self.run_case([challenge('a'),challenge('b'),done()]);self.assertTrue(run()['journal_transaction_completed']);self.assertEqual(len(c),2);self.assertEqual(len(p.stdin.getvalue().splitlines()),2)
 def test_missing_second_challenge(self):
  p,c,run=self.run_case([challenge('a')]);self.assertRaises(RuntimeError,run)
 def test_duplicate_nonce(self):
  p,c,run=self.run_case([challenge('a'),challenge('a'),done()]);self.assertRaisesRegex(RuntimeError,'Repeated',run)
 def test_wrong_candidate(self):
  bad=challenge('a');bad['candidate']='20261021-030006Z';p,c,run=self.run_case([bad]);self.assertRaises(RuntimeError,run)
 def test_wrong_pin_uuid(self):
  p,c,run=self.run_case([challenge('a')],pin={'source_uuid':'wrong'});self.assertRaises(RuntimeError,run)
 def test_no_success_without_final(self):
  p,c,run=self.run_case([challenge('a'),challenge('b')]);self.assertRaises(RuntimeError,run)
 def test_failure_exit(self):
  p,c,run=self.run_case([challenge('a'),challenge('b'),done()],rc=1);self.assertRaises(RuntimeError,run)
 def test_private_no_cli(self):
  t=ast.parse(Path('/mnt/data/0040-build/roles/btrfs-replication/files/btrfs-native-push.py').read_text());main=next(x for x in t.body if isinstance(x,ast.FunctionDef) and x.name=='main');self.assertNotIn('answer_transaction_challenges',ast.unparse(main))
if __name__=='__main__':unittest.main(verbosity=2)
