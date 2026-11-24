"""Regression: a quiet successful pg_restore has a present but empty log."""
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

RUNNER = Path(__file__).resolve().parent.parent / 'tools' / 'rehearse-0028-step2-isolated.sh'


class ResumeReceiptValidation(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='0028-resume-receipts-')
        self.addCleanup(self.temp.cleanup)
        self.evidence = Path(self.temp.name)
        for name in ('production.READONLY.pgcustom',
                     'production.READONLY.pgcustom.sha256',
                     'restore-counts.txt', 'docker-identity.txt'):
            (self.evidence / name).write_bytes(b'present\n')
        (self.evidence / 'pg-restore.log').write_bytes(b'')

    def verify(self):
        script = RUNNER.read_text(encoding='utf-8')
        start = script.index('    for required in production.READONLY.pgcustom ')
        stop = script.index('    (cd "$resume_source" && sha256sum', start)
        check = script[start:stop]
        command = 'resume_source=' + shlex.quote(str(self.evidence)) + '\n' + check + '\necho ACCEPTED\n'
        return subprocess.run(['bash', '-c', command], text=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def test_present_empty_restore_log_is_allowed(self):
        result = self.verify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('ACCEPTED', result.stdout)

    def test_missing_restore_log_is_rejected(self):
        (self.evidence / 'pg-restore.log').unlink()
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('original restore log is missing', result.stderr)

    def test_empty_required_dump_is_rejected(self):
        (self.evidence / 'production.READONLY.pgcustom').write_bytes(b'')
        result = self.verify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('missing original restore evidence', result.stderr)


if __name__ == '__main__':
    unittest.main(verbosity=2)
