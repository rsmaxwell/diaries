"""0028 Step 1: frozen-HTML source suggestions are drafts, never approvals."""
import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import (
    extract_images, image_page_prefix, portal, sha, source_suggestions,
)


class SourceInferenceTests(unittest.TestCase):
    SIMPLE = ('<figure><img src="images/img2840-image-map-whitley-park.jpg" width="600px" />'
              '<figcaption>Whitley Park</figcaption></figure>')

    def example(self, original=None, status='MATCHED_ONE_IMAGE'):
        original = original if original is not None else self.SIMPLE
        images = extract_images(original)
        row = {
            'fragment_id':'84','embedded_image_ordinal':'1',
            'source_html_sha256':sha(original),
            'source_img_sha256':sha(images[0]['src']),
            'source_link_state':images[0]['link_state'],
            'source_link_url_PRIVATE':images[0]['link_url'] or '',
            'source_ambiguous':images[0]['source_ambiguous'],
            'live_source_drift':False,
            'source_status':status,
            'catalogue_cross_check':'MATCHED_SNAPSHOT_AND_FILE',
            'expected_page_id':'',
            'source_marquee':{'status':'ABSENT','id':'','page_id':'','geometry_sha256':''},
            'legacy_review':{'approved_page_id':'692','disposition':'CONVERT_TO_IMAGE'},
            'disposition':'','occurrence_action':'','approved_page_id':'',
            'suffix_verified':'','text_allocation':'','page_provenance':'',
            'review_note':'','reviewed_by':'','reviewed_at':'',
            'v2_review_confirmed':'','review_clear_confirmed':'',
            'review_remove_marquee_confirmed':'',
        }
        preview={'fragment_id':'84','ordinal':'1','original_html_PRIVATE':original,
                 'year':1828,'month':3,'day':20,'sequence':'12.0000'}
        return row,preview

    def test_simple_matched_single_image_suggests_draft_only(self):
        r,p=self.example()
        h=source_suggestions(r,p)
        self.assertEqual('CONVERT_TO_IMAGE',h['disposition'])
        self.assertEqual('REMOVE_AS_IMAGE',h['occurrence_action'])
        self.assertEqual('NOT_PRESENT',h['link_handling'])
        self.assertEqual('NOT_APPLICABLE',h['marquee_handling'])
        self.assertIn('img2840',h['_page_hint'])
        self.assertIn('historical v1 Page ID hint: 692 (unverified)',h['_page_hint'])
        self.assertIn('Page ID 692',h['page_provenance'])
        self.assertIn('no Page association',h['page_provenance'])
        self.assertIn('1828-03-20',h['text_allocation'])
        self.assertIn('12.0000',h['text_allocation'])
        self.assertIn('Whitley Park',h['text_allocation'])
        for key in ('approved_page_id','suffix_verified','v2_review_confirmed','reviewed_at','reviewed_by','review_clear_confirmed','review_remove_marquee_confirmed'):
            self.assertNotIn(key,h)
            self.assertEqual('',r[key])
        # No verified HTML supplied -> never guess a disposition.
        self.assertNotIn('disposition',source_suggestions(r))

    def test_linked_image_exact_url_suggested_without_clear(self):
        original=('<figure><a href="https://example.org/a?x=1&amp;y=2#z">'
                  '<img src="images/img2840-test.jpg" width="600px" />'
                  '<figcaption>Good</figcaption></a></figure>')
        r,p=self.example(original)
        h=source_suggestions(r,p)
        self.assertEqual('PRESERVE',h['link_handling'])
        self.assertEqual('https://example.org/a?x=1&y=2#z',h['image_link_url_PRIVATE'])
        self.assertEqual('CONVERT_TO_IMAGE',h['disposition'])
        self.assertNotIn('review_clear_confirmed',h)

    def test_unsafe_or_meaningful_markup_is_manual(self):
        examples=(
            self.SIMPLE+'"',  # stray quoted character must be preserved/reviewed
            '<p>Important narrative</p>'+self.SIMPLE,
            '<div>'+self.SIMPLE+'</div>',
            '<!-- history -->'+self.SIMPLE,
            self.SIMPLE+'<script>evil()</script>',
            '<figure><img src="images/img2840-a.jpg"/><img src="images/img2840-b.jpg"/></figure>',
            '<figure><img src="images/img2840-a.jpg" alt="Meaningful text"/></figure>',
        )
        for original in examples:
            with self.subTest(original=original[:45]):
                r,p=self.example(original)
                self.assertNotIn('disposition',source_suggestions(r,p))
                self.assertNotIn('text_allocation',source_suggestions(r,p))

    def test_unresolved_match_drift_and_marquee_need_manual(self):
        for key,value in (('source_status','AMBIGUOUS_PATH'),
                          ('catalogue_cross_check','NOT_RESOLVED'),
                          ('live_source_drift',True)):
            r,p=self.example();r[key]=value
            self.assertNotIn('disposition',source_suggestions(r,p))
        r,p=self.example()
        r['source_marquee']={'status':'COMPLETE','id':'55','page_id':'692','geometry_sha256':sha('geo')}
        r['expected_page_id']='692'
        h=source_suggestions(r,p)
        self.assertEqual('PRESERVE',h['marquee_handling'])
        self.assertNotIn('disposition',h)

    def test_source_preview_identity_must_match(self):
        r,p=self.example()
        for field,value in (('fragment_id','999'),('ordinal','2'),('original_html_PRIVATE','<img/>')):
            mismatch=copy.deepcopy(p);mismatch[field]=value
            with self.assertRaisesRegex(ValueError,'identity/hash mismatch'):
                source_suggestions(r,mismatch)
        p=copy.deepcopy(p);r['source_img_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'IMG identity mismatch'):
            source_suggestions(r,p)

    def test_frozen_page_relationship_is_hint_not_approval(self):
        r,p=self.example()
        r['expected_page_id']='692'
        h=source_suggestions(r,p)
        self.assertIn('already belongs to Page ID 692',h['page_provenance'])
        self.assertNotIn('approved_page_id',h)

    def test_page_prefix_not_assumed_to_be_ownership(self):
        self.assertEqual('img2833',image_page_prefix('images/img2833-note.jpg'))
        self.assertEqual('',image_page_prefix('images/something-img2833-note.jpg'))
        self.assertEqual('',image_page_prefix('images/whitley.jpg'))

    def test_preview_and_review_data_separate_and_inert(self):
        r,p=self.example()
        original=p['original_html_PRIVATE']
        previews=[dict(p,readable_text_PRIVATE='Whitley Park',image_start=original.index('<img'),
                       image_end=original.index('/>')+2)]
        doc={'schema':'0028-0051-review-v2','fingerprints':{'inventory_sha256':'test'},
             'decisions':[r]}
        portal_html=portal(doc,previews)
        self.assertIn('source-derived conversion',portal_html.lower())
        self.assertIn('CONVERT_TO_IMAGE',portal_html)
        self.assertIn('Page ID hint',portal_html)
        self.assertIn('connect-src \'none\'',portal_html)
        self.assertNotIn('original_html_PRIVATE',r)
        self.assertEqual('',r['disposition'])
        self.assertEqual('',r['reviewed_at'])


if __name__=='__main__':
    unittest.main()
