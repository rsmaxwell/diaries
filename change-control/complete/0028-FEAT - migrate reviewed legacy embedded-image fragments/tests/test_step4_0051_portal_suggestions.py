"""0028/0051 offline review UI suggestions: source-only, no implicit approval."""
import copy
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import portal, source_suggestions, sha


class PortalSuggestionTests(unittest.TestCase):
    def source(self):
        return {
            'fragment_id':'1564','embedded_image_ordinal':'1',
            'expected_page_id':'', 'source_link_state':'NONE',
            'source_link_url_PRIVATE':'', 'source_ambiguous':False,
            'source_marquee':{'status':'ABSENT', 'id':'', 'geometry_sha256':'', 'page_id':''},
            'legacy_review':{'disposition':'DEFER','review_note':'Historical ambiguity'},
            'disposition':'','occurrence_action':'','reviewed_by':'','reviewed_at':'',
            'v2_review_confirmed':'', 'review_clear_confirmed':'',
            'review_remove_marquee_confirmed':''
        }

    def test_unlinked_unmarqueed_1564_conservative(self):
        r=self.source()
        self.assertEqual({'link_handling':'NOT_PRESENT', 'image_link_url_PRIVATE':'',
                          'marquee_handling':'NOT_APPLICABLE'},source_suggestions(r))
        doc=portal({'schema':'0028-0051-review-v2','fingerprints':{'inventory_sha256':'test'},'decisions':[r]})
        self.assertIn("connect-src 'none'",doc)
        self.assertIn('Resume from exported PRIVATE JSON',doc)
        self.assertIn('No migration approval',doc)
        self.assertNotIn('unsafe-eval',doc)
        # source suggestions are embedded separately from the decision data
        self.assertEqual('',r['disposition'])
        self.assertEqual('',r['reviewed_at'])
        self.assertEqual('',r['v2_review_confirmed'])

    def test_link_preservation_exact_decoded_url(self):
        r=self.source()
        r.update(source_link_state='LINKED',source_link_url_PRIVATE='https://example.org/x?one=1&two=2#pic')
        self.assertEqual('PRESERVE',source_suggestions(r)['link_handling'])
        self.assertEqual(r['source_link_url_PRIVATE'],source_suggestions(r)['image_link_url_PRIVATE'])

    def test_dangerous_or_ambiguous_link_never_suggested(self):
        for link in ('javascript:alert(1)','https://name:pass@example.org/',
                     'https://example.org/bad space'):
            r=self.source();r.update(source_link_state='LINKED',source_link_url_PRIVATE=link)
            self.assertNotIn('link_handling',source_suggestions(r))
        r=self.source();r.update(source_link_state='LINKED',
                                 source_link_url_PRIVATE='https://example.org/',source_ambiguous=True)
        self.assertNotIn('link_handling',source_suggestions(r))

    def test_marquee_non_destructive_and_complete_only(self):
        r=self.source()
        r['source_marquee']={'status':'COMPLETE','id':'5','page_id':'33','geometry_sha256':sha('geo')}
        r['expected_page_id']='33'
        self.assertEqual('PRESERVE',source_suggestions(r)['marquee_handling'])
        r['source_marquee']['page_id']='44'
        self.assertNotIn('marquee_handling',source_suggestions(r))
        r['source_marquee']['status']='GEOMETRY_NOT_IN_SOURCE'
        self.assertNotIn('marquee_handling',source_suggestions(r))

    def test_untrusted_html_never_breaks_json_script(self):
        r=self.source();r['legacy_review']['review_note']='</script><img src=x onerror=alert(1)>'
        doc=portal({'schema':'0028-0051-review-v2','fingerprints':{},'decisions':[r]})
        self.assertNotIn('</script><img',doc)
        self.assertIn('\\u003c/script\\u003e',doc)


if __name__=='__main__': unittest.main()
