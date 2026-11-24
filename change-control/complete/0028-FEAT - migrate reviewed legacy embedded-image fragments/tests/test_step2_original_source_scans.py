"""Offline, non-mutating tests for 0028 original page-scan staging."""
import csv
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'tools' / '0028-stage-original-page-scans.py'
spec = importlib.util.spec_from_file_location('stage_0028_scans', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class ScanStagingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / 'nas-diaries'
        self.source.mkdir()
        self.diary = 'diary-1828-and-1829-and-jan-1830'
        (self.source / self.diary).mkdir()
        (self.source / self.diary / 'img2839.jpg').write_bytes(b'private-test-page-2839')
        (self.source / self.diary / 'img2840.jpg').write_bytes(b'private-test-page-2840')
        self.dest = self.base / 'private-staged'
        self.dest.mkdir()
        self.csvpath = self.base / 'pages.csv'
        self.records = [
            [self.diary, 'img2839', 'jpg', '691'],
            [self.diary, 'img2840', 'jpg', '692'],
        ]
        self.write_records()

    def write_records(self):
        with self.csvpath.open('w', encoding='utf-8', newline='') as out:
            writer = csv.writer(out)
            writer.writerow(mod.REQUIRED_HEADERS)
            writer.writerows(self.records)

    def test_stage_and_verify_independent_copies(self):
        rows = mod.source_rows(self.csvpath)
        original = (self.source / self.diary / 'img2839.jpg').read_bytes()
        result = mod.stage(rows, self.source, self.dest)
        self.assertEqual(2, result['original_page_count'])
        self.assertEqual('PASS', result['status'])
        self.assertEqual(original, (self.source / self.diary / 'img2839.jpg').read_bytes())
        staged = self.dest / 'diaries' / self.diary / 'img2839.jpg'
        self.assertEqual(original, staged.read_bytes())
        self.assertEqual(2, mod.check_existing(rows, self.dest)['original_page_count'])
        self.assertTrue((self.dest / 'SHA256SUMS.txt').is_file())

    def test_staged_file_tampering_detected(self):
        rows = mod.source_rows(self.csvpath)
        mod.stage(rows, self.source, self.dest)
        tampered = self.dest / 'diaries' / self.diary / 'img2840.jpg'
        tampered.chmod(0o644)
        tampered.write_bytes(b'bad')
        with self.assertRaisesRegex(ValueError, 'checksum drift'):
            mod.check_existing(rows, self.dest)

    def test_path_traversal_and_backslash_rejected(self):
        for malicious in ('..', '../img2839', '..\\etc', '/etc/passwd'):
            self.records[0][1] = malicious
            self.write_records()
            with self.assertRaises(ValueError):
                mod.source_rows(self.csvpath)

    def test_unsupported_extension_rejected(self):
        self.records[0][2] = 'exe'
        self.write_records()
        with self.assertRaisesRegex(ValueError, 'Unsupported page scan extension'):
            mod.source_rows(self.csvpath)

    def test_duplicate_page_rejected(self):
        self.records.append(self.records[0][:])
        self.write_records()
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            mod.source_rows(self.csvpath)

    def test_same_filename_with_other_id_rejected(self):
        self.records.append([self.diary, 'img2839', 'jpg', '9999'])
        self.write_records()
        with self.assertRaisesRegex(ValueError, 'Page filename shared'):
            mod.source_rows(self.csvpath)

    def test_symlink_refused(self):
        p = self.source / self.diary / 'img2840.jpg'
        p.unlink()
        p.symlink_to(self.source / self.diary / 'img2839.jpg')
        with self.assertRaisesRegex(ValueError, 'symlink'):
            mod.stage(mod.source_rows(self.csvpath), self.source, self.dest)
        self.assertEqual([], list(self.dest.iterdir()))

    def test_missing_source_fails_before_any_copy(self):
        (self.source / self.diary / 'img2840.jpg').unlink()
        with self.assertRaises(FileNotFoundError):
            mod.stage(mod.source_rows(self.csvpath), self.source, self.dest)
        self.assertEqual([], list(self.dest.iterdir()))

    def test_nonempty_destination_refused(self):
        (self.dest / 'existing.txt').write_text('do not overwrite')
        with self.assertRaisesRegex(ValueError, 'EMPTY'):
            mod.stage(mod.source_rows(self.csvpath), self.source, self.dest)
        self.assertTrue((self.dest / 'existing.txt').is_file())

    def test_source_destination_overlap_rejected(self):
        dest = self.source / 'rehearsal-output'
        dest.mkdir()
        with self.assertRaisesRegex(ValueError, 'distinct'):
            mod.stage(mod.source_rows(self.csvpath), self.source, dest)

    def test_legacy_python_compatible_path_containment(self):
        # Our Cygwin Python can be older than pathlib.Path.is_relative_to.
        self.assertNotIn('.is_relative_to(', SCRIPT.read_text(encoding='utf-8'))
        self.assertTrue(mod.is_within(self.source, self.source))
        self.assertTrue(mod.is_within(self.source / self.diary, self.source))
        self.assertFalse(mod.is_within(self.base / 'nas-diaries-copy', self.source))
        self.assertFalse(mod.is_within(self.source, self.base / 'nas-diaries-copy'))

    def test_similarly_named_sibling_destination_is_allowed(self):
        sibling = self.base / 'nas-diaries-output'
        sibling.mkdir()
        staged = mod.stage(mod.source_rows(self.csvpath), self.source, sibling)
        self.assertEqual(2, staged['original_page_count'])

    def test_symlinked_parent_directory_cannot_escape_source_root(self):
        outside = self.base / 'outside'
        outside.mkdir()
        (outside / 'img2839.jpg').write_bytes(b'outside')
        (outside / 'img2840.jpg').write_bytes(b'outside')
        for scan in (self.source / self.diary).iterdir():
            scan.unlink()
        (self.source / self.diary).rmdir()
        (self.source / self.diary).symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escaped root'):
            mod.stage(mod.source_rows(self.csvpath), self.source, self.dest)
        self.assertEqual([], list(self.dest.iterdir()))

    def test_wrong_headers_rejected(self):
        self.csvpath.write_text('filename,other\nabc,def\n')
        with self.assertRaisesRegex(ValueError, 'headings'):
            mod.source_rows(self.csvpath)

    def test_check_existing_wrong_page_id_rejected(self):
        rows = mod.source_rows(self.csvpath)
        mod.stage(rows, self.source, self.dest)
        rows[0]['page_id'] = 999
        with self.assertRaisesRegex(ValueError, 'Page ID drift'):
            mod.check_existing(rows, self.dest)

    def test_http_proxy_static_contract(self):
        nginx = (ROOT / 'tools' / '0028-mqtt-http-proxy-with-scans.conf').read_text()
        source = (ROOT / 'tools' / '0028-original-page-scans-nginx.conf').read_text()
        self.assertIn('location ^~ /diaries/', nginx)
        self.assertIn('diaries-0028-replay-source-scans:8080', nginx)
        self.assertIn('diaries-0028-replay-responder:8081', nginx)
        self.assertIn('diaries-0028-replay-reader:8082', nginx)
        self.assertIn('location ^~ /diaries/', source)
        self.assertIn('alias /usr/share/nginx/html/diaries/', source)
        self.assertIn('location / { return 404; }', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
