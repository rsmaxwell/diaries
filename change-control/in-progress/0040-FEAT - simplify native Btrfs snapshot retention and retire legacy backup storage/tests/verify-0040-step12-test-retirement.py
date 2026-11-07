#!/usr/bin/env python3
"""Fixture verification of guarded Step 12 historical Playbooks test retirement."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parent.parent/'tools'/'retire-obsolete-playbooks-step12-tests.py'
TEST_REL = Path('roles/btrfs-replication/tests')

class Cases(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        base = Path(self.tmp.name)
        self.repo = base/'playbooks'
        self.feature = base/'diaries'/'change-control'/'in-progress'/'0040-FEAT'
        self.feature.joinpath('tools').mkdir(parents=True)
        shutil.copy2(SCRIPT, self.feature/'tools'/SCRIPT.name)
        self.test_root = self.repo/TEST_REL
        self.test_root.mkdir(parents=True)
        for name in ('verify-0040-simplified-replication.py',
                     'verify-0040-simplified-protection.py',
                     'verify-0040-step12-3-shared-retention.py',
                     'verify-0040-step12-3-privileged-delete-transfer-guard.py'):
            (self.test_root/name).write_text('print("still in use")\n')
        self.old = self.test_root/'verify-0040-step12-3-receiver-entry.py'
        self.old.write_text('# obsolete v1\n')
        self.agreed = self.test_root/'verify-0040-agreed-parent-selection.py'
        self.agreed.write_text('# obsolete agreed v1\n')
        self.untracked = self.test_root/'verify-0040-step12-3c-receiver-cli.py'
        subprocess.run(['git', '-C', str(self.repo), 'init', '-b', 'main'], check=True, capture_output=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.name', 'Test'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.email', 'test@example.com'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-m', 'baseline'], check=True, capture_output=True)
        self.untracked.write_text('# obsolete untracked\n')
        self.old.write_text('# obsolete modified tracked\n')

    def run_cleanup(self, mode, expect=0):
        script = self.feature/'tools'/SCRIPT.name
        args=['python3', str(script), '--playbooks', str(self.repo), mode]
        if mode == '--apply':
            args += ['--expect-count', '3']
        p = subprocess.run(args,
                           capture_output=True, text=True)
        if p.returncode != expect:
            self.fail(f'expected {expect} got {p.returncode}\nOUT={p.stdout}\nERR={p.stderr}')
        return p

    def test_plan_readonly_counts_tracked_and_untracked(self):
        out=self.run_cleanup('--plan').stdout
        self.assertIn('CANDIDATES: 3',out)
        self.assertIn('PLAN ONLY',out)
        self.assertTrue(self.old.exists())
        self.assertFalse((self.feature/'tests'/'retired-step12-3').exists())

    def test_apply_archives_exact_bytes_and_removes_only_candidates(self):
        before={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (self.old,self.agreed,self.untracked)}
        self.run_cleanup('--apply')
        archive=self.feature/'tests'/'retired-step12-3'
        manifest=json.loads((archive/'manifest.json').read_text())
        self.assertEqual(manifest['schema'],2)
        self.assertEqual(len(manifest['files']),3)
        for item in manifest['files']:
            n=Path(item['path']).name
            self.assertEqual(item['sha256'],before[n])
            self.assertEqual(hashlib.sha256((archive/item['archive']).read_bytes()).hexdigest(),before[n])
            self.assertFalse((self.test_root/n).exists())
        self.assertTrue((self.test_root/'verify-0040-simplified-replication.py').exists())
        self.assertTrue((self.test_root/'verify-0040-step12-3-shared-retention.py').exists())
        self.assertIn('CANDIDATES: 0',self.run_cleanup('--plan').stdout)

    def test_staged_change_refuses_without_loss(self):
        subprocess.run(['git', '-C', str(self.repo), 'add', str(self.old)],check=True)
        self.run_cleanup('--apply',expect=1)
        self.assertTrue(self.old.exists())
        self.assertFalse((self.feature/'tests'/'retired-step12-3').exists())

    def test_active_code_reference_refuses(self):
        script=self.repo/'roles'/'btrfs-replication'/'tasks'/'native.yaml'
        script.parent.mkdir(parents=True)
        script.write_text('test: verify-0040-step12-3-receiver-entry.py\n')
        p=self.run_cleanup('--apply',expect=1)
        self.assertIn('Active executable references',p.stderr)
        self.assertTrue(self.old.exists())

    def test_existing_archive_conflict_refuses_before_deletion(self):
        archive=self.feature/'tests'/'retired-step12-3'/'playbooks'/TEST_REL
        archive.mkdir(parents=True)
        (archive/self.old.name).write_text('different historic version\n')
        self.run_cleanup('--apply',expect=1)
        self.assertTrue(self.old.exists())

    def test_symlink_candidate_refuses(self):
        self.old.unlink()
        self.old.symlink_to(self.agreed)
        self.run_cleanup('--plan',expect=1)
        self.assertTrue(self.old.is_symlink())

    def test_no_candidate_families_keep_current_suites(self):
        self.run_cleanup('--apply')
        self.assertTrue((self.test_root/'verify-0040-step12-3-privileged-delete-transfer-guard.py').exists())
        self.assertTrue((self.test_root/'verify-0040-simplified-protection.py').exists())

if __name__ == '__main__':
    unittest.main(verbosity=2)
