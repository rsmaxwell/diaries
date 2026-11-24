#!/usr/bin/env python3
"""Offline, fabricated-data tests for the read-only Step 1 collector."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'step1_inventory.py'
spec = importlib.util.spec_from_file_location('step1_inventory', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def row(fid, html, kind='MARQUEE', page=12, marq=None, image_id=None):
    return dict(fragment_id=fid, version=1, page_id=page, type=kind,
                image_id=image_id, year=1830, month=1, day=2, sequence='2.0000',
                text=html, lock_user_id=None, lock_session_id=None,
                lock_timestamp=None,
                marquees=[{'id': marq, 'page_id': page}] if marq else [])


class Step1Tests(unittest.TestCase):
    def test_html_inventory_handles_case_repeat_and_missing_src(self):
        value = '<IMG SRC="a&amp;b.png"><img src="a&amp;b.png"/><img alt="none">'
        self.assertEqual(mod.image_sources(value), ['a&b.png', 'a&b.png', ''])

    def test_review_drafts_and_drifts_not_preapproved(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            snapshot = root / 'snapshot.csv'
            with snapshot.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['kind', 'payload'])
                w.writerow(['identity', json.dumps({'database': 'test', 'postgres_version': '18'})])
                w.writerow(['image', json.dumps({'image_id': 4, 'checksum': 'a'*64, 'relative_path': 'a.jpg'})])
                w.writerow(['fragment', json.dumps(row(1, 'A <img src="one.jpg"> B <img src="two.jpg">', marq=8))])
                w.writerow(['fragment', json.dumps(row(2, 'Existing <img src="three.jpg">', kind='IMAGE', image_id=4))])
                w.writerow(['fragment', json.dumps(row(3, 'No embedded image', marq=9))])
            historical = root / 'old.csv'
            historical.write_text('fragment_id\n1\n2\n3\n', encoding='utf-8')
            output = root / 'out'
            output.mkdir()
            summary = mod.analyse(snapshot, output, historical)
            self.assertEqual(summary['counts']['total_fragments'], 3)
            self.assertEqual(summary['counts']['unreviewed_legacy_candidates'], 1)
            self.assertEqual(summary['counts']['total_legacy_occurrences'], 2)
            self.assertEqual(summary['counts']['unreviewed_disposition_rows'], 2)
            with (output / '0028-dispositions.UNREVIEWED.csv').open(newline='', encoding='utf-8') as f:
                records = list(csv.DictReader(f))
            self.assertEqual(len(records), 2)
            self.assertEqual([r['fragment_id'] for r in records], ['1', '3'])
            self.assertEqual(records[1]['embedded_image_count'], '0')
            self.assertEqual(records[1]['disposition'], '')
            self.assertEqual(records[0]['disposition'], '')
            self.assertEqual(records[0]['marquee_id'], '8')
            with (output / '0028-image-decisions.UNREVIEWED.csv').open(newline='', encoding='utf-8') as f:
                occurs = list(csv.DictReader(f))
            self.assertEqual([r['embedded_image_ordinal'] for r in occurs], ['1', '2'])
            self.assertTrue(all(r['occurrence_action'] == '' and r['resolved_image_id'] == '' for r in occurs))
            with (output / '0028-0022-candidate-drift.csv').open(newline='', encoding='utf-8') as f:
                drift = list(csv.DictReader(f))
            self.assertEqual({r['fragment_id']: r['status'] for r in drift},
                {'2': 'NOW_IMAGE_WITH_EMBEDDED_IMG', '3': 'NO_LONGER_CURRENT_LEGACY_CANDIDATE'})
            self.assertTrue((output / 'SHA256SUMS.txt').read_text())

    def test_historic_review_and_0024_xref_are_hints_only(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            snapshot = root / 'snapshot.csv'
            with snapshot.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['kind', 'payload'])
                w.writerow(['identity', '{"database": "fixture"}'])
                w.writerow(['image', json.dumps({'image_id': 9,
                    'checksum': 'b'*64, 'relative_path': 'photos/photo.jpg'})])
                w.writerow(['fragment', json.dumps(row(5, '<img src="photo.jpg">'))])
            ledger = root / 'ledger.json'
            ledger.write_text(json.dumps({'decisions': [
                {'fragment_type': 'IMAGE', 'database_fragment_id': 5}]}))
            xref = root / 'xref.csv'
            with xref.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['fragmentId', 'sourceSha256', 'imageId',
                            'relativePath', 'status', 'matchMethod'])
                w.writerow(['5', mod.digest('photo.jpg'), '9', 'photos/photo.jpg',
                            'MATCHED_ONE_IMAGE', 'UNIQUE_LOCAL_SUFFIX'])
            out = root / 'out'
            out.mkdir()
            summary = mod.analyse(snapshot, out, None, ledger, xref)
            self.assertEqual(summary['historicLedgerHintsStillCurrent'], 1)
            self.assertEqual(summary['xrefHintsWithCurrentSourceHash'], 1)
            with (out / '0028-0024-crossreference-hints.csv').open(newline='', encoding='utf-8') as f:
                hint = next(csv.DictReader(f))
            self.assertEqual(hint['xref_method'], 'UNIQUE_LOCAL_SUFFIX')
            self.assertEqual(hint['authorisation'], 'HINT_ONLY_NOT_APPROVED')
            with (out / '0028-image-decisions.UNREVIEWED.csv').open(newline='', encoding='utf-8') as f:
                decision = next(csv.DictReader(f))
            self.assertEqual(decision['resolved_image_id'], '')
            self.assertEqual(decision['occurrence_action'], '')

    def test_duplicate_fragment_rejected(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            snapshot = root / 'snapshot.csv'
            with snapshot.open('w', newline='', encoding='utf-8') as f:
                w = csv.writer(f)
                w.writerow(['kind', 'payload'])
                w.writerow(['identity', '{}'])
                for _ in range(2):
                    w.writerow(['fragment', json.dumps(row(10, '<img src="x">'))])
            output = root / 'out'
            output.mkdir()
            with self.assertRaisesRegex(ValueError, 'Duplicate Fragment'):
                mod.analyse(snapshot, output, None)

    def test_read_only_remote_script_contract(self):
        self.assertEqual(mod.COPY_SQL.split(None, 1)[0], 'COPY')
        self.assertIn('TO STDOUT WITH (FORMAT CSV, HEADER TRUE)', mod.COPY_SQL)
        self.assertNotIn('UPDATE ', mod.COPY_SQL.upper())
        self.assertNotIn('DELETE ', mod.COPY_SQL.upper())
        self.assertNotIn('INSERT ', mod.COPY_SQL.upper())

if __name__ == '__main__':
    unittest.main()
