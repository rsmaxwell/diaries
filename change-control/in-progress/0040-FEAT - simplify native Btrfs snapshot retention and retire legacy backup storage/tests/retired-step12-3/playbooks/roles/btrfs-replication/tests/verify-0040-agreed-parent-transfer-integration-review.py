#!/usr/bin/python3
import importlib.util
from pathlib import Path
import unittest

FILES = Path(__file__).resolve().parents[1] / 'files'

def load(n):
    p = FILES / ('btrfs-agreed-parent-' + n + '.py')
    s = importlib.util.spec_from_file_location('04g_' + n.replace('-', '_'), p)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m)
    return m

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.integration = load('transfer-integration-review')
        cls.contract = load('transfer-transport-contract')
        cls.adapter = load('transfer-execution-adapter')
        cls.a = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
        cls.b = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}

    def review(self):
        state={'schema':1,'established':self.a,'pending':self.b,'previous':None}
        return {'status':'prepared-transfer-review','parent':self.a,'candidate':self.b,
                'source':state,'receiver':dict(state),'state_changed':False,
                'transfer_executed':False,'release_executed':False,
                'authorizes_transfer':False,'authorizes_promote':False,
                'authorizes_prune':False,'authorizes_release':False}

    def check(self, r=None, cmds=None):
        r = self.review() if r is None else r
        cmds = self.contract.exact_incremental_commands(self.a,self.b) if cmds is None else cmds
        return self.integration.check_contract(r,cmds,contract=self.contract,adapter=self.adapter)

    def test_review_contract_passes_without_authority(self):
        result=self.check()
        self.assertEqual(result['status'],'transfer-integration-review')
        self.assertFalse(result['authorizes_transfer'])
        self.assertFalse(result['receiver_destination_absence_verified'])
        self.assertFalse(result['transport_execution_identity_verified'])

    def test_divergent_state_refused(self):
        r=self.review();r['receiver']['pending']=None
        with self.assertRaises(RuntimeError):self.check(r)

    def test_unprepared_refused(self):
        r=self.review();r['source']['pending']=None;r['receiver']['pending']=None
        with self.assertRaises(RuntimeError):self.check(r)

    def test_authority_refused(self):
        r=self.review();r['authorizes_transfer']=True
        with self.assertRaises(RuntimeError):self.check(r)

    def test_wrong_receiver_command_refused(self):
        cmd=self.contract.exact_incremental_commands(self.a,self.b);cmd['receiver_accept']=('unsafe',)
        with self.assertRaises((RuntimeError,Exception)):self.check(cmds=cmd)

    def test_wrong_parent_refused(self):
        cmd=self.contract.exact_incremental_commands(self.a,self.b);cmd['parent']={'timestamp':'20251030-030033Z','uuid':self.a['uuid']}
        with self.assertRaises(Exception):self.check(cmds=cmd)

    def test_no_execution_flag(self):
        import inspect
        self.assertNotIn('execute',inspect.signature(self.integration.run_review).parameters)
        self.assertFalse(hasattr(self.integration,'transfer_once'))

    def test_contract_never_calls_execution(self):
        class FailAdapter:
            def exact_argv(self,*args):
                raise RuntimeError('adapter refused')
        with self.assertRaises(RuntimeError):
            self.integration.check_contract(self.review(),self.contract.exact_incremental_commands(self.a,self.b),contract=self.contract,adapter=FailAdapter())

if __name__=='__main__':unittest.main(verbosity=2)
