#!/usr/bin/env python3
"""Offline tests for native-Windows/Cygwin-safe JAR contents check."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile, ZIP_STORED

FEATURE = Path(__file__).resolve().parent.parent
TOOLS = FEATURE / 'tools'
spec = importlib.util.spec_from_file_location('verify_jar', TOOLS / '0028_step3_verify_jar_entries.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.jar = Path(self.tmp.name) / 'diaries-responder-0.0.9-SNAPSHOT-fat.jar'

    def create(self, entries):
        with ZipFile(self.jar, 'w', ZIP_STORED) as z:
            for name, content in entries:
                z.writestr(name, content)

    def test_valid_fat_jar(self):
        self.create([(verifier.REQUIRED[0], b'compiled cli'),
                     (verifier.REQUIRED[1], b'create table journal;')])
        self.assertEqual(verifier.verify_jar(self.jar)[verifier.REQUIRED[0]], 12)

    def test_missing_class_fails(self):
        self.create([(verifier.REQUIRED[1], b'create table journal;')])
        with self.assertRaisesRegex(ValueError, '0 copies of required entry'):
            verifier.verify_jar(self.jar)

    def test_missing_sql_fails(self):
        self.create([(verifier.REQUIRED[0], b'compiled cli')])
        with self.assertRaisesRegex(ValueError, '0 copies of required entry'):
            verifier.verify_jar(self.jar)

    def test_empty_required_entry_fails(self):
        self.create([(verifier.REQUIRED[0], b''), (verifier.REQUIRED[1], b'sql')])
        with self.assertRaisesRegex(ValueError, 'required JAR entry is empty'):
            verifier.verify_jar(self.jar)

    def test_invalid_zip_fails(self):
        self.jar.write_bytes(b'not a ZIP file')
        with self.assertRaisesRegex(ValueError, 'built fat JAR is invalid'):
            verifier.verify_jar(self.jar)

    def test_duplicate_required_class_fails(self):
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter('ignore', UserWarning)
            self.create([(verifier.REQUIRED[0], b'compiled cli'),
                         (verifier.REQUIRED[0], b'another cli'),
                         (verifier.REQUIRED[1], b'sql')])
        with self.assertRaisesRegex(ValueError, '2 copies of required entry'):
            verifier.verify_jar(self.jar)

    def test_crc_corruption_fails(self):
        self.create([(verifier.REQUIRED[0], b'COMPILEDCLI'), (verifier.REQUIRED[1], b'sql')])
        raw = self.jar.read_bytes()
        raw = raw.replace(b'COMPILEDCLI', b'CORRUPT_CLI')
        self.jar.write_bytes(raw)
        with self.assertRaisesRegex(ValueError, 'built fat JAR is invalid'):
            verifier.verify_jar(self.jar)

    def test_shell_uses_python_zip_check_not_jar_listing(self):
        script = (TOOLS / 'prepare-0028-step3-release-artifact.sh').read_text()
        self.assertIn('python3 "$feature/tools/0028_step3_verify_jar_entries.py" "${jars[0]}"', script)
        self.assertNotIn('jar tf "${jars[0]}"', script)
        self.assertNotIn('grep -Fxq', script)
        self.assertIn('if ! git -C diaries-responder diff --quiet', script)
        self.assertIn('test ! -e "$out"', script)

    def test_main_rejects_missing_jar(self):
        self.assertEqual(verifier.main(['verify.py', str(self.jar)]), 2)


if __name__ == '__main__':
    unittest.main(verbosity=2)
