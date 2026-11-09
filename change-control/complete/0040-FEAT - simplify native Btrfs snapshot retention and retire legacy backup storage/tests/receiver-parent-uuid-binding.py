import importlib.machinery, importlib.util, pathlib, sys, unittest
sender, manager = map(pathlib.Path, sys.argv[1:3])
def load(name, path):
    loader=importlib.machinery.SourceFileLoader(name,str(path))
    spec=importlib.util.spec_from_loader(name,loader)
    mod=importlib.util.module_from_spec(spec);sys.modules[name]=mod;loader.exec_module(mod)
    return mod
s=load('receiver_binding',sender);m=load('manager_binding',manager)
P='20261023-030037Z'; U='fdcabd00-aa98-7647-bd3a-de5e23186d38'; C='20261009-170001Z'
class Tests(unittest.TestCase):
    def test_coordinator_passes_parent_identity_and_rechecks_pin(self):
        calls=[]
        def plan(*_):return dict(snapshot=P,source_uuid=U,candidates=[C],authorizes_prune=False,deletion_executed=False)
        def verify(*a):self.assertEqual(a,(P,U,C));calls.append('pin')
        def txn(candidate,**kw):
            self.assertEqual(candidate,C)
            self.assertEqual(kw['protected_stamp'],P)
            self.assertEqual(kw['expected_parent_uuid'],U)
            calls.append('transaction');kw['verify_source_pin']()
        result=s.execute_candidate_transaction_locked(P,U,C,planner=plan,verify_pin=verify,transaction=txn)
        self.assertEqual(calls,['pin','transaction','pin']);self.assertTrue(result['transaction_completed'])
    def test_manager_requires_expected_parent_uuid(self):
        import inspect
        sig=inspect.signature(m.receiver_delete_one_locked)
        self.assertIn('expected_parent_uuid',sig.parameters)
        self.assertEqual(sig.parameters['expected_parent_uuid'].default,inspect.Parameter.empty)
    def test_invalid_parent_uuid_fails_before_inventory_and_journal(self):
        config=m.Config(pathlib.Path('/tmp/x'),pathlib.Path('/tmp/a'),pathlib.Path('/tmp/x/state/writer.lock'),(),m.RetentionPolicy(1,1,1,1,1,30),m.VerificationPolicy(False,'','','',None),mode='receiver',receiver_state_dir=pathlib.Path('/tmp/x/state'))
        with self.assertRaisesRegex(m.SnapshotError,'invalid expected protected parent UUID'):
            m.receiver_delete_one_locked(config,C,protected_stamp=P,expected_parent_uuid='bad',verify_source_pin=lambda: self.fail('pin called'),delete_subvolume=lambda _: self.fail('delete called'))
    def test_parent_receipt_identity_check_precedes_journal(self):
        text=manager.read_text()
        part=text.split('def receiver_delete_one_locked(',1)[1].split('def receiver_guarded_prune(',1)[0]
        self.assertIn('parent_uuid != expected_parent_uuid',part)
        self.assertLess(part.index('parent_uuid != expected_parent_uuid'),part.index('receiver_journal_write(state, record)'))
    def test_no_public_executor(self):
        self.assertNotIn("parser.add_argument('--execute-prune'",sender.read_text())
        self.assertIn('receiver pruning blocked: live common-parent coordination not implemented',manager.read_text())
if __name__=='__main__':unittest.main(argv=[sys.argv[0]],verbosity=2)
