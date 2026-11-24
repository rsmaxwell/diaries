import hashlib
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from step1_propose_content_review import HtmlInventory, evidence_check, review_proposal


class ProposalTests(unittest.TestCase):
    def parse(self, html):
        x = HtmlInventory(); x.feed(html); return x

    def base(self, ownership='NO_PAGE_NO_MARQUEE', status='MATCHED_ONE_IMAGE'):
        return {'0024_status': status, 'catalogue_cross_check': 'MATCHED_SNAPSHOT_AND_FILE', 'page_ownership': ownership}

    def test_image_wrapping_link_preserved_for_review(self):
        result = self.parse('<figure><a href="https://example.com/"><img src="x.jpg"><figcaption>caption</figcaption></a></figure>')
        self.assertEqual(['https://example.com/'], result.image_wrapping_hrefs)
        self.assertEqual('caption', result.caption)
        self.assertEqual('', result.other_text)
        self.assertEqual(0, result.caption_links)
        self.assertEqual(1, result.figure_count)

    def test_caption_link_is_not_image_wrapping_link(self):
        result = self.parse('<figure><img src="x.jpg"><figcaption><a href="https://example.com">caption</a></figcaption></figure>')
        self.assertEqual([], result.image_wrapping_hrefs)
        self.assertEqual(1, result.caption_links)

    def test_literal_trailing_quote_is_not_discarded(self):
        result = self.parse('<figure><img src="a.png">"<figcaption>A</figcaption></figure>')
        self.assertEqual('"', result.other_text)

    def test_extra_narrative_not_lost(self):
        result = self.parse('<h2>Note</h2><p>Original notes</p><figure><img src="a.png"><figcaption>A</figcaption></figure>')
        self.assertEqual('Note Original notes', result.other_text)

    def test_proposal_unowned_link_requires_both_checks(self):
        disposition, state = review_proposal(self.base(), self.parse('<a href="https://x"><img src="x.png"></a>'))
        self.assertEqual(('CONVERT_TO_IMAGE','BLOCKED_PAGE_AND_EXTERNAL_LINK'),(disposition,state))

    def test_proposal_owned_link_requires_marquee_checks(self):
        disposition, state = review_proposal(self.base('DIRECT_AND_MARQUEE_AGREE'), self.parse('<a href="https://x"><img src="x.png"></a>'))
        self.assertEqual(('CONVERT_TO_IMAGE','BLOCKED_MARQUEE_AND_EXTERNAL_LINK'),(disposition,state))

    def test_ambiguous_image_is_deferred(self):
        self.assertEqual(('DEFER','BLOCKED_IMAGE_AMBIGUOUS'), review_proposal(self.base(status='AMBIGUOUS_PATH'), self.parse('<img src="x.png">')))

    def test_evidence_manifest_detects_byte_drift(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'sample.csv').write_text('original',encoding='utf8')
            digest=hashlib.sha256(b'original').hexdigest()
            (root/'SHA256SUMS.txt').write_text(f'{digest}  sample.csv\n',encoding='utf8')
            self.assertEqual([],evidence_check(root))
            (root/'sample.csv').write_text('changed',encoding='utf8')
            with self.assertRaisesRegex(ValueError,'HASH MISMATCH'):
                evidence_check(root)
            self.assertEqual(['sample.csv'],evidence_check(root,skip=('sample.csv',)))

if __name__ == '__main__':
    unittest.main()
