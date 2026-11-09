import importlib.machinery, importlib.util, pathlib, sys, unittest
from unittest import mock

def load(path, name):
    loader=importlib.machinery.SourceFileLoader(name,path)
    spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;loader.exec_module(mod);return mod
sender=load(sys.argv[1],'sender_session_contract')
receiver=load(sys.argv[2],'receiver_session_contract')
STAMP='20261023-030037Z';UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38';N='a'*64
class Tests(unittest.TestCase):
 def test_valid_challenge(self):
  self.assertEqual(sender.validate_session_challenge({'kind':'pin-challenge','nonce':N,'snapshot':STAMP,'source_uuid':UUID},STAMP,UUID),N)
 def test_wrong_challenge_uuid(self):
  with self.assertRaises(RuntimeError):sender.validate_session_challenge({'kind':'pin-challenge','nonce':N,'snapshot':STAMP,'source_uuid':'other'},STAMP,UUID)
 def test_short_nonce_rejected(self):
  with self.assertRaises(RuntimeError):sender.validate_session_challenge({'kind':'pin-challenge','nonce':'abc','snapshot':STAMP,'source_uuid':UUID},STAMP,UUID)
 def test_valid_response(self):receiver.verify_session_response({'kind':'pin-response','nonce':N,'snapshot':STAMP,'source_uuid':UUID},stamp=STAMP,uuid=UUID,nonce=N)
 def test_wrong_nonce_rejected(self):
  with self.assertRaises(RuntimeError):receiver.verify_session_response({'kind':'pin-response','nonce':'b'*64,'snapshot':STAMP,'source_uuid':UUID},stamp=STAMP,uuid=UUID,nonce=N)
 def test_wrong_parent_rejected(self):
  with self.assertRaises(RuntimeError):receiver.verify_session_response({'kind':'pin-response','nonce':N,'snapshot':'20261022-030000Z','source_uuid':UUID},stamp=STAMP,uuid=UUID,nonce=N)
 def test_live_session_with_mocked_parent(self):
  import io,json
  outgoing=io.StringIO()
  with mock.patch.object(receiver,'check_protected_parent',return_value={'snapshot':STAMP,'source_uuid':UUID}), mock.patch.object(receiver.secrets,'token_hex',return_value=N):
   result=receiver.prune_session_check(STAMP,UUID,incoming=io.StringIO(json.dumps({'kind':'pin-response','nonce':N,'snapshot':STAMP,'source_uuid':UUID})+'\n'),outgoing=outgoing)
  self.assertFalse(result['deletion_executed']);self.assertFalse(result['authorizes_prune']);self.assertEqual(len(outgoing.getvalue().splitlines()),2)
 def test_missing_response_fails_closed(self):
  import io
  with mock.patch.object(receiver,'check_protected_parent',return_value={}),mock.patch.object(receiver.secrets,'token_hex',return_value=N):
   with self.assertRaises(RuntimeError):receiver.prune_session_check(STAMP,UUID,incoming=io.StringIO(''),outgoing=io.StringIO())
 def test_no_delete_cli(self):
  text=pathlib.Path(sys.argv[2]).read_text()
  self.assertNotIn("add_argument('--delete-receiver'",text)
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
