#!/usr/bin/env python3
"""Fail-closed recovery state classification, no external effects."""
import importlib.util
from pathlib import Path
import unittest

path = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-unattended-policy.py'
spec = importlib.util.spec_from_file_location('policy', path)
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
A = {'timestamp':'20261030-030033Z','uuid':'aaa'}
B = {'timestamp':'20261030-170009Z','uuid':'bbb'}
C = {'timestamp':'20261101-140039Z','uuid':'ccc'}
def state(est=B, pending=None, previous=None):
    return dict(schema=1, established=est, pending=pending, previous=previous)

class Tests(unittest.TestCase):
    def test_idle_next_cycle(self):
        self.assertEqual(p.next_action(state(),state(),candidate=C),'prepare-next-candidate')
    def test_idle_select_candidate(self):
        self.assertEqual(p.next_action(state(),state()),'select-next-candidate')
    def test_prepared_untransferred(self):
        s=state(pending=C)
        self.assertEqual(p.next_action(s,s,committed=False,destination='absent'),'execute-prepared')
    def test_committed_before_promotion(self):
        s=state(pending=C)
        self.assertEqual(p.next_action(s,s,committed=True,destination='readonly-matching'),'resume-committed')
    def test_receiver_promoted(self):
        s=state(pending=C)
        self.assertEqual(p.next_action(s,state(est=C,previous=B),committed=True,destination='readonly-matching'),'resume-committed')
    def test_promoted_previous(self):
        s=state(est=C,previous=B)
        self.assertEqual(p.next_action(s,s,committed=True),'acknowledge-previous')
    def test_interrupted_ack(self):
        s=state(est=C,previous=B)
        self.assertEqual(p.next_action(s,state(est=C),committed=True),'acknowledge-previous')
    def test_incomplete_requires_separate_reconciler(self):
        s=state(pending=C)
        self.assertEqual(p.next_action(s,s,committed=False,destination='incomplete'),'reconcile-incomplete-receive')
    def test_unknown_receipt_refused(self):
        s=state(pending=C)
        with self.assertRaises(p.RecoveryRefused): p.next_action(s,s,committed=None,destination='absent')
    def test_unexpected_receiver_refused(self):
        with self.assertRaises(p.RecoveryRefused): p.next_action(state(),state(est=C))
    def test_stale_candidate_refused(self):
        with self.assertRaises(p.RecoveryRefused): p.next_action(state(),state(),candidate=A)
    def test_identity_invalid_refused(self):
        with self.assertRaises(p.RecoveryRefused): p.next_action(state(),state(pending={'bad':'id'}))
    def test_committed_incomplete_refused(self):
        s=state(pending=C)
        with self.assertRaises(p.RecoveryRefused): p.next_action(s,s,committed=True,destination='incomplete')
    def test_no_ack_without_receipt(self):
        s=state(est=C, previous=B)
        with self.assertRaises(p.RecoveryRefused): p.next_action(s,s,committed=False)

if __name__=='__main__': unittest.main(verbosity=2)
