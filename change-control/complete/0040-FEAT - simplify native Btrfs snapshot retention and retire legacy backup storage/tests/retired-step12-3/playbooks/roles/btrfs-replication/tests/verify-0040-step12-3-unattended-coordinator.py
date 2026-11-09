#!/usr/bin/env python3
"""Offline unattended recovery dispatch and fail-closed regression."""
import importlib.util
from pathlib import Path
import unittest

FILES = Path(__file__).resolve().parents[1] / 'files'
def load(name):
    spec = importlib.util.spec_from_file_location(name, FILES / ('btrfs-agreed-parent-' + name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

p, c = load('unattended-policy'), load('unattended-coordinator')
B = {'timestamp': '20261030-170009Z', 'uuid': 'bbb'}
C = {'timestamp': '20261101-140039Z', 'uuid': 'ccc'}
def st(est=B, pending=None, previous=None):
    return dict(schema=1, established=est, pending=pending, previous=previous)
def evidence(source=None, receiver=None, committed=None, destination=None, candidate=None):
    source = source or st()
    return dict(source=source, receiver=receiver or source, committed=committed,
                destination=destination, candidate=candidate)

class Tests(unittest.TestCase):
    def test_missing_locks_refuses_before_observation(self):
        seen=[]
        with self.assertRaisesRegex(c.UnattendedRefused, 'locks'):
            c.choose_once(policy=p, observe=lambda: seen.append(1), operation=lambda *x:None)
        self.assertEqual(seen, [])
    def test_prepared_execution_once_then_validated(self):
        e=[evidence(st(pending=C), committed=False, destination='absent'),
           evidence(st(pending=C), committed=True, destination='readonly-matching')]
        seen=[]
        result=c.choose_once(policy=p, observe=lambda: e.pop(0),
                             operation=lambda action, obs: seen.append(action) or {'completed':True},
                             canonical_locks_held=True)
        self.assertEqual(seen, ['execute-prepared'])
        self.assertEqual(result['next_action'], 'resume-committed')
    def test_committed_promoted_resume(self):
        e=evidence(st(pending=C), receiver=st(est=C, previous=B), committed=True, destination='readonly-matching')
        result=c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:{'completed':True}, canonical_locks_held=True)
        self.assertEqual(result['action'], 'resume-committed')
    def test_previous_ack(self):
        e=evidence(st(est=C, previous=B), committed=True)
        result=c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:{'completed':True}, canonical_locks_held=True)
        self.assertEqual(result['action'], 'acknowledge-previous')
    def test_incomplete_never_dispatches_mutation(self):
        e=evidence(st(pending=C), committed=False, destination='incomplete')
        calls=[]
        with self.assertRaisesRegex(c.UnattendedRefused, 'fenced reconciler'):
            c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:calls.append(args), canonical_locks_held=True)
        self.assertEqual(calls, [])
    def test_unknown_receipt_never_dispatches(self):
        e=evidence(st(pending=C), committed=None, destination='absent')
        calls=[]
        with self.assertRaises(p.RecoveryRefused):
            c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:calls.append(args), canonical_locks_held=True)
        self.assertEqual(calls, [])
    def test_bad_completion_refuses(self):
        e=evidence(candidate=C)
        with self.assertRaisesRegex(c.UnattendedRefused, 'completion'):
            c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:{'completed':False}, canonical_locks_held=True)
    def test_lost_post_observation_refuses(self):
        count=[0]
        def observe():
            count[0]+=1
            if count[0] == 2: raise OSError('peer went away')
            return evidence(candidate=C)
        with self.assertRaises(OSError):
            c.choose_once(policy=p, observe=observe, operation=lambda *args:{'completed':True}, canonical_locks_held=True)
    def test_reject_inconsistent_post_state(self):
        seq=[evidence(candidate=C), evidence(source=st(pending=C), receiver=st(est=C), committed=None)]
        with self.assertRaises(p.RecoveryRefused):
            c.choose_once(policy=p, observe=lambda:seq.pop(0), operation=lambda *args:{'completed':True}, canonical_locks_held=True)
    def test_no_pruning_authority(self):
        e=evidence(candidate=C)
        result=c.choose_once(policy=p, observe=lambda:e, operation=lambda *args:{'completed':True}, canonical_locks_held=True)
        self.assertFalse(result['authorizes_release'])
        self.assertFalse(result['authorizes_prune'])

if __name__=='__main__': unittest.main(verbosity=2)
