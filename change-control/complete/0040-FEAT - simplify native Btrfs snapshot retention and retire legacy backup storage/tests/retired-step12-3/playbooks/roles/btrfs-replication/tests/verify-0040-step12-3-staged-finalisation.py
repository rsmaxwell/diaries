#!/usr/bin/env python3
"""Source-level transaction tests; no real Btrfs changes."""
import importlib.util
from pathlib import Path
import unittest
import copy

ROOT = Path(__file__).resolve().parents[1] / 'files'
spec = importlib.util.spec_from_file_location('core', ROOT / 'btrfs-agreed-parent-finalisation-core.py')
core = importlib.util.module_from_spec(spec); spec.loader.exec_module(core)
A = {'timestamp': '20261030-030033Z', 'uuid': 'd901ddd2-66c7-0b42-b26c-ab6886273b7a'}
B = {'timestamp': '20261030-170009Z', 'uuid': 'a9b78fb9-4da6-cf4f-b242-13909f574193'}
NONCE = 'a' * 64
BTRFS = 'b' * 8 + '-bbbb-bbbb-bbbb-' + 'b' * 12
BOOT = 'e87ccc64-fddc-41e7-a6e0-a4151dbb3fad'
JOURNAL = {'schema': 1, 'status': 'receiving', 'parent': A, 'candidate': B,
           'nonce': NONCE, 'scope_unit': 'btrfs-agreed-receive-'+B['timestamp']+'-'+NONCE[:16]+'.scope',
           'scope_binding': 'reserved-not-termination-evidence', 'receiver_boot_id': BOOT,
           'staging': {'directory_dev': 11, 'directory_ino': 123}}
FIELDS = {'snapshot': B['timestamp'], 'source_uuid': B['uuid'],
          'received_uuid': B['uuid'], 'parent_snapshot': A['timestamp'],
          'parent_source_uuid': A['uuid'], 'transport': 'btrfs-incremental',
          'read_only_verified': True, 'source_send_exit': 0,
          'receiver_receive_exit': 0}

