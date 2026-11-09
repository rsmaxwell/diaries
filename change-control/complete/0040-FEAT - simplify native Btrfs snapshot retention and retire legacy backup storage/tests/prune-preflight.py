#!/usr/bin/env python3
"""0040-FEAT sender-held prune-preflight contract: mocked endpoints, no production access."""
import importlib.util
import pathlib
import sys
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('push', sys.argv[1])
push = importlib.util.module_from_spec(spec)
spec.loader.exec_module(push)
STAMP = '20261023-030037Z'
UUID = 'fdcabd00-aa98-7647-bd3a-de5e23186d38'

class Tests(unittest.TestCase):
    def test_valid_and_no_deletion(self):
        with patch.object(push, 'prepare_prune_parent', return_value={
            'snapshot': STAMP, 'source_uuid': UUID}), patch.object(
                push, 'receiver_values', return_value=[{'snapshot': STAMP, 'source_uuid': UUID}]):
            value = push.prune_preflight()
        self.assertFalse(value['authorizes_prune'])
        self.assertFalse(value['deletion_executed'])
        self.assertEqual(value['retention_candidates'], 'not_calculated')
        self.assertEqual(value['common_parent'], STAMP)
    def test_receiver_parent_missing(self):
        with patch.object(push, 'prepare_prune_parent', return_value={
            'snapshot': STAMP, 'source_uuid': UUID}), patch.object(push, 'receiver_values', return_value=[]):
            with self.assertRaisesRegex(RuntimeError, 'not uniquely accepted'):
                push.prune_preflight()
    def test_receiver_parent_duplicate(self):
        entry = {'snapshot': STAMP, 'source_uuid': UUID}
        with patch.object(push, 'prepare_prune_parent', return_value=entry), patch.object(
            push, 'receiver_values', return_value=[entry, entry]):
            with self.assertRaisesRegex(RuntimeError, 'not uniquely accepted'):
                push.prune_preflight()
    def test_source_pin_failure_is_fatal(self):
        with patch.object(push, 'prepare_prune_parent', side_effect=RuntimeError('pin failure')):
            with self.assertRaisesRegex(RuntimeError, 'pin failure'):
                push.prune_preflight()
    def test_mutually_exclusive_cli(self):
        source = pathlib.Path(sys.argv[1]).read_text()
        self.assertIn("selection.add_argument('--prune-preflight'", source)
        self.assertIn('args.prepare_prune_parent or args.prune_preflight', source)
        self.assertIn('if args.prune_preflight:', source)

if __name__ == '__main__':
    unittest.main(argv=[sys.argv[0]], verbosity=2)
