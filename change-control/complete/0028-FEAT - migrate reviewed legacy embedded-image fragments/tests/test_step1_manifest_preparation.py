#!/usr/bin/env python3
"""Offline synthetic fixtures for 0028 reviewed manifest preparation (no database)."""
import csv
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

module_path=Path(__file__).resolve().parent.parent/'tools'/'step1_prepare_reviewed_manifest.py'
spec=importlib.util.spec_from_file_location('prepare_0028',str(module_path))
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sha(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()

class ManifestPreparationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.paths={name:self.root/name for name in ('review.json','snapshot.csv','mapping.csv','check.json','summary.json')}
        decisions=[];fragments=[];mappings=[]
        for i in range(1,73):
            fid=str(i);src='images/fixture-{}.png'.format(i)
            txt='<figure><img src="{}" /><figcaption>Caption {}</figcaption></figure>'.format(src,i)
            has_link=i<=30
            has_marquee=i<=22
            m={'status':'COMPLETE' if has_marquee else 'ABSENT',
               'id':str(1000+i) if has_marquee else '',
               'page_id':'752' if has_marquee else '',
               'version':'0' if has_marquee else '',
               'geometry_sha256':'a'*64 if has_marquee else ''}
            link='https://example.test/image/{}/?a=1&b=2#part'.format(i) if has_link else ''
            d=dict(fragment_id=fid,embedded_image_ordinal='1',
                   source_html_sha256=sha(txt),source_img_sha256=sha(src),
                   expected_fragment_version='0',expected_page_id='',
                   source_marquee=m,source_link_url_sha256=sha(link),
                   source_link_url_PRIVATE=link,
                   disposition='CONVERT_TO_IMAGE' if i<72 else 'DEFER',
                   occurrence_action='REMOVE_AS_IMAGE' if i<72 else 'DEFER',
                   approved_page_id='752' if i<72 else '',
                   page_provenance='Fixture',suffix_verified='YES',
                   text_allocation='No extra content',caption_override='',
                   review_note='Reviewed fixture',reviewed_by='Example Reviewer',
                   reviewed_at='2026-11-23T12:00:00Z',
                   v2_review_confirmed='YES' if i<72 else '',
                   review_clear_confirmed='NO',
                   review_remove_marquee_confirmed='NO',
                   link_handling='PRESERVE' if has_link else 'NOT_PRESENT',
                   image_link_url_PRIVATE=link,
                   marquee_handling='PRESERVE' if has_marquee else 'NOT_APPLICABLE',
                   legacy_review={'caption_effective':'Caption {}'.format(i)})
            if i==72: d['fragment_id']='1564'; fid='1564'
            decisions.append(d)
            f=dict(fragment_id=int(fid),version=0,page_id=None,type=None,image_id=None,
                   year=1829,month=7,day=8,sequence='{}.0000'.format(i),
                   text=txt,marquees=[dict(id=1000+i,version=0,page_id=752)] if has_marquee else [])
            fragments.append(f)
            if i<72:
                mappings.append(dict(fragment_id=fid,embedded_image_ordinal='1',
                       approved_page_id='752',reviewed_image_id=str(i),
                       current_relative_path_PRIVATE='diary/images/fixture-{}.png'.format(i),
                       pre0052_checksum='b'*64,current_checksum='c'*64,
                       checksum_change='UNCHANGED',source_html_sha256=sha(txt),
                       reviewed_caption_override=''))
        self.review={'schema':'0028-0051-review-v2','productionApplyAllowed':False,
                     'decisions':decisions}
        self.check={'rows':72,'rowsWithBlockers':0,'productionApplyAllowed':False,
                    'byDisposition':{'CONVERT_TO_IMAGE':71,'DEFER':1}}
        self._write_json('review.json',self.review)
        self._write_json('check.json',self.check)
        self._write_csv('snapshot.csv',['kind','payload'],
                        [dict(kind='fragment',payload=json.dumps(f)) for f in fragments])
        self._write_csv('mapping.csv',list(mappings[0]),mappings)
        self.summary={'status':'PASS','productionApplyAllowed':False,
            'review_sha256':mod.sha_file(self.paths['review.json']),
            'current_snapshot_sha256':mod.sha_file(self.paths['snapshot.csv']),
            'catalogue_metadata_changed_image_ids':['3','18'],
            'snapshot_timestamp':'2026-11-23T12:00:00Z'}
        self._write_json('summary.json',self.summary)
    def _write_json(self,n,d):self.paths[n].write_text(json.dumps(d),encoding='utf-8')
    def _write_csv(self,n,fields,rows):
        with self.paths[n].open('w',encoding='utf-8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    def run_assemble(self):
        return mod.assemble(self.paths['review.json'],self.paths['snapshot.csv'],
                     self.paths['mapping.csv'],self.paths['check.json'],
                     self.paths['summary.json'])
    def sync_review(self):
        self._write_json('review.json',self.review)
        self.summary['review_sha256']=mod.sha_file(self.paths['review.json'])
        self._write_json('summary.json',self.summary)
    def test_all_72_and_preservation_fields(self):
        dispositions,images,policies,summary=self.run_assemble()
        self.assertEqual((len(dispositions),len(images),len(policies)),(72,72,72))
        self.assertEqual(sum(x['link_handling']=='PRESERVE' for x in policies),30)
        self.assertEqual(sum(x['marquee_handling']=='PRESERVE' for x in policies),22)
        self.assertEqual([x['resolved_image_id'] for x in images if x['fragment_id']=='1'],['1'])
        self.assertEqual(images[-1]['occurrence_action'],'DEFER')
    def test_changed_review_hash_fails(self):
        self.review['decisions'][0]['review_note']='Tampered'
        self._write_json('review.json',self.review)
        with self.assertRaisesRegex(ValueError,'different review'):self.run_assemble()
    def test_changed_snapshot_hash_fails(self):
        with self.paths['snapshot.csv'].open('a',encoding='utf-8') as f:f.write('\n')
        with self.assertRaisesRegex(ValueError,'different production snapshot'):self.run_assemble()
    def test_unapproved_link_clearing_fails(self):
        self.review['decisions'][0]['link_handling']='CLEAR_CONFIRMED'; self.sync_review()
        with self.assertRaisesRegex(ValueError,'destructive or undecided link'):self.run_assemble()
    def test_marquee_removal_fails(self):
        self.review['decisions'][0]['marquee_handling']='REMOVE_CONFIRMED'; self.sync_review()
        with self.assertRaisesRegex(ValueError,'destructive or undecided Marquee'):self.run_assemble()
    def test_missing_image_mapping_fails(self):
        rows=mod.read_csv(self.paths['mapping.csv'])
        self._write_csv('mapping.csv',list(rows[0]),rows[1:])
        with self.assertRaisesRegex(ValueError,'71 mapping'):self.run_assemble()
    def test_source_html_drift_fails(self):
        rows=mod.read_csv(self.paths['snapshot.csv'])
        obj=json.loads(rows[0]['payload']);obj['text']='edited';rows[0]['payload']=json.dumps(obj)
        self._write_csv('snapshot.csv',list(rows[0]),rows)
        self.summary['current_snapshot_sha256']=mod.sha_file(self.paths['snapshot.csv'])
        self._write_json('summary.json',self.summary)
        with self.assertRaisesRegex(ValueError,'Source text changed'):self.run_assemble()

if __name__=='__main__':unittest.main()
