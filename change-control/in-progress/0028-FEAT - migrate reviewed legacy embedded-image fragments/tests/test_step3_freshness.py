"""Synthetic, no-network, no-DB tests for 0028 production freshness comparator."""
import csv
import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

CODE = Path(__file__).resolve().parents[1] / 'tools' / '0028-step3-freshness.py'
spec = importlib.util.spec_from_file_location('fresh0028', str(CODE))
fresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fresh)


def digest(s):
    return hashlib.sha256(s.encode('utf-8')).hexdigest()


class FreshnessTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.manifest = root/'manifest'; self.manifest.mkdir()
        self.files = root/'files'; self.files.mkdir()
        self.base = root/'baseline.csv'
        self.current = root/'current.csv'
        self.candidates = root/'candidates.csv'
        self.now = datetime.now(timezone.utc)
        self.fragments = []
        self.catalogue = []
        self.dispositions = []
        self.images = []
        self.preserve = []
        self.occurrences = []
        for fid in list(range(1, 72)) + [1564]:
            convert = fid!=1564
            linked = fid<=30
            marquee = fid<=22
            src = 'image_{}.png'.format(fid)
            html = '<p><img src="{}"></p>'.format(src)
            f = {'fragment_id':fid,'version':2,'page_id':fid+100,
                 'type':'MARQUEE','image_id':None,'year':1828,'month':3,'day':20,
                 'sequence':'1.00','text':html,'lock_user_id':None,
                 'lock_session_id':None,'marquees':[]}
            if marquee:
                f['marquees']=[{'id':fid+1000,'page_id':fid+100,'version':1,
                                'x':1.0,'y':2.0,'width':100.0,'height':200.0}]
            self.fragments.append(f)
            d={'fragment_id':str(fid),'expected_fragment_version':'2',
                'page_id':str(fid+100),'marquee_id':str(fid+1000) if marquee else '',
                'fragment_type_before':'MARQUEE','year':'1828','month':'3','day':'20',
                'sequence':'1','original_html_sha256':digest(html),
                'embedded_image_count':'1',
                'disposition':'CONVERT_TO_IMAGE' if convert else 'DEFER'}
            self.dispositions.append(d)
            i={'fragment_id':str(fid),'embedded_image_ordinal':'1',
               'original_src_sha256':digest(src),
               'resolved_relative_path':src if convert else '',
               'resolved_image_id':str(fid) if convert else '',
               'expected_image_checksum':digest('test media '+str(fid)) if convert else '',
               'occurrence_action':'REMOVE_AS_IMAGE' if convert else 'DEFER'}
            self.images.append(i)
            v={'fragment_id':str(fid),'embedded_image_ordinal':'1',
               'original_html_sha256':digest(html),'source_img_sha256':digest(src),
               'approved_page_id':str(fid+100),
               'link_handling':'PRESERVE' if linked else 'NOT_PRESENT',
               'image_link_url_PRIVATE':'https://example.invalid/'+str(fid) if linked else '',
               'source_link_url_sha256':digest('https://example.invalid/'+str(fid)) if linked else '',
               'marquee_handling':'PRESERVE' if marquee else 'NOT_APPLICABLE',
               'source_marquee_id':str(fid+1000) if marquee else '',
               'source_marquee_page_id':str(fid+100) if marquee else '',
               'source_marquee_version':'1' if marquee else ''}
            self.preserve.append(v)
            self.occurrences.append({'fragment_id':str(fid),'embedded_image_ordinal':'1'})
            if convert:
                (self.files/src).write_text('test media '+str(fid))
                self.catalogue.append({'image_id':fid,'relative_path':src,
                                       'checksum':digest('test media '+str(fid))})
        self.write()

    def tearDown(self):
        self.tmp.cleanup()

    @staticmethod
    def csv_write(path, rows):
        with path.open('w', encoding='utf-8', newline='') as out:
            writer=csv.DictWriter(out, fieldnames=list(rows[0]))
            writer.writeheader();writer.writerows(rows)

    def snapshot(self, path, fragments):
        rows=[]
        for f in fragments: rows.append({'kind':'fragment','payload':json.dumps(f)})
        for img in self.catalogue:rows.append({'kind':'image','payload':json.dumps(img)})
        rows.append({'kind':'identity','payload':json.dumps({'database':'diaries',
              'postgres_version':'18.1','snapshot_at':self.now.isoformat()})})
        self.csv_write(path, rows)

    def write(self):
        filenames=['0028-dispositions.csv','0028-image-decisions.csv',
                   '0028-v2-preservation-decisions.PRIVATE.csv']
        for name,rows in zip(filenames,(self.dispositions,self.images,self.preserve)):
            self.csv_write(self.manifest/name,rows)
        receipt={'schema':'0028-step1-prepared-migration-inputs-v1',
                 'status':'PREPARED_NOT_APPROVED','productionApplyAllowed':False,
                 'migrationApproved':False,
                 'output_sha256':{n:fresh.file_hash(self.manifest/n) for n in filenames}}
        (self.manifest/'PREPARATION-RESULT.json').write_text(json.dumps(receipt))
        self.snapshot(self.base, self.fragments)
        self.snapshot(self.current,self.fragments)
        self.csv_write(self.candidates,self.occurrences)

    def result(self):
        return fresh.inspect(self.manifest,self.base,self.current,
                             self.candidates,self.files,now=self.now)

    def assert_block(self, code):
        report=self.result()
        self.assertEqual('BLOCKED_SOURCE_DRIFT', report['status'])
        self.assertTrue(any(x.startswith(code) for x in report['errors']),report['errors'])
        self.assertFalse(report['productionApplyAllowed'])

    def test_full_72_pass_but_not_authorised(self):
        result=self.result()
        self.assertEqual('PASS_SOURCE_FRESHNESS',result['status'], result['errors'])
        self.assertEqual(71,result['valid_NAS_files'])
        self.assertEqual(30,result['preserved_links'])
        self.assertEqual(22,result['preserved_marquees'])
        self.assertFalse(result['productionApplyAuthorised'])

    def test_current_marquee_placement_and_newer_version_allowed(self):
        self.fragments[0]['marquees'][0].update(x=42.5,width=235.7,version=3)
        self.write()
        result=self.result()
        self.assertEqual('PASS_SOURCE_FRESHNESS',result['status'],result['errors'])
        self.assertEqual(1,result['permitted_marquee_version_increments'])

    def test_missing_marquee_blocked(self):
        self.fragments[0]['marquees']=[];self.write()
        self.assert_block('MARQUEE_PRESENCE_CHANGED')

    def test_reassigned_marquee_page_blocked(self):
        self.fragments[0]['marquees'][0]['page_id']=450;self.write()
        self.assert_block('MARQUEE_ID_OR_PAGE_CHANGED')

    def test_replaced_marquee_id_blocked(self):
        self.fragments[0]['marquees'][0]['id']=9982;self.write()
        self.assert_block('MARQUEE_ID_OR_PAGE_CHANGED')

    def test_old_marquee_version_blocked(self):
        self.fragments[0]['marquees'][0]['version']=0;self.write()
        self.assert_block('MARQUEE_VERSION_REVERSED')

    def test_source_html_drift_blocked(self):
        self.fragments[0]['text']+='<p>changed</p>';self.write()
        self.assert_block('SOURCE_HTML_CHANGED')

    def test_legacy_null_source_page_and_null_type_are_not_drift(self):
        # Production has legitimate unpaged/NULL-typed embedded-image
        # fragments. Their frozen CSV page_id and type are empty strings.
        row = self.fragments[30]  # one without a source Marquee
        row['page_id'] = None
        row['type'] = None
        self.dispositions[30]['page_id'] = ''
        self.dispositions[30]['fragment_type_before'] = ''
        self.write()
        result = self.result()
        self.assertEqual('PASS_SOURCE_FRESHNESS', result['status'], result['errors'])

    def test_legacy_null_source_page_cannot_be_reassigned(self):
        row = self.fragments[30]
        row['page_id'] = None
        row['type'] = None
        self.dispositions[30]['page_id'] = ''
        self.dispositions[30]['fragment_type_before'] = ''
        self.write()
        row['page_id'] = 999
        self.write()
        self.assert_block('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT')

    def test_legacy_null_source_page_is_not_zero(self):
        row = self.fragments[30]
        row['page_id'] = None
        self.dispositions[30]['page_id'] = '0'
        self.write()
        self.assert_block('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT')

    def test_legacy_null_source_type_still_fails_if_changed(self):
        row = self.fragments[30]
        row['page_id'] = None
        row['type'] = None
        self.dispositions[30]['page_id'] = ''
        self.dispositions[30]['fragment_type_before'] = ''
        self.write()
        row['type'] = 'MARQUEE'
        self.write()
        self.assert_block('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT')

    def test_legacy_null_source_version_still_fails_if_changed(self):
        row = self.fragments[30]
        row['page_id'] = None
        row['type'] = None
        self.dispositions[30]['page_id'] = ''
        self.dispositions[30]['fragment_type_before'] = ''
        self.write()
        row['version'] = 5
        self.write()
        self.assert_block('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT')

    def test_deferred_legacy_null_source_page(self):
        row = self.fragments[-1]  # deferred 1564
        row['page_id'] = None
        row['type'] = None
        self.dispositions[-1]['page_id'] = ''
        self.dispositions[-1]['fragment_type_before'] = ''
        self.write()
        result = self.result()
        self.assertEqual('PASS_SOURCE_FRESHNESS', result['status'], result['errors'])

    def test_source_fragment_version_drift_blocked(self):
        self.fragments[0]['version']=3;self.write()
        self.assert_block('FRAGMENT_ID_VERSION_PAGE_TYPE_DRIFT')

    def test_reviewed_lock_blocked(self):
        self.fragments[0]['lock_session_id']='test-session';self.write()
        self.assert_block('REVIEWED_FRAGMENT_LOCKED')

    def test_new_unreviewed_candidate_blocked(self):
        self.occurrences.append({'fragment_id':'9000','embedded_image_ordinal':'1'})
        self.write()
        self.assert_block('NEW_OR_UNREVIEWED_LEGACY_OCCURRENCE')

    @staticmethod
    def run_real_wrapper_result_gate(exit_code):
        # Exercise the exact final result gate from the shipped Bash wrapper.
        # No production hosts, inventory or Docker are invoked.
        wrapper = CODE.parent / 'verify-0028-step3-production-freshness.sh'
        content = wrapper.read_text(encoding='utf-8')
        marker = '\nrc=$?\n'
        if '\n)\n' not in content or '\n) &&' in content or marker not in content:
            raise AssertionError('Preflight script no longer has a standalone fail-fast subshell')
        gate = 'rc=$?\n' + content.rsplit(marker, 1)[1]
        return subprocess.run(['bash', '-c', '( exit {} )\n{}'.format(exit_code, gate)],
                              capture_output=True, text=True)

    def test_production_comparison_failure_never_prints_overall_pass(self):
        result = self.run_real_wrapper_result_gate(7)
        self.assertEqual(7, result.returncode)
        self.assertIn('BLOCKED', result.stderr)
        self.assertNotIn('PREFLIGHT: PASS', result.stdout)

    def test_production_comparison_success_prints_overall_pass(self):
        result = self.run_real_wrapper_result_gate(0)
        self.assertEqual(0, result.returncode)
        self.assertIn('PREFLIGHT: PASS', result.stdout)

    def test_catalogue_checksum_change_blocked(self):
        self.catalogue[0]['checksum']=digest('other');self.write()
        self.assert_block('CATALOGUE_IMAGE_ID_PATH_OR_HASH_DRIFT')

    def test_image_file_checksum_change_blocked(self):
        (self.files/'image_1.png').write_text('different')
        self.assert_block('NAS_FILES_CHECKSUM_CHANGED')

    def test_frozen_csv_tampering_is_rejected(self):
        with (self.manifest/'0028-dispositions.csv').open('a') as output:output.write('bad\n')
        with self.assertRaisesRegex(ValueError,'Frozen manifest checksum'):
            self.result()

    def test_stale_snapshot_blocked(self):
        from datetime import timedelta
        rows=fresh.csv_rows(self.current)
        ident=json.loads(rows[-1]['payload'])
        ident['snapshot_at']=(self.now-timedelta(hours=2)).isoformat()
        rows[-1]['payload']=json.dumps(ident)
        self.csv_write(self.current,rows)
        self.assert_block('PRODUCTION_SNAPSHOT_NOT_FRESH')

    def test_wrong_database_name_blocked(self):
        self.snapshot(self.base,self.fragments)
        rows=fresh.csv_rows(self.current)
        j=json.loads(rows[-1]['payload']);j['database']='another_db'
        rows[-1]['payload']=json.dumps(j)
        self.csv_write(self.current,rows)
        self.assert_block('PRODUCTION_DATABASE_NAME_CHANGED')


if __name__=='__main__': unittest.main()
