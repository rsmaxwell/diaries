"""0028 Step 1: new source-viewer portal never replaces existing evidence."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import SCHEMA, sha
from step1_refresh_0051_portal_offline import refresh, INPUT_NAME, OUTPUT_NAME


class RefreshTests(unittest.TestCase):
    def fixture(self, tmp):
        root=Path(tmp)/'private'
        source_dir=root/'20261121T122838Z-post0051-v2'
        frozen_dir=root/'20261118T093606Z'
        source_dir.mkdir(parents=True)
        frozen_dir.mkdir(parents=True)
        frozen=frozen_dir/'current-schema-snapshot.PRIVATE.csv'
        original='<p>Text <img src="images/test.jpg"></p>'
        with frozen.open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=['kind','payload']);writer.writeheader()
            writer.writerow({'kind':'fragment','payload':json.dumps({
                'fragment_id':7,'version':1,'page_id':None,'text':original,'marquees':[]})})
        (frozen_dir/'SHA256SUMS.txt').write_text(sha(frozen.read_bytes())+'  '+frozen.name+'\n')
        doc={'schema':SCHEMA,'review_status':'UNREVIEWED_V2',
             'productionApplyAllowed':False,
             'fingerprints':{'inventory_sha256':sha(frozen.read_bytes())},
             'decisions':[{'fragment_id':'7','embedded_image_ordinal':'1',
              'source_html_sha256':sha(original),'source_img_sha256':sha('images/test.jpg'),
              'expected_fragment_version':'1','expected_page_id':'',
              'source_link_state':'NONE','source_link_url_PRIVATE':'',
              'source_marquee':{'status':'ABSENT','id':'','page_id':'','geometry_sha256':''},
              'disposition':'','occurrence_action':'','review_note':'','reviewed_at':'',
              'reviewed_by':'','legacy_review':{}}]}
        source=source_dir/INPUT_NAME
        source.write_text(json.dumps(doc),encoding='utf-8')
        (source_dir/'SHA256SUMS.txt').write_text(sha(source.read_bytes())+'  '+INPUT_NAME+'\n')
        return source,frozen

    def test_sealed_regeneration_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,frozen=self.fixture(tmp)
            checksums={p:p.read_bytes() for p in (source,frozen,
                        source.parent/'SHA256SUMS.txt',frozen.parent/'SHA256SUMS.txt')}
            out=refresh(source)
            self.assertEqual(OUTPUT_NAME,out.name)
            self.assertIn('Original Fragment HTML',out.read_text())
            self.assertIn('UNAPPROVED',out.read_text())
            self.assertIn('\\u003cimg',out.read_text())
            self.assertTrue(all(p.read_bytes()==content for p,content in checksums.items()))
            with self.assertRaises(FileExistsError):refresh(source)
            self.assertTrue(all(p.read_bytes()==content for p,content in checksums.items()))

    def test_tampered_v2_and_snapshot_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            source,frozen=self.fixture(tmp)
            source.write_text('{}')
            with self.assertRaisesRegex(ValueError,'SHA256'):
                refresh(source)
            self.assertFalse((source.parent/OUTPUT_NAME).exists())
        with tempfile.TemporaryDirectory() as tmp:
            source,frozen=self.fixture(tmp)
            frozen.write_text(frozen.read_text()+'garbage')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                refresh(source)
            self.assertFalse((source.parent/OUTPUT_NAME).exists())


if __name__=='__main__': unittest.main()
