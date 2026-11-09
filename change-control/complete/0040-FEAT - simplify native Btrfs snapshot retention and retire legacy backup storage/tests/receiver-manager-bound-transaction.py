import importlib.util
from importlib.machinery import SourceFileLoader
import fcntl
import io
import json
from pathlib import Path
import tempfile
import sys
import types
import unittest

source = Path(sys.argv[1])
spec = importlib.util.spec_from_loader('receiver_under_test', SourceFileLoader('receiver_under_test', str(source)))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
sys.argv = sys.argv[:1]
PARENT='20261023-030037Z'
CANDIDATE='20261012-100003Z'
UUID='fdcabd00-aa98-7647-bd3a-de5e23186d38'

class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.state = self.root/'state'
        self.state.mkdir()
        self.lock = self.root/'manager.lock'
        self.writer = self.state/'writer.lock'
        self.lock.touch()
        self.writer.touch()
        self.config = types.SimpleNamespace(mode='receiver',receiver_state_dir=self.state,
            receiver_prune_enabled=False,lock_path=self.lock,writer_lock_path=self.writer)
        self.original=m.secrets.token_hex
        calls=iter(('a'*64,'b'*64))
        m.secrets.token_hex=lambda n:next(calls)
        self.addCleanup(setattr,m.secrets,'token_hex',self.original)
        self.output=io.StringIO()
        self.deleted=False
        self.pin_count=0
        def delete(path):self.deleted=True
        self.delete=delete
        def manager_func(config,target,*,protected_stamp,expected_parent_uuid,verify_source_pin,delete_subvolume):
            self.assertEqual(target,CANDIDATE)
            self.assertEqual(protected_stamp,PARENT)
            self.assertEqual(expected_parent_uuid,UUID)
            self.assertIs(delete_subvolume,self.delete)
            for path in (self.lock,self.writer):
                with path.open('r+') as other:
                    with self.assertRaises(BlockingIOError):
                        fcntl.flock(other,fcntl.LOCK_EX|fcntl.LOCK_NB)
            verify_source_pin()
            self.pin_count+=1
            delete_subvolume(self.root/'disposable')
        self.manager=types.SimpleNamespace(receiver_delete_one_locked=manager_func)
    def planner(self,stamp,uuid):
        return {'snapshot':stamp,'source_uuid':uuid,'authorizes_prune':False,
             'deletion_executed':False,'candidates':[CANDIDATE]}
    def responses(self,wrong_second=False):
        return io.StringIO(''.join(json.dumps({'kind':'transaction-pin-response',
            'nonce':('a'*64 if i==0 else ('c'*64 if wrong_second else 'b'*64)),
            'snapshot':PARENT,'source_uuid':UUID,'candidate':CANDIDATE})+'\n' for i in range(2)))
    def invoke(self,incoming=None):
        return m.run_manager_bound_transaction(PARENT,UUID,CANDIDATE,
            manager=self.manager,config=self.config,
            incoming=incoming or self.responses(),outgoing=self.output,
            planner=self.planner,delete_subvolume=self.delete)
    def test_success_locks_and_manager_invocation(self):
        result=self.invoke()
        self.assertTrue(self.deleted)
        self.assertEqual(self.pin_count,1)
        self.assertEqual(result['kind'],'transaction-completed')
        self.assertEqual(len(self.output.getvalue().splitlines()),3)
    def test_bad_second_response_fails_before_manager(self):
        with self.assertRaises(RuntimeError):self.invoke(self.responses(True))
        self.assertFalse(self.deleted)
        self.assertNotIn('transaction-completed',self.output.getvalue())
    def test_manager_failure_propagates_without_success(self):
        self.manager.receiver_delete_one_locked=lambda *a,**kw: (_ for _ in ()).throw(RuntimeError('injected crash'))
        with self.assertRaisesRegex(RuntimeError,'injected crash'):self.invoke()
        self.assertNotIn('transaction-completed',self.output.getvalue())
    def test_disabled_config_required(self):
        self.config.receiver_prune_enabled=True
        with self.assertRaisesRegex(RuntimeError,'Refuse configuration'):self.invoke()
    def test_unsafe_writer_lock_refused(self):
        self.writer.unlink()
        self.writer.symlink_to(self.lock)
        with self.assertRaisesRegex(RuntimeError,'unsafe'):self.invoke()
    def test_no_public_delete_cli(self):
        text=source.read_text()
        self.assertNotIn("parser.add_argument('--execute-prune'",text)
        self.assertNotIn('run_manager_bound_transaction(',text[text.index('def main():'):])

if __name__=='__main__':unittest.main(verbosity=2)
