"""Offline tests of the isolated rehearsal media, plan and approval guards (Python >=3.7)."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parent.parent / 'tools'


def load(module, filename):
    spec = importlib.util.spec_from_file_location(module, str(BASE / filename))
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


stage = load('stage0028', 'stage-0028-rehearsal-media.py')
fixtures = load('fixtures0028', 'prepare-0028-rehearsal-fixtures.py')


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='0028-fixtures-')
        self.root = Path(self.temp.name)
        self.repo = self.root / 'repo'
        self.manifest = self.root / 'manifest'
        self.repo.mkdir()
        self.manifest.mkdir()
        self.content = self.repo / 'data/responder/diaries-content/files-development-common'
        self.content.mkdir(parents=True)
        self.content_data = b'0028 isolated image bytes for unit test'
        self.digest = hashlib.sha256(self.content_data).hexdigest()
        file = self.content / 'diary-1828/images/example.jpg'
        file.parent.mkdir(parents=True)
        file.write_bytes(self.content_data)
        with (self.manifest / '0028-image-decisions.csv').open('w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=['fragment_id', 'occurrence_action', 'resolved_image_id', 'resolved_relative_path', 'expected_image_checksum'])
            writer.writeheader()
            for number in range(71):
                writer.writerow({'fragment_id': number + 1, 'occurrence_action': 'REMOVE_AS_IMAGE', 'resolved_image_id': '3', 'resolved_relative_path': 'diary-1828/images/example.jpg', 'expected_image_checksum': self.digest})
            writer.writerow({'fragment_id': 1564, 'occurrence_action': 'DEFER', 'resolved_image_id': '', 'resolved_relative_path': '', 'expected_image_checksum': ''})

    def tearDown(self):
        self.temp.cleanup()

    def plan(self):
        conversions = [{'date': ('1828-03-20' if i < 2 else ('1828-04-17' if i < 7 else '1829-07-08')),
                        'fragmentId': i + 1} for i in range(71)]
        result = {'schemaVersion': 1, 'mode': 'dry-run', 'producedBy': '0028-71-in-place-v1',
                  'databaseIdentity': 'TEST_DB_ONLY', 'filesRoot': 'TEST_MEDIA_ONLY',
                  'inputIdentity': 'TEST_REVIEW_ONLY', 'conversions': conversions,
                  'deferredFragments': [1564]}
        path = self.root / 'plan.json'
        path.write_text(json.dumps(result), encoding='utf-8')
        return path

    def test_copy_matches_checksum_and_is_independent(self):
        dest = self.root / 'out/files-root'
        stage.run(self.repo, self.manifest, str(self.content), dest)
        original = self.content / 'diary-1828/images/example.jpg'
        copied = dest / 'diary-1828/images/example.jpg'
        self.assertEqual(copied.read_bytes(), original.read_bytes())
        self.assertNotEqual(copied.stat().st_ino, original.stat().st_ino)
        self.assertTrue((dest.parent / 'MEDIA-COPY-RESULT.PRIVATE.json').is_file())

    def test_real_contract_has_72_rows_and_one_excluded_defer(self):
        files = stage.read_manifest(self.manifest)
        self.assertEqual(files, {'diary-1828/images/example.jpg': self.digest})

    def test_reject_unexpected_second_defer(self):
        target = self.manifest / '0028-image-decisions.csv'
        with target.open(newline='') as inp:
            rows = list(csv.DictReader(inp))
        rows[0]['occurrence_action'] = 'DEFER'
        with target.open('w', newline='') as out:
            w = csv.DictWriter(out, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        with self.assertRaises(ValueError):
            stage.read_manifest(self.manifest)

    def test_reject_deferred_catalogue_mapping(self):
        target = self.manifest / '0028-image-decisions.csv'
        with target.open(newline='') as inp:
            rows = list(csv.DictReader(inp))
        rows[-1]['resolved_image_id'] = '18'
        with target.open('w', newline='') as out:
            w = csv.DictWriter(out, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)
        with self.assertRaises(ValueError):
            stage.read_manifest(self.manifest)

    def test_no_overwrite_existing_media(self):
        dest = self.root / 'out/files-root'
        dest.mkdir(parents=True)
        with self.assertRaises(ValueError):
            stage.run(self.repo, self.manifest, str(self.content), dest)

    def test_stale_catalogue_file_fails_before_copy(self):
        (self.content / 'diary-1828/images/example.jpg').write_bytes(b'drift')
        with self.assertRaises(ValueError):
            stage.run(self.repo, self.manifest, str(self.content), self.root / 'out/files-root')
        self.assertFalse((self.root / 'out/files-root').exists())

    def test_path_traversal_fails(self):
        with self.assertRaises(ValueError):
            stage.validated_path(self.content, '../private/image.jpg')

    def test_rehearsal_plan_generates_rollback_fixture(self):
        plan = self.plan()
        fixtures.generate(type('A', (), {'plan': plan, 'dir': self.root})())
        info = json.loads((self.root / 'INJECTION-PARAMETERS.json').read_text())
        self.assertEqual(info['failureDate'], '1828-04-17')
        self.assertEqual(info['earlierCommittedExpected'], 2)
        self.assertEqual(info['failureFragment'], 7)
        self.assertIn('0028_REHEARSAL_INJECTED_FAILURE', (self.root / 'inject-failure.sql').read_text())

    def test_wrong_plan_scope_rejected(self):
        path = self.plan()
        plan = json.loads(path.read_text())
        plan['deferredFragments'] = []
        path.write_text(json.dumps(plan))
        with self.assertRaises(ValueError):
            fixtures.load_plan(path)

    def test_rehearsal_approval_is_not_production(self):
        path = self.plan()
        out = self.root / 'APPROVAL.json'
        fixtures.make_approval(type('A', (), {'plan': path, 'output': out, 'operator': 'tester'})())
        approval = json.loads(out.read_text())
        self.assertEqual(approval['scope'], 'RESTORED_REHEARSAL')
        self.assertEqual(approval['plan_sha256'], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertNotIn('permit-production-apply', approval)

    def test_cannot_overwrite_approval(self):
        path = self.plan()
        out = self.root / 'APPROVAL.json'
        out.write_text('{}')
        with self.assertRaises(ValueError):
            fixtures.make_approval(type('A', (), {'plan': path, 'output': out, 'operator': 'tester'})())


if __name__ == '__main__':
    unittest.main(verbosity=2)
