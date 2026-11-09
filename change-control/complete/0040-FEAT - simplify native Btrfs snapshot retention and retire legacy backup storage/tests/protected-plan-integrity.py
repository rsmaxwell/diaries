"""0040-FEAT sender-side fail-closed retention-plan contract regression.
Usage: python3 protected-plan-integrity.py PATH_TO_BTRFS_NATIVE_PUSH_PY
"""
import importlib.util
import sys
import unittest
from pathlib import Path

source = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location('sender_contract', source)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
STAMP = '20261023-030037Z'
UUID = 'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa'
OLD = '20261020-030000Z'


def plan(**kwargs):
    result = {'snapshot': STAMP, 'source_uuid': UUID,
              'receiver_verified_under_lock': True,
              'authorizes_prune': False, 'deletion_executed': False,
              'candidates': [OLD], 'retained': 3, 'total': 4}
    result.update(kwargs)
    return result


class Tests(unittest.TestCase):
    def check(self, value):
        return m.validate_protected_plan(value, parent_stamp=STAMP, parent_uuid=UUID)

    def reject(self, value):
        with self.assertRaises(RuntimeError):
            self.check(value)

    def test_valid(self):
        self.assertEqual(self.check(plan())['candidates'], [OLD])

    def test_empty_valid(self):
        self.assertEqual(self.check(plan(candidates=[], retained=19, total=19))['candidates'], [])

    def test_duplicates_rejected(self):
        self.reject(plan(candidates=[OLD, OLD], retained=2))

    def test_counts_rejected(self):
        self.reject(plan(retained=4))
        self.reject(plan(total=0, retained=0, candidates=[]))
        self.reject(plan(total=True, retained=3))
        self.reject(plan(total=4, retained='3'))

    def test_future_candidate_rejected(self):
        self.reject(plan(candidates=['20261024-030000Z']))

    def test_parent_rejected(self):
        self.reject(plan(candidates=[STAMP]))

    def test_unsafe_authority_rejected(self):
        self.reject(plan(authorizes_prune=True))
        self.reject(plan(deletion_executed=True))
        self.reject(plan(receiver_verified_under_lock=False))

    def test_wrong_identity_rejected(self):
        self.reject(plan(snapshot=OLD))
        self.reject(plan(source_uuid='bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'))

    def test_malformed_candidates_rejected(self):
        self.reject(plan(candidates='not-a-list'))
        self.reject(plan(candidates=[None]))
        self.reject(plan(candidates=['../bad']))

    def test_no_deletion_available(self):
        self.assertNotIn('--execute-prune', source.read_text())
        self.assertNotIn("selection.add_argument('--prune-execute'", source.read_text())


if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]], verbosity=2)
