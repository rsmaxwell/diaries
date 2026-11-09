#!/usr/bin/env python3
"""Source tests for the dormant staging path contract, no filesystem changes."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-agreed-parent-staging-contract.py'
spec = importlib.util.spec_from_file_location('staging_contract', FILE)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

STAMP = '20261102-090000Z'
NONCE = 'a' * 64
CANDIDATE = {'timestamp': STAMP, 'uuid': '69ef9a57-50ff-9a4e-92ed-8f10560ab1f2'}
JOURNAL = {'status': 'receiving', 'candidate': CANDIDATE, 'nonce': NONCE}

class Cases(unittest.TestCase):
    def test_canonical_paths(self):
        result = m.verify_journal_binding(JOURNAL, CANDIDATE, locks_held=True)
        self.assertEqual(result['staged_subvolume'], m.FINAL_ROOT / ('.receive-' + NONCE))
        self.assertEqual(result['published_subvolume'], m.FINAL_ROOT / STAMP)
        self.assertEqual(result['staged_subvolume'].parent, m.FINAL_ROOT)

    def test_locks_required(self):
        with self.assertRaises(m.StagingRefused):
            m.verify_journal_binding(JOURNAL, CANDIDATE)

    def test_nonce_refuses_traversal(self):
        for bad in ('../' + NONCE, NONCE.upper(), 'a'*63, ''):
            with self.subTest(bad=bad), self.assertRaises(m.StagingRefused):
                m.paths(STAMP, bad)

    def test_snapshot_refuses_traversal(self):
        for bad in ('../20261102-090000Z', STAMP + '/x', '20261102-090000z'):
            with self.subTest(bad=bad), self.assertRaises(m.StagingRefused):
                m.paths(bad, NONCE)

    def test_missing_nonce_refuses(self):
        with self.assertRaises(m.StagingRefused):
            m.verify_journal_binding({'status':'receiving','candidate':CANDIDATE}, CANDIDATE, locks_held=True)

    def test_mismatched_candidate_refuses(self):
        with self.assertRaises(m.StagingRefused):
            m.verify_journal_binding(JOURNAL, {'timestamp': '20261102-100000Z', 'uuid': CANDIDATE['uuid']}, locks_held=True)

    def test_nonreceiving_refuses(self):
        with self.assertRaises(m.StagingRefused):
            m.verify_journal_binding(dict(JOURNAL, status='committed'), CANDIDATE, locks_held=True)

    def test_no_mutators_or_cli(self):
        source = FILE.read_text()
        for bad in ('os.rename(', 'os.replace(', 'subprocess.run(', 'subvolume delete', 'def main('):
            self.assertNotIn(bad, source)

if __name__ == '__main__':
    unittest.main(verbosity=2)
