import importlib.util
import tempfile
import unittest
from pathlib import Path

DIR = Path(__file__).resolve().parents[1] / 'files'
def load(name):
    spec = importlib.util.spec_from_file_location(name.replace('-', '_'), DIR / name)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

sel = load('btrfs-agreed-parent-candidate-selection.py')
entry = load('btrfs-agreed-parent-cycle-entry.py')
A = '20261030-170009Z'
B = '20261101-140039Z'
C = '20261101-170009Z'
UUID = '69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'

def show(path):
    return f'Name: {path.name}\nUUID: {UUID}\nReceived UUID: -\nFlags: readonly\n'

class Tests(unittest.TestCase):
    def test_select_latest(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for stamp in (A,B,C): (root/stamp).mkdir()
            self.assertEqual(sel.select_candidate(A,root=root,show=show)['timestamp'], C)
    def test_none_available(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/A).mkdir()
            self.assertIsNone(sel.select_candidate(A,root=root,show=show))
    def test_reject_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/B).symlink_to(root)
            with self.assertRaises(sel.CandidateRefused):sel.select_candidate(A,root=root,show=show)
    def test_reject_readwrite(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); (root/B).mkdir()
            with self.assertRaises(sel.CandidateRefused):sel.select_candidate(A,root=root,show=lambda p:show(p).replace('readonly','-'))
    def test_auto_review(self):
        state={'established':{'timestamp':A,'uuid':'uuid'},'pending':None,'previous':None}
        calls=[]
        def invoke(args):
            calls.append(args)
            if '--inspect' in args:return {'status':'local-source-state-only','authorizes_transfer':False,'state':state}
            return {'status':'review-only','state_changed':False}
        result=entry.auto_cycle(call=invoke,selector=lambda parent:{'timestamp':B,'uuid':UUID})
        self.assertEqual(result['status'],'cycle-review-only')
        self.assertEqual(len(calls),3)
    def test_no_candidate_no_mutation(self):
        state={'established':{'timestamp':A,'uuid':'uuid'},'pending':None,'previous':None}
        calls=[]
        def invoke(args):
            calls.append(args)
            return {'status':'local-source-state-only','authorizes_transfer':False,'state':state}
        self.assertEqual(entry.auto_cycle(call=invoke,selector=lambda parent:None)['status'],'no-eligible-candidate')
        self.assertEqual(len(calls),1)
    def test_auto_execute_refuses_unsettled_state(self):
        def invoke(args):
            if '--inspect' in args:return {'status':'local-source-state-only','authorizes_transfer':False,'state':{'established':{'timestamp':A},'pending':{'timestamp':B},'previous':None}}
            self.fail('unsafe mutation dispatched')
        with self.assertRaisesRegex(entry.Refused, 'UUID missing'):
            entry.auto_cycle(execute=True,call=invoke)
    def test_pending_refused(self):
        state={'established':{'timestamp':A,'uuid':'uuid'},'pending':{'timestamp':B},'previous':None}
        with self.assertRaises(entry.Refused):entry.automatic_target(state,selector=lambda parent:None)

if __name__=='__main__':unittest.main(verbosity=2)
