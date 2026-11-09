#!/usr/bin/env python3
"""Source regression for privileged, never-destructive reboot assessment."""
import ast
from pathlib import Path
import unittest

HERE=Path(__file__).resolve().parents[1]
SOURCE=HERE/'files/btrfs-agreed-parent-receiver-entry.py'
TASKS=HERE/'tasks/agreed-parent-runtime.yaml'

class Cases(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text=SOURCE.read_text()
        cls.tree=ast.parse(cls.text)
    def test_cli_exposes_read_only_assessment(self):
        self.assertIn("--assess-previous-boot",self.text)
        self.assertIn('inspect_previous_boot_fixed(parent, candidate)',self.text)
    def test_root_and_canonical_locks(self):
        f=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect_previous_boot_fixed')
        s=ast.get_source_segment(self.text,f)
        self.assertIn('os.geteuid() != 0',s)
        self.assertIn('receiver._lock(stack, MANAGER)',s)
        self.assertIn('receiver._lock(stack, WRITER)',s)
    def test_requires_receipt_and_journal(self):
        f=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect_previous_boot_fixed')
        s=ast.get_source_segment(self.text,f)
        self.assertIn('storage.receipt_absent',s)
        self.assertIn('reconciler.validate_journal',s)
        self.assertIn('reconciler.fence_previous_boot',s)
    def test_never_grants_authority(self):
        f=next(n for n in self.tree.body if isinstance(n,ast.FunctionDef) and n.name=='inspect_previous_boot_fixed')
        s=ast.get_source_segment(self.text,f)
        for k in ('cleanup_authorized','retransmit_authorized','prune_authorized','release_authorized'):
            self.assertIn("'"+k+"': False",s)
        self.assertNotIn('delete_subvolume(',s)
    def test_installer_includes_dependency(self):
        self.assertIn('    - incomplete-reconciler\n',TASKS.read_text())

if __name__=='__main__':unittest.main(verbosity=2)
