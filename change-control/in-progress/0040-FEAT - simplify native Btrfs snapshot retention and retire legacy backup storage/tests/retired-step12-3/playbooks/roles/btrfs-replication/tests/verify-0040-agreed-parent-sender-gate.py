#!/usr/bin/env python3
"""0040 fastpath: source test for fail-closed live sender entry point."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'files' / 'btrfs-native-push.py'

class Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = SOURCE.read_text()
        cls.tree = ast.parse(cls.text)
        cls.main = next(node for node in cls.tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        cls.branch = next(node for node in cls.main.body if isinstance(node, ast.If) and ast.unparse(node.test) == 'args.agreed_parent is not None')
        cls.code = ast.unparse(cls.branch)

    def test_explicit_mode(self):
        self.assertIn("'--agreed-parent'", self.text)
    def test_branch_precedes_legacy(self):
        self.assertLess(self.main.body.index(self.branch), next(i for i,n in enumerate(self.main.body) if isinstance(n,ast.With)))
    def test_early_return(self):
        self.assertIsInstance(self.branch.body[-1], ast.Return)
    def test_no_mutation_in_branch(self):
        for token in ('release-source', 'protect-source', 'choose_parent(', 'Popen(', '--accept'):
            self.assertNotIn(token,self.code)
    def test_fixed_readonly_planner(self):
        self.assertIn('btrfs-agreed-parent-locked-prepare-plan.py',self.code)
        self.assertNotIn('shell=True',self.code)
    def test_all_authorities_false(self):
        for name in ('prepare','source_prepare','transfer','promote','prune','release'):
            self.assertIn('authorizes_'+name,self.code)
        self.assertIn('is False',self.code)
    def test_no_legacy_flags(self):
        for name in ('args.preflight','args.full','args.reseed'):
            self.assertIn(name,self.code)
    def test_no_lock_reacquire(self):
        self.assertNotIn('flock(',self.code)
        self.assertNotIn('LOCK.open(',self.code)
    def test_explicit_non_mutation(self):
        for flag in ('transfer_executed','state_changed','release_executed'):
            self.assertIn(flag,self.code)

if __name__ == '__main__':
    unittest.main(verbosity=2)
