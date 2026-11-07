import importlib.util
import unittest
from pathlib import Path

SOURCE = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-locked-candidate.py'
spec = importlib.util.spec_from_file_location('locked_candidate', SOURCE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
P = {'timestamp': '20261030-170009Z', 'uuid': 'parent-id'}
C = {'timestamp': '20261101-140039Z', 'uuid': 'candidate-id'}

class Cases(unittest.TestCase):
    def run_review(self, *, pending=None, previous=None, candidate=C, fail=False):
        events=[]
        def acquire(stack, name):
            events.append('lock-' + name.name)
        def load(path, require_root=False):
            self.assertTrue(require_root)
            events.append('load')
            return {'schema':1,'established':P,'pending':pending,'previous':previous}
        def validate(state):
            events.append('validate')
            if fail: raise ValueError('invalid')
        def select(parent):
            events.append('select')
            self.assertEqual(parent,P['timestamp'])
            return candidate
        try:
            response=mod.review(acquire=acquire,load_state=load,
                                validate_state=validate,select=select)
            return response,events
        except ValueError:
            return None,events
    def test_locked_selection(self):
        out,events=self.run_review()
        self.assertEqual(out['status'],'locked-candidate-review')
        self.assertFalse(out['authorizes_transfer'])
        self.assertEqual(events,['lock-.native-push.lock','lock-btrfs-snapshot-manager.lock','load','validate','select'])
    def test_none_available(self):
        out,_=self.run_review(candidate=None)
        self.assertEqual(out['status'],'no-eligible-candidate')
    def test_pending_refused_without_selection(self):
        out,events=self.run_review(pending=C)
        self.assertEqual(out['status'],'transaction-reconciliation-required')
        self.assertNotIn('select',events)
    def test_previous_refused_without_selection(self):
        out,events=self.run_review(previous=P)
        self.assertEqual(out['status'],'transaction-reconciliation-required')
        self.assertNotIn('select',events)
    def test_invalid_state_blocks(self):
        out,events=self.run_review(fail=True)
        self.assertIsNone(out)
        self.assertNotIn('select',events)
    def test_stale_candidate_refused(self):
        with self.assertRaises(RuntimeError):self.run_review(candidate=P)
    def test_invalid_candidate_refused(self):
        with self.assertRaises(RuntimeError):self.run_review(candidate={'timestamp':'20261101-140039Z'})

if __name__=='__main__':unittest.main(verbosity=2)
