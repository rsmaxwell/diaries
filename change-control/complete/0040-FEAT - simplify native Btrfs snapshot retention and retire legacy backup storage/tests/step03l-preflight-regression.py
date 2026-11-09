#!/usr/bin/env python3
"""Run: python3 test-step03l-preflight.py step03l-preflight.py"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
spec=importlib.util.spec_from_file_location('preflight',sys.argv[1]); m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class PreflightTests(unittest.TestCase):
    def test_empty_mount_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'@data').mkdir()
            result=m.inspect(root,root/'@data'/'0040-step03l-rehearsal',mount_info='')
            self.assertFalse(result['all_passed']);self.assertFalse(result['authorizes_deletion'])
    def test_existing_disposable_dir_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t); (root/'@data'/'0040-step03l-rehearsal').mkdir(parents=True)
            result=m.inspect(root,root/'@data'/'0040-step03l-rehearsal',mount_info='')
            self.assertFalse(next(c for c in result['checks'] if c['check']=='rehearsal-not-present')['passed'])
    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'@data').mkdir(); (root/'@data'/'0040-step03l-rehearsal').symlink_to(root)
            result=m.inspect(root,root/'@data'/'0040-step03l-rehearsal',mount_info='')
            self.assertFalse(next(c for c in result['checks'] if c['check']=='no-symlink-0040-step03l-rehearsal')['passed'])
    def test_no_mutation_and_no_authority(self):
        with tempfile.TemporaryDirectory() as t:
            root=Path(t);(root/'@data').mkdir(); before=list(root.rglob('*'))
            result=m.inspect(root,root/'@data'/'0040-step03l-rehearsal',mount_info='')
            self.assertEqual(before,list(root.rglob('*')))
            self.assertFalse(result['authorizes_creation']);self.assertFalse(result['authorizes_deletion'])
if __name__=='__main__':
    unittest.main(argv=[sys.argv[0]],verbosity=2)
