#!/usr/bin/env python3
import importlib.util
import pathlib
import unittest
import subprocess
import tempfile

feature = pathlib.Path(__file__).resolve().parent.parent
script = feature / 'tools' / 'repair-0028-gradle-diff.py'
spec = importlib.util.spec_from_file_location('repair0028', str(script))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
task = (feature / 'tools' / 'migration0028-gradle-task.inc').read_text(encoding='utf-8')
HEAD = """// core header
foo { a = 1 }

tasks.register('migration0024ImageCatalogue', JavaExec) {
    group = 'migration'
}

tasks.register('migration0022Inventory', JavaExec) {
}
"""

class RepairTests(unittest.TestCase):
    def test_reordered_existing_blocks_reconstructed_to_head_order(self):
        current = ("tasks.register('migration0022Inventory', JavaExec) {\n}\n" + task +
                   "\n// core header\nfoo { a = 1 }\n" +
                   "tasks.register('migration0024ImageCatalogue', JavaExec) {\n    group = 'migration'\n}\n")
        result = module.make_candidate(HEAD, current, task)
        self.assertIn(task, result)
        self.assertTrue(module.staged_diff_only_adds_task(HEAD, result))
        self.assertLess(result.index('foo {'), result.index('migration0028ReviewedFragments'))
        self.assertLess(result.index('migration0028ReviewedFragments'), result.index('migration0024ImageCatalogue'))

    def test_crlf_input_supported(self):
        current = (HEAD.replace("tasks.register('migration0024ImageCatalogue'", task + "\ntasks.register('migration0024ImageCatalogue'"))
        result = module.make_candidate(HEAD.replace('\n', '\r\n'), current.replace('\n','\r\n'), task)
        self.assertTrue(module.staged_diff_only_adds_task(HEAD, result))

    def test_unrelated_code_change_refused(self):
        current = HEAD.replace('a = 1', 'a = 2').replace("tasks.register('migration0024ImageCatalogue'", task + "\ntasks.register('migration0024ImageCatalogue'")
        with self.assertRaisesRegex(ValueError, 'non-0028'):
            module.make_candidate(HEAD, current, task)

    def test_modified_migration_task_refused(self):
        current = HEAD.replace("tasks.register('migration0024ImageCatalogue'", task.replace('validate-manifest', 'apply') + "\ntasks.register('migration0024ImageCatalogue'")
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            module.make_candidate(HEAD, current, task)

    def test_duplicate_task_refused(self):
        current = HEAD.replace("tasks.register('migration0024ImageCatalogue'", task + task + "\ntasks.register('migration0024ImageCatalogue'")
        with self.assertRaisesRegex(ValueError, 'exactly one'):
            module.make_candidate(HEAD, current, task)

    def test_no_baseline_old_task_refused(self):
        with self.assertRaisesRegex(ValueError, '0024'):
            module.make_candidate('other', 'other\n' + task, task)

    def test_git_subprocess_uses_working_directory_instead_of_native_git_c(self):
        # Exercise actual Git from a directory containing spaces. This catches
        # mixed Cygwin/native Git path handling without altering the user's repo.
        with tempfile.TemporaryDirectory(prefix='0028 git cwd ') as td:
            repo = pathlib.Path(td) / 'responder checkout'
            repo.mkdir()
            subprocess.run(['git', 'init', '-q'], cwd=str(repo), check=True)
            (repo / 'build.gradle').write_text('// baseline\n', encoding='utf-8')
            subprocess.run(['git', 'add', 'build.gradle'], cwd=str(repo), check=True)
            subprocess.run(['git', '-c', 'user.name=0028-test',
                            '-c', 'user.email=0028@example.invalid',
                            'commit', '-q', '-m', 'baseline'], cwd=str(repo), check=True)
            self.assertEqual(module.git(repo, 'show', 'HEAD:build.gradle'), b'// baseline\n')
            self.assertEqual(len(module.git(repo, 'rev-parse', 'HEAD').decode().strip()), 40)

    def test_no_candidate_removal(self):
        self.assertFalse(module.staged_diff_only_adds_task('a\nb\nc\n','a\nc\n'))

if __name__ == '__main__':
    unittest.main(verbosity=2)
