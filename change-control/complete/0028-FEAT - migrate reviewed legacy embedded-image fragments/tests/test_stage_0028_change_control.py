import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

HERE=pathlib.Path(__file__).resolve().parents[1]
p=HERE/'tools'/'stage-0028-change-control.py'
spec=importlib.util.spec_from_file_location('stage0028',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class Check(unittest.TestCase):
    def test_root_readme(self):
        self.assertIsNone(m.candidate_path_allowed('README.md'))
    def test_root_unknown(self):
        self.assertIsNotNone(m.candidate_path_allowed('approved-manifest.csv'))
    def test_reports_markdown(self):
        self.assertIsNone(m.candidate_path_allowed('reports/STEP3.md'))
        self.assertIsNotNone(m.candidate_path_allowed('reports/private-dump.json'))
    def test_tool_types(self):
        for p in ['tools/prepare.sh','tools/probe.py','tools/bridge/bridge.js',
                  'tools/bridge/Dockerfile','tools/sample.conf','tools/templates/review-fields.example.csv']:
            self.assertIsNone(m.candidate_path_allowed(p),p)
    def test_excludes_private(self):
        for p in ['evidence/Step 3/private/plan.json','scratch/test.py',
                  'tools/private/review.py','tools/node_modules/a.js','tools/__pycache__/t.py']:
            self.assertIsNotNone(m.candidate_path_allowed(p),p)
    def test_excludes_binary(self):
        for p in ['tools/jar.jar','tools/test.sql','tools/data.dump','tools/a.zip','tools/key.pem']:
            self.assertIsNotNone(m.candidate_path_allowed(p),p)
    def test_excludes_out_of_scope(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(m.Stop):
                m.inspect_file(pathlib.Path(d),'change-control/in-progress/0053-DEF/foo.py')
    def test_protect_symlink(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); p=root/m.FEATURE/'tools'/'x.py'
            p.parent.mkdir(parents=True)
            target=root/'source'; target.write_text('hello')
            p.symlink_to(target)
            with self.assertRaises(m.Stop):m.inspect_file(root,str(pathlib.PurePosixPath(m.FEATURE,'tools/x.py')))
    def test_secret_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); p=root/m.FEATURE/'tools'/'x.py'
            p.parent.mkdir(parents=True)
            p.write_text('-----BEGIN ' + 'PRIVATE KEY-----')
            with self.assertRaises(m.Stop): m.inspect_file(root,m.FEATURE+'/tools/x.py')
    def test_allows_normal_source(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d); p=root/m.FEATURE/'tools'/'x.py'
            p.parent.mkdir(parents=True)
            p.write_text('print(1)\n')
            rec=m.inspect_file(root,m.FEATURE+'/tools/x.py')
            self.assertEqual(rec['bytes'],9)

    def test_synthetic_url_rejection_fixtures_allowed_in_exact_tests(self):
        cases = [
            ('tests/test_step4_0051_compatibility_review.py',
             b'def test_dangerous_urls_are_rejected(self):\n'
             b"        for url in ('https://" b"name:password@example.org/',):\n"
             b'            self.assertFalse(valid_url(url),url)\n'),
            ('tests/test_step4_0051_portal_suggestions.py',
             b'def test_dangerous_or_ambiguous_link_never_suggested(self):\n'
             b"        for link in ('https://" b"name:pass@example.org/',):\n"
             b"            self.assertNotIn('link_handling',source_suggestions(r))\n"),
        ]
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            for relative, data in cases:
                p=root/m.FEATURE/relative
                p.parent.mkdir(parents=True,exist_ok=True)
                p.write_bytes(data)
                rec=m.inspect_file(root,m.FEATURE+'/'+relative)
                self.assertEqual(rec['bytes'],len(data))

    def test_other_credentials_still_rejected_in_allowed_fixture_files(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            rel='tests/test_step4_0051_compatibility_review.py'
            p=root/m.FEATURE/rel; p.parent.mkdir(parents=True)
            good=(b'def test_dangerous_urls_are_rejected(self):\n'
                  b"        x='https://" b"name:password@example.org/'\n"
                  b'        self.assertFalse(valid_url(url),url)\n')
            p.write_bytes(good + b"other='https://" b"admin:realpassword@host.invalid/'\n")
            with self.assertRaises(m.Stop):
                m.inspect_file(root,m.FEATURE+'/'+rel)
            p.write_bytes(good + b"other='https://" b"name:password@example.org/'\n")
            with self.assertRaises(m.Stop):
                m.inspect_file(root,m.FEATURE+'/'+rel)
            p.write_bytes(b"other='https://" b"name:password@example.org/'\n")
            with self.assertRaises(m.Stop):
                m.inspect_file(root,m.FEATURE+'/'+rel)

    def test_fixtures_not_whitelisted_in_other_paths(self):
        with tempfile.TemporaryDirectory() as d:
            root=pathlib.Path(d)
            p=root/m.FEATURE/'tests'/'unrelated.py';p.parent.mkdir(parents=True)
            p.write_text("x='https://" "name:password@example.org/'\n")
            with self.assertRaises(m.Stop):
                m.inspect_file(root,m.FEATURE+'/tests/unrelated.py')

    def test_temporary_git_feature_stage_is_exclusive(self):
        import subprocess
        def cmd(where, *args):
            p=subprocess.run(['git', *args], cwd=str(where), capture_output=True,
                             text=True)
            if p.returncode:
                raise AssertionError(p.stderr)
            return p.stdout.strip()
        with tempfile.TemporaryDirectory() as d:
            base=pathlib.Path(d)
            child=base/'child';child.mkdir()
            cmd(child,'init','-q');cmd(child,'config','user.email','test@example.invalid')
            cmd(child,'config','user.name','Test')
            (child/'source.txt').write_text('migration commit\n')
            cmd(child,'add','.');cmd(child,'commit','-qm','child')
            child_sha=cmd(child,'rev-parse','HEAD')
            parent=base/'parent';parent.mkdir()
            cmd(parent,'init','-q');cmd(parent,'config','user.email','test@example.invalid')
            cmd(parent,'config','user.name','Test')
            cmd(parent,'-c','protocol.file.allow=always','submodule','add','-q',str(child),'diaries-responder')
            prefix=parent/m.FEATURE;prefix.mkdir(parents=True)
            (prefix/'README.md').write_text('# 0028\n')
            (prefix/'.gitignore').write_text('/evidence/Step 3/private/\n')
            cmd(parent,'add','.');cmd(parent,'commit','-qm','baseline')
            (prefix/'reports').mkdir()
            (prefix/'reports'/'review.md').write_text('Report body\n')
            (prefix/'tools').mkdir()
            (prefix/'tools'/'test.py').write_text('print(1)\n')
            ignored=prefix/'evidence'/'Step 3'/'private';ignored.mkdir(parents=True)
            (ignored/'private-manifest.csv').write_text('secret source rows\n')
            other=parent/'change-control'/'in-progress'/'0053-DEF';other.mkdir()
            (other/'README.md').write_text('Not 0028\n')
            before=cmd(parent,'status','--porcelain')
            oldpin=m.PIN
            try:
                m.PIN=child_sha
                m.run(parent,False)
                self.assertEqual(cmd(parent,'diff','--cached','--name-only'),'')
                m.run(parent,True)
            finally:
                m.PIN=oldpin
            actual=cmd(parent,'diff','--cached','--name-only').splitlines()
            self.assertEqual(actual,[m.FEATURE+'/reports/review.md',m.FEATURE+'/tools/test.py'])
            self.assertTrue((ignored/'private-manifest.csv').exists())
            self.assertIn('0053-DEF',cmd(parent,'status','--short'))
            self.assertFalse(cmd(parent,'status','--short').find('private-manifest.csv')>=0)

    def test_staging_scanner_can_scan_its_own_sources_and_report(self):
        # Source-file inspection must not mistake the synthetic negative-test
        # examples for secrets in the scanner or its tests or documentation.
        root = HERE.parents[2]
        for relative in (
            'tools/stage-0028-change-control.py',
            'tests/test_stage_0028_change_control.py',
            'reports/STEP3-GIT-SYNTHETIC-URL-FIXTURE-WHITELIST-20261124.md',
        ):
            with self.subTest(relative=relative):
                record = m.inspect_file(root, m.FEATURE + '/' + relative)
                self.assertGreater(record['bytes'], 0)

    def test_no_commit_or_push_in_script(self):
        src=p.read_text()
        self.assertNotIn("git(repo,'commit'",src)
        self.assertNotIn("git(repo,'push'",src)
        self.assertIn('original_staged',src)
        self.assertIn('PIN',src)

if __name__=='__main__':
    unittest.main(verbosity=2)
