"""0028 V2 caption override: synthetic validation, old draft compatibility and inert UI."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import (
    SCHEMA, sha, marquee_evidence, validate, portal, original_figcaption
)

class CaptionOverrideTests(unittest.TestCase):
    def fixture(self):
        source='<figure><img src="images/voyage.png"><figcaption>Voyage for Copenhagen to St Petersburg</figcaption></figure>'
        current={'575': {'fragment_id':575,'version':0,'page_id':None,'text':source,'marquees':[]}}
        row={'fragment_id':'575','embedded_image_ordinal':'1','source_html_sha256':sha(source),
             'source_img_sha256':sha('images/voyage.png'),'expected_fragment_version':'0',
             'expected_page_id':'','source_marquee':marquee_evidence(current['575']),
             'source_link_state':'NONE','source_link_url_PRIVATE':'',
             'source_link_url_sha256':sha(''),'source_ambiguous':False,
             'live_source_drift':False,'source_status':'MATCHED_ONE_IMAGE',
             'catalogue_cross_check':'MATCHED_SNAPSHOT_AND_FILE','legacy_review':{
                 'caption_override':'DO NOT USE HISTORICAL OVERRIDE'},
             'caption_override':'','disposition':'','occurrence_action':'',
             'link_handling':'','image_link_url_PRIVATE':'','marquee_handling':'',
             'suffix_verified':'','text_allocation':'','approved_page_id':'',
             'page_provenance':'','review_note':'','reviewed_by':'','reviewed_at':'',
             'v2_review_confirmed':''}
        prepared={'schema':SCHEMA,'fingerprints':{'proposals_sha256':'a','inventory_sha256':'b'},
                  'review_status':'UNREVIEWED_V2','productionApplyAllowed':False,'decisions':[row]}
        reviewed=copy.deepcopy(prepared)
        reviewed['decisions'][0].update(disposition='CONVERT_TO_IMAGE',occurrence_action='REMOVE_AS_IMAGE',
            link_handling='NOT_PRESENT',marquee_handling='NOT_APPLICABLE',suffix_verified='YES',
            approved_page_id='744',page_provenance='Reviewed editorial Page 744',
            text_allocation='Preserve date and sequence',review_note='Fix for to from by explicit decision',
            reviewed_by='Test reviewer',reviewed_at='2026-11-22T09:05:00Z',v2_review_confirmed='YES')
        return prepared,reviewed,current,source

    def check(self,prep,reviewed,current):
        return validate(prep,reviewed,current)

    def test_blank_override_and_old_json_still_valid(self):
        prep,reviewed,current,_=self.fixture()
        del reviewed['decisions'][0]['caption_override']  # Draft (33) and earlier.
        self.assertEqual(0,self.check(prep,reviewed,current)['rowsWithBlockers'])
        self.assertFalse(self.check(prep,reviewed,current)['productionApplyAllowed'])

    def test_caption_override_is_reviewer_editable_and_requires_no_schema_upgrade(self):
        prep,reviewed,current,_=self.fixture()
        reviewed['decisions'][0]['caption_override']='Voyage from Copenhagen to St Petersburg'
        result=self.check(prep,reviewed,current)
        self.assertEqual(0,result['rowsWithBlockers'])
        self.assertFalse(result['productionApplyAllowed'])
        self.assertEqual('',prep['decisions'][0]['caption_override'])
        self.assertEqual('DO NOT USE HISTORICAL OVERRIDE', prep['decisions'][0]['legacy_review']['caption_override'])

    def test_invalid_override_fails_closed(self):
        prep,reviewed,current,_=self.fixture()
        for value in ('  ','<img src=x>','oops\nother', 'x'*2001, 12):
            reviewed['decisions'][0]['caption_override']=value
            with self.subTest(value=str(value)[:20]),self.assertRaisesRegex(ValueError,'caption override'):
                self.check(prep,reviewed,current)

    def test_override_without_conversion_is_blocked(self):
        prep,reviewed,current,_=self.fixture()
        reviewed['decisions'][0].update(disposition='DEFER',occurrence_action='DEFER',
            caption_override='New caption')
        self.assertIn('CAPTION_OVERRIDE_WITHOUT_CONVERSION',self.check(prep,reviewed,current)['blockers'])

    def test_frozen_original_caption_and_inert_rendering(self):
        prep,reviewed,current,source=self.fixture()
        preview={'fragment_id':'575','ordinal':'1','original_html_PRIVATE':source,
                 'readable_text_PRIVATE':'voyage','image_start':8,'image_end':37,
                 'year':1829,'month':6,'day':26,'sequence':'1.0000'}
        fact=original_figcaption(preview)
        self.assertEqual({'verified':True,'value':'Voyage for Copenhagen to St Petersburg'},fact)
        doc=portal(prep,[preview]);self.assertIn('id="caption_override"',doc)
        self.assertIn('const originalCaptions=',doc)
        self.assertIn('caption.textContent=',doc)
        self.assertIn("'caption_override','text_allocation'",doc)
        self.assertIn("source.decisions=rows",doc)
        self.assertIn("connect-src 'none'",doc)
        self.assertIn('UNAPPROVED',doc)
        self.assertNotIn('<img src="images/voyage.png">',doc)
        self.assertEqual('DO NOT USE HISTORICAL OVERRIDE',prep['decisions'][0]['legacy_review']['caption_override'])
        self.assertFalse(prep['productionApplyAllowed'])

if __name__=='__main__':unittest.main()
