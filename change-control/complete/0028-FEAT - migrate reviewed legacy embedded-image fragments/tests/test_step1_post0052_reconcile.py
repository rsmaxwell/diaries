#!/usr/bin/env python3
"""Synthetic offline regressions: no production calls, mutations or raw logs."""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FEATURE = Path(__file__).resolve().parents[1]
PRIVATE = FEATURE/'evidence/Step 1/private'
TOOL = FEATURE/'tools/step1_post0052_reconcile_readonly.py'
REVIEW = PRIVATE/'0028-0051-review-v2.DRAFT.PRIVATE (91).json'
# Test the known complete (91) draft after applying the same Fragment 598
# confirmation only in-memory: never alter private source evidence on disk.
BASELINE_SNAPSHOT = PRIVATE/'20261121T122838Z-post0051-current/current-schema-snapshot.PRIVATE.csv'
FROZEN_SNAPSHOT = PRIVATE/'20261118T093606Z/current-schema-snapshot.PRIVATE.csv'
PROPOSALS = PRIVATE/'0028-proposed-review.PRIVATE.csv'
CANDIDATES = PRIVATE/'20261121T122838Z-post0051-current/0028-image-decisions.UNREVIEWED.csv'


class Post0052ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.current = self.base/'current.csv'
        self.review = self.base/'review.json'
        self.candidates = self.base/'candidates.csv'
        # Synthetic snapshot has 0052 changes for 3 and 18, all else fixed.
        with BASELINE_SNAPSHOT.open(encoding='utf-8', newline='') as file:
            rows = list(csv.DictReader(file))
        for row in rows:
            item = json.loads(row['payload'])
            if row['kind'] == 'identity':
                item['snapshot_at'] = '2026-11-23T14:50:00+00:00'
            elif row['kind'] == 'image' and item['image_id'] in (3, 18):
                item['checksum'] = ('a' if item['image_id'] == 3 else 'b')*64
                item['version'] = 1
            row['payload'] = json.dumps(item)
        self.snapshot_rows = rows
        self.write_snapshot()
        draft = json.loads(REVIEW.read_text(encoding='utf-8'))
        fragment = [d for d in draft['decisions'] if d['fragment_id'] == '598'][0]
        fragment['v2_review_confirmed'] = 'YES'
        fragment['reviewed_at'] = '2026-11-23T14:17:18.073Z'
        self.review.write_text(json.dumps(draft), encoding='utf-8')
        shutil.copy2(CANDIDATES, self.candidates)

    def write_snapshot(self):
        with self.current.open('w',encoding='utf-8',newline='') as file:
            writer = csv.DictWriter(file,fieldnames=['kind','payload'],lineterminator='\n')
            writer.writeheader(); writer.writerows(self.snapshot_rows)

    def run_check(self):
        out = self.base/'out'
        cmd = [sys.executable, str(TOOL),
            '--frozen-snapshot',str(FROZEN_SNAPSHOT),
            '--previous-snapshot',str(BASELINE_SNAPSHOT),
            '--current-snapshot',str(self.current),
            '--current-candidates',str(self.candidates),
            '--proposals',str(PROPOSALS),
            '--review',str(self.review),
            '--output',str(out)]
        res = subprocess.run(cmd,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True)
        status = json.loads((out/'0028-post0052-reconciliation-summary.json').read_text()) if out.exists() else None
        return res.returncode,status

    def test_expected_0052_changes_pass(self):
        code,report = self.run_check()
        self.assertEqual(code,0,report)
        self.assertEqual(report['status'],'PASS')
        self.assertEqual(report['reviewed_conversions'],71)
        self.assertEqual(report['explicit_deferred'],1)
        self.assertEqual(report['catalogue_metadata_changed_image_ids'],['18','3'])
        self.assertFalse(report['productionApplyAllowed'])

    def test_old_hermitage_checksum_fails_closed(self):
        for row in self.snapshot_rows:
            if row['kind'] == 'image':
                item = json.loads(row['payload'])
                if item['image_id'] == 18:
                    item['checksum'] = '2097979bd1ca47370a55c0f6053167a96f541a5c04adfe4ff52dc564ccc97d5a'
                    row['payload'] = json.dumps(item)
        self.write_snapshot()
        code,report = self.run_check()
        self.assertNotEqual(code,0)
        self.assertTrue(any('0052_IMAGE_STILL_HAS_OLD_CHECKSUM_18' == x for x in report['errors']))

    def test_protected_image_change_fails_closed(self):
        for row in self.snapshot_rows:
            if row['kind'] == 'image':
                item = json.loads(row['payload'])
                if item['image_id'] == 25:
                    item['checksum'] = 'c'*64
                    row['payload'] = json.dumps(item)
        self.write_snapshot()
        code,report = self.run_check()
        self.assertNotEqual(code,0)
        self.assertIn('PROTECTED_IMAGE_METADATA_CHANGED_25',report['errors'])

    def test_source_date_drift_fails_closed(self):
        for row in self.snapshot_rows:
            if row['kind'] == 'fragment':
                item = json.loads(row['payload'])
                if item['fragment_id'] == 84:
                    item['day'] = 21
                    row['payload'] = json.dumps(item)
        self.write_snapshot()
        code,report = self.run_check()
        self.assertNotEqual(code,0)
        self.assertIn('SOURCE_METADATA_DRIFT_84_day',report['errors'])

    def test_new_legacy_occurrence_fails_closed(self):
        with self.candidates.open(encoding='utf-8',newline='') as file:
            source_rows = list(csv.DictReader(file))
        newrow = dict(source_rows[0]);newrow['fragment_id']='999999'
        with self.candidates.open('w',encoding='utf-8',newline='') as file:
            writer=csv.DictWriter(file,fieldnames=source_rows[0].keys(),lineterminator='\n')
            writer.writeheader();writer.writerows(source_rows+[newrow])
        code,report = self.run_check()
        self.assertNotEqual(code,0)
        self.assertIn('LIVE_CANDIDATE_COVERAGE_CHANGED',report['errors'])


if __name__ == '__main__':
    unittest.main()
