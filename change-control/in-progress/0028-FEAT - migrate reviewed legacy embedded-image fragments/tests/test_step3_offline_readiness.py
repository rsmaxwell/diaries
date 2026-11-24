"""Synthetic-only tests for Step 3 OFFLINE readiness; no database or network."""
import csv
import hashlib
import importlib.util
import json
import pathlib
import tempfile
import unittest

THIS = pathlib.Path(__file__).resolve().parent
HELPER = THIS.parent / 'tools' / '0028-step3-readiness-audit.py'
spec = importlib.util.spec_from_file_location('step3_0028', str(HELPER))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

D = ('fragment_id','embedded_image_count','original_html_sha256',
     'expected_fragment_version','disposition','marquee_id')
I = ('fragment_id','embedded_image_ordinal','original_src_sha256',
     'resolved_image_id','resolved_relative_path','expected_image_checksum','occurrence_action')
V = ('fragment_id','embedded_image_ordinal','original_html_sha256',
     'source_img_sha256','link_handling','image_link_url_PRIVATE',
     'marquee_handling','source_marquee_status','source_marquee_id',
     'v2_review_confirmed')
H = 'a' * 64
B = 'b' * 64
C = 'c' * 64


def write_rows(path, headers, rows):
    with path.open('w',encoding='utf-8',newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def fixture(folder):
    path=pathlib.Path(folder)
    disp=[];images=[];preserve=[]
    for index in range(71):
        fid=str(index+1)
        link=index<30
        mar=index<22
        disp.append(dict(fragment_id=fid,embedded_image_count='1',
                         original_html_sha256=H,expected_fragment_version='0',
                         disposition='CONVERT_TO_IMAGE',marquee_id=fid if mar else ''))
        images.append(dict(fragment_id=fid,embedded_image_ordinal='1',
                           original_src_sha256=B,resolved_image_id='18',
                           resolved_relative_path='images/test.png',
                           expected_image_checksum=C,occurrence_action='CONVERT_TO_IMAGE'))
        preserve.append(dict(fragment_id=fid,embedded_image_ordinal='1',
                             original_html_sha256=H,source_img_sha256=B,
                             link_handling='PRESERVE' if link else 'NOT_PRESENT',
                             image_link_url_PRIVATE='https://example.invalid/x' if link else '',
                             marquee_handling='PRESERVE' if mar else 'NOT_APPLICABLE',
                             source_marquee_status='COMPLETE' if mar else 'ABSENT',
                             source_marquee_id=fid if mar else '',v2_review_confirmed='YES'))
    disp.append(dict(fragment_id='1564',embedded_image_count='1',
                     original_html_sha256=H,expected_fragment_version='0',
                     disposition='DEFER',marquee_id=''))
    images.append(dict(fragment_id='1564',embedded_image_ordinal='1',
                       original_src_sha256=B,resolved_image_id='',
                       resolved_relative_path='',expected_image_checksum='',occurrence_action='DEFER'))
    preserve.append(dict(fragment_id='1564',embedded_image_ordinal='1',original_html_sha256=H,
                         source_img_sha256=B,link_handling='NOT_PRESENT',
                         image_link_url_PRIVATE='',marquee_handling='NOT_APPLICABLE',
                         source_marquee_status='ABSENT',source_marquee_id='',
                         v2_review_confirmed=''))
    rec={'schema':'0028-step1-prepared-migration-inputs-v1',
         'status':'PREPARED_NOT_APPROVED','productionApplyAllowed':False,
         'migrationApproved':False,
         'counts':{'CONVERT_TO_IMAGE':71,'DEFER':1,
                   'links_preserved':30,'marquees_preserved':22}}
    tables=[(mod.EXPECTED[0],D,disp),(mod.EXPECTED[1],I,images),
            (mod.EXPECTED[2],V,preserve)]
    seal(path,rec,tables)
    return rec,tables


def seal(path,rec,tables):
    for filename,header,rows in tables:
        write_rows(path/filename,header,rows)
    rec['output_sha256']={filename:mod.file_sha(path/filename) for filename,_,_ in tables}
    (path/'PREPARATION-RESULT.json').write_text(json.dumps(rec),encoding='utf-8')


class OfflineReadinessTests(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory()
        self.addCleanup(self.t.cleanup)
        self.path=pathlib.Path(self.t.name)
        self.rec,self.tables=fixture(self.path)

    def assertRejected(self):
        with self.assertRaises(ValueError): mod.audit(self.path)

    def test_valid_review_is_offline_only(self):
        result=mod.audit(self.path)
        self.assertEqual(result['convertToImage'],71)
        self.assertEqual(result['defer'],1)
        self.assertFalse(result['productionApplyAuthorised'])
        self.assertFalse(result['productionSourceFreshnessVerified'])

    def test_changed_csv_bytes_rejected_by_receipt_digest(self):
        p=self.path/mod.EXPECTED[0]
        p.write_bytes(p.read_bytes()+b'\n')
        self.assertRejected()

    def test_non_approved_receipt_rejected(self):
        self.rec['productionApplyAllowed']=True
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_unexpected_deferred_id_rejected(self):
        self.tables[0][2][-1]['fragment_id']='1664'
        self.tables[1][2][-1]['fragment_id']='1664'
        self.tables[2][2][-1]['fragment_id']='1664'
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_missing_preserved_link_rejected(self):
        self.tables[2][2][0]['image_link_url_PRIVATE']=''
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_missing_original_marquee_rejected(self):
        self.tables[0][2][0]['marquee_id']=''
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_destructive_link_action_rejected(self):
        self.tables[2][2][0]['link_handling']='CLEAR'
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_missing_catalogue_digest_rejected(self):
        self.tables[1][2][0]['expected_image_checksum']=''
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

    def test_duplicate_source_fragment_rejected(self):
        self.tables[0][2][1]['fragment_id']='1'
        seal(self.path,self.rec,self.tables)
        self.assertRejected()

if __name__=='__main__':unittest.main()