class Tests(unittest.TestCase):
    def setUp(self):
        self.journal = copy.deepcopy(JOURNAL)
        self.state = {'schema': 1, 'established': A, 'pending': B, 'previous': None}
        self.published = False
        self.receipt = False
        self.sender_ok = True
        self.events = []
    def run_finalise(self):
        def proof(a,b,n):
            self.events.append('proof')
            if not self.sender_ok: return None
            return {'authenticated_session': True, 'source_send_exit': 0,
                    'ssh_exit': 0, 'receiver_receive_exit': 0, 'parent': a, 'candidate': b}
        def stage(b,n):
            self.events.append('stage')
            if self.published: raise AssertionError('stage consulted after publication')
            return {'status': 'staged-received-verified', 'candidate': b,
                    'subvolume_uuid': BTRFS, 'receipt_committed': False,
                    'publication_authorized': False, 'cleanup_authorized': False}
        def witness(j,w):
            self.events.append('witness')
            self.journal['publication_witness'] = w
        def publish(b,j):
            self.events.append('publish')
            self.published = True
            return {'status': 'published-awaiting-receipt',
                    'receipt_committed': False, 'cleanup_authorized': False}
        def inspect(stamp):
            self.events.append('inspect-published')
            return {'flags': 'readonly', 'received_uuid': B['uuid'], 'uuid': BTRFS} if self.published else None
        def commit(stamp, fields):
            self.events.append('commit'); self.receipt = True
        return core.finalize_staged_locked(
            A, B, read_state=lambda: self.state,
            read_journal=lambda: copy.deepcopy(self.journal),
            verify_source_completion=proof, inspect_staged=stage,
            record_publication_witness=witness, publish_staged=publish,
            inspect_published=inspect, published_absent=lambda stamp: not self.published, receipt_absent=lambda s: not self.receipt,
            commit_receipt=commit, receipt_fields=FIELDS,
            manager_lock_held=True, writer_lock_held=True)
    def test_staged_validated_journal(self):
        self.assertEqual(core.validate_provisional_journal(self.journal, A, B), self.journal)
    def test_authenticated_publish_then_receipt(self):
        result = self.run_finalise()
        self.assertTrue(result['receipt_committed'])
        self.assertEqual(self.events, ['proof','stage','witness','publish','inspect-published','commit'])
    def test_bad_sender_never_publishes(self):
        self.sender_ok = False
        with self.assertRaises(core.FinalisationRefused): self.run_finalise()
        self.assertFalse(self.published)
        self.assertEqual(self.events, ['proof'])
    def test_crash_after_publish_rolls_forward(self):
        self.journal['publication_witness'] = {'subvolume_uuid': BTRFS, 'received_uuid': B['uuid']}
        self.published = True
        self.run_finalise()
        self.assertEqual(self.events, ['proof','inspect-published','commit'])
    def test_witness_without_publication_rolls_forward(self):
        self.journal['publication_witness'] = {'subvolume_uuid': BTRFS, 'received_uuid': B['uuid']}
        self.run_finalise()
        self.assertTrue(self.receipt)
        self.assertEqual(self.events, ['proof','stage','publish','inspect-published','commit'])
    def test_witness_mismatch_refuses_and_preserves_staging(self):
        self.journal['publication_witness'] = {'subvolume_uuid': 'cccccccc-cccc-cccc-cccc-cccccccccccc',
                                               'received_uuid': B['uuid']}
        with self.assertRaises(core.FinalisationRefused): self.run_finalise()
        self.assertFalse(self.published)
        self.assertFalse(self.receipt)
    def test_witness_ambiguous_final_absence_refuses(self):
        self.journal['publication_witness'] = {'subvolume_uuid': BTRFS, 'received_uuid': B['uuid']}
        # The core must not infer absence from an inspector failure.
        with self.assertRaises(core.FinalisationRefused):
            core.finalize_staged_locked(
                A, B, read_state=lambda: self.state,
                read_journal=lambda: copy.deepcopy(self.journal),
                verify_source_completion=lambda a,b,n: {
                    'authenticated_session': True, 'source_send_exit': 0,
                    'ssh_exit': 0, 'receiver_receive_exit': 0,
                    'parent': a, 'candidate': b},
                inspect_staged=lambda *x: self.fail('unexpected staged inspection'),
                record_publication_witness=lambda *x: self.fail('unexpected witness update'),
                publish_staged=lambda *x: self.fail('unexpected publication'),
                inspect_published=lambda *x: None,
                receipt_absent=lambda stamp: True,
                commit_receipt=lambda *x: self.fail('unexpected receipt'),
                receipt_fields=FIELDS, manager_lock_held=True, writer_lock_held=True)
        self.assertFalse(self.receipt)
    def test_locks_required(self):
        with self.assertRaises(core.FinalisationRefused):
            core.finalize_staged_locked(A,B,read_state=lambda:self.state,read_journal=lambda:self.journal,
                verify_source_completion=lambda *x:None,inspect_staged=lambda *x:None,
                record_publication_witness=lambda *x:None,publish_staged=lambda *x:None,
                inspect_published=lambda *x:None,receipt_absent=lambda *x:True,
                commit_receipt=lambda *x:None,receipt_fields=FIELDS)
    def test_invalid_witness_refuses(self):
        self.journal['publication_witness'] = {'subvolume_uuid':'invalid', 'received_uuid':B['uuid']}
        with self.assertRaises(core.FinalisationRefused): self.run_finalise()
    def test_committed_receipt_refuses(self):
        self.receipt = True
        with self.assertRaises(core.FinalisationRefused): self.run_finalise()
        self.assertFalse(self.published)

if __name__ == '__main__': unittest.main(verbosity=2)
