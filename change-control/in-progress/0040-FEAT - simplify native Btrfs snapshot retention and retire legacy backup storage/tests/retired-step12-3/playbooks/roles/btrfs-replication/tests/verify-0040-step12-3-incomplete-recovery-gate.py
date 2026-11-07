#!/usr/bin/env python3
"""Fail-closed evidence matrix for 0040 partial receive recovery."""
import importlib.util
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / 'files/btrfs-agreed-parent-incomplete-recovery-gate.py'
spec = importlib.util.spec_from_file_location('recovery_gate', p)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
A = {'timestamp':'20261030-030033Z','uuid':'d901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp':'20261030-170009Z','uuid':'a9b78fb9-4da6-cf4f-b242-13909f574193'}
P = {'schema':1,'established':A,'pending':B,'previous':None}
J = {'schema':1,'status':'receiving','parent':A,'candidate':B,'nonce':'a'*64}

def input(**changes):
    x = dict(parent=A,candidate=B,source_state=P,receiver_state=P,journal=J,
             receipt_state='absent',destination_state='incomplete',
             locks_held=True,stream_terminated=True,destination_owned=True)
    x.update(changes)
    return x

class Tests(unittest.TestCase):
    def test_fenced_partial_is_evidence_only(self):
        result=m.assess(**input())
        self.assertEqual(result['status'],'fenced-incomplete-receive-evidence')
        self.assertFalse(result['cleanup_authorized'])
        self.assertFalse(result['retransmit_authorized'])
    def test_absent_destination_evidence_only(self):
        self.assertFalse(m.assess(**input(destination_state='absent',destination_owned=False))['cleanup_authorized'])
    def test_unfenced_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(stream_terminated=False))
    def test_unproven_fencing_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(stream_terminated=None))
    def test_missing_locks_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(locks_held=False))
    def test_wrong_journal_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(journal=dict(J, candidate=A)))
    def test_missing_journal_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(journal=None))
    def test_invalid_nonce_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(journal=dict(J, nonce='bad')))
    def test_committed_receipt_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(receipt_state='committed'))
    def test_unknown_receipt_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(receipt_state=None))
    def test_readonly_destination_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(destination_state='readonly-matching'))
    def test_unowned_partial_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(destination_owned=False))
    def test_uncertain_ownership_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(destination_owned=None))
    def test_state_mismatch_refuses(self):
        with self.assertRaises(m.RecoveryRefused): m.assess(**input(receiver_state=dict(P,pending=None)))

if __name__ == '__main__': unittest.main(verbosity=2)
