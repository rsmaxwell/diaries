"""Non-destructive, synthetic 0051 migration compatibility reviewer regression."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import (
    extract_images, valid_url, marquee_evidence, sha, validate, portal, SCHEMA
)


class CompatibilityV2Tests(unittest.TestCase):
    def source(self, *, marquee=True, linked=True):
        href='https://archive.example/a?x=1&y=2#zoom'
        original='<a href="https://archive.example/a?x=1&amp;y=2#zoom"><img src="a.png"></a>' if linked else '<img src="a.png">'
        fragments={'72': {'fragment_id':72,'version':7,'page_id':18,'text':original,
                          'marquees':[{'id':5,'version':3,'page_id':18,'x':2.5,'y':1.0,'width':4.2,'height':5.5}] if marquee else []}}
        row={'fragment_id':'72','embedded_image_ordinal':'1',
             'source_html_sha256':sha(original),'source_img_sha256':sha('a.png'),
             'expected_fragment_version':'7','expected_page_id':'18',
             'source_marquee':marquee_evidence(fragments['72']),
             'source_link_state':'LINKED' if linked else 'NONE',
             'source_link_url_PRIVATE':href if linked else '',
             'source_link_url_sha256':sha(href if linked else ''),
             'source_ambiguous':False,'live_source_drift':False,
             'source_status':'MATCHED_ONE_IMAGE','catalogue_cross_check':'MATCHED_SNAPSHOT_AND_FILE',
             'legacy_review':{},'disposition':'','occurrence_action':'','link_handling':'',
             'image_link_url_PRIVATE':'','marquee_handling':'','approved_page_id':'',
             'page_provenance':'','suffix_verified':'','text_allocation':'',
             'review_note':'','reviewed_by':'','reviewed_at':'','v2_review_confirmed':''}
        return row,fragments

    def decision(self,row,*,marquee='PRESERVE',link='PRESERVE'):
        r=copy.deepcopy(row)
        r.update(disposition='CONVERT_TO_IMAGE',occurrence_action='REMOVE_AS_IMAGE',
                 link_handling=link,image_link_url_PRIVATE=row['source_link_url_PRIVATE'] if link=='PRESERVE' else '',
                 marquee_handling=marquee,suffix_verified='YES',
                 text_allocation='Retain verified original text and chronology',
                 review_note='Explicit synthetic reviewed conversion',
                 reviewed_by='Test reviewer',reviewed_at='2026-11-20T15:00:00Z',
                 v2_review_confirmed='YES')
        return r

    def check(self,row,decision,current=None):
        src={'schema':SCHEMA,'fingerprints':{'proposals_sha256':'abc','inventory_sha256':'def'},'decisions':[row]}
        out={'schema':SCHEMA,'fingerprints':src['fingerprints'],'decisions':[decision]}
        return validate(src,out,current)

    def test_exact_link_with_query_fragment_and_html_entity(self):
        src='<a href="https://archive.example/a?x=1&amp;y=2#zoom"><img src="a.png"></a>'
        imgs=extract_images(src)
        self.assertEqual('LINKED',imgs[0]['link_state'])
        self.assertEqual('https://archive.example/a?x=1&y=2#zoom',imgs[0]['link_url'])
        self.assertTrue(valid_url(imgs[0]['link_url']))

    def test_two_images_under_one_anchor_requires_review(self):
        images=extract_images('<a href="https://archive.example/"><img src="a"><img src="b"></a>')
        self.assertEqual(['AMBIGUOUS','AMBIGUOUS'],[x['link_state'] for x in images])

    def test_dangerous_urls_are_rejected(self):
        for url in ('javascript:alert(1)','data:image/png;base64,aaa',
                    'https://name:password@example.org/','https://example.org/bad space',
                    'http://example.org/%QQ','https://example.org:99999/a'):
            self.assertFalse(valid_url(url),url)

    def test_lossless_link_and_marquee_preservation(self):
        row,current=self.source()
        report=self.check(row,self.decision(row),current)
        self.assertEqual(0,report['rowsWithBlockers'])
        self.assertFalse(report['productionApplyAllowed'])

    def test_missing_geometry_blocks_conversion(self):
        row,current=self.source()
        row['source_marquee']={'status':'GEOMETRY_NOT_IN_SOURCE','id':'5',
            'page_id':'18','version':'','geometry_sha256':''}
        decision=self.decision(row)
        report=self.check(row,decision,current)
        self.assertIn('MARQUEE_GEOMETRY_OR_VERSION_NOT_FROZEN',report['blockers'])

    def test_changed_link_is_detected(self):
        row,current=self.source()
        d=self.decision(row)
        d['image_link_url_PRIVATE']='https://archive.example/other'
        self.assertIn('IMAGE_LINK_EXACT_ROUNDTRIP_FAILED',self.check(row,d,current)['blockers'])

    def test_explicit_link_clear_needs_second_confirmation(self):
        row,current=self.source()
        d=self.decision(row,link='CLEAR_CONFIRMED')
        self.assertIn('LINK_CLEAR_NOT_EXPLICITLY_CONFIRMED',self.check(row,d,current)['blockers'])
        d['review_clear_confirmed']='YES'
        self.assertEqual(0,self.check(row,d,current)['rowsWithBlockers'])

    def test_marquee_remove_needs_second_confirmation(self):
        row,current=self.source()
        d=self.decision(row,marquee='REMOVE_CONFIRMED')
        self.assertIn('MARQUEE_REMOVAL_NOT_EXPLICITLY_CONFIRMED',self.check(row,d,current)['blockers'])
        d['review_remove_marquee_confirmed']='YES'
        self.assertEqual(0,self.check(row,d,current)['rowsWithBlockers'])

    def test_cross_page_marquee_and_stale_fragment_block(self):
        row,current=self.source()
        altered=copy.deepcopy(row)
        altered['source_marquee']['page_id']='99'
        self.assertIn('CROSS_PAGE_MARQUEE',self.check(altered,self.decision(altered),current)['blockers'])
        current['72']['version']=8
        self.assertIn('STALE_OR_CHANGED_LIVE_FRAGMENT',self.check(row,self.decision(row),current)['blockers'])

    def test_no_link_no_marquee_valid(self):
        row,current=self.source(marquee=False,linked=False)
        d=self.decision(row,marquee='NOT_APPLICABLE',link='NOT_PRESENT')
        self.assertEqual(0,self.check(row,d,current)['rowsWithBlockers'])

    def test_no_implicit_approval(self):
        row,current=self.source()
        d=self.decision(row)
        d['v2_review_confirmed']=''
        self.assertIn('V2_RECONFIRMATION_REQUIRED',self.check(row,d,current)['blockers'])
        self.assertIn('FRESH_READONLY_DB_SNAPSHOT_REQUIRED',self.check(row,d)['blockers'])

    def test_source_tamper_fatal_and_portal_inert(self):
        row,current=self.source()
        d=self.decision(row)
        d['source_link_url_sha256']='0000'
        with self.assertRaisesRegex(ValueError,'evidence drift'):
            self.check(row,d,current)
        doc=portal({'schema':SCHEMA,'decisions':[row]})
        self.assertIn("connect-src 'none'",doc)
        self.assertNotIn('</script><img',doc)
        self.assertIn('UNAPPROVED',doc)


if __name__=='__main__': unittest.main()
