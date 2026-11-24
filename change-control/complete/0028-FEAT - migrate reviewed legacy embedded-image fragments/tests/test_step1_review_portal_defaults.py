"""0028 review-portal convenience defaults; standard-library tests only."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from step1_review_portal import extract_caption, resolve_caption, assess_decisions, digest, JS, make_html


class DefaultsTests(unittest.TestCase):
    @staticmethod
    def row(html='<figure><img src="a.png"><figcaption>Whitley Park</figcaption></figure>', *, other='', caption='Whitley Park'):
        extracted, status = extract_caption(html)
        return {'fragment_id': '84', 'embedded_image_ordinal': '1',
                'original_html_sha256': digest(html.encode()),
                'original_src_sha256': digest(b'a.png'),
                'page_id': '692', 'marquee_id': '',
                '0024_status': 'MATCHED_ONE_IMAGE', 'catalogue_cross_check': 'MATCHED_SNAPSHOT_AND_FILE',
                'proposal_external_image_hrefs_PRIVATE': '', 'proposal_unallocated_text_PRIVATE': other,
                'proposal_caption_plaintext_PRIVATE': caption,
                'verified_caption_status': status, 'verified_original_caption': extracted,
                'proposal_caption_link_count': '0'}

    def choice(self, row, **kwargs):
        d={'fragment_id': row['fragment_id'], 'embedded_image_ordinal': '1',
           'original_html_sha256': row['original_html_sha256'],
           'original_src_sha256': row['original_src_sha256'],
           'disposition': 'CONVERT_TO_IMAGE', 'occurrence_action': 'REMOVE_AS_IMAGE',
           'suffix_verified': 'YES', 'link_handling': 'NOT_PRESENT',
           'reviewed_by': 'Reviewer', 'reviewed_at': '2026-11-18T12:30:00Z',
           'review_note': 'Source checked', 'text_allocation': ''}
        d.update(kwargs)
        return d

    @staticmethod
    def check(row, choice):
        return assess_decisions([row], 'sha1', 'sha2',
            {'schema':'0028-human-review-v1', 'source_sha256':'sha1',
             'source_inventory_sha256':'sha2', 'decisions':[choice]})

    def test_caption_plaintext_entity_extraction(self):
        self.assertEqual(('A & B', 'UNIQUE_FIGCAPTION'),
            extract_caption('<figure><figcaption>A &amp; B</figcaption></figure>'))

    def test_caption_whitley_park_default(self):
        row=self.row()
        self.assertEqual(('Whitley Park', 'EXISTING_FIGCAPTION'), resolve_caption(row, ''))
        self.assertEqual(0, self.check(row, self.choice(row, caption_override='',
            caption_effective='Whitley Park',caption_source='EXISTING_FIGCAPTION'))['rowsWithBlockers'])

    def test_explicit_caption_override_wins(self):
        row=self.row()
        self.assertEqual(('New caption', 'REVIEWER_OVERRIDE'), resolve_caption(row, '  New caption  '))
        self.assertEqual(0, self.check(row,self.choice(row,caption_override='New caption',
            caption_effective='New caption',caption_source='REVIEWER_OVERRIDE'))['rowsWithBlockers'])

    def test_changed_exported_caption_is_detected(self):
        row=self.row()
        report=self.check(row,self.choice(row,caption_override='',
            caption_effective='Tampered caption',caption_source='EXISTING_FIGCAPTION'))
        self.assertIn('CAPTION_RESOLUTION_MISMATCH',report['blockers'])

    def test_missing_caption_requires_allocation_acknowledgement(self):
        row=self.row('<img src="a.png">', caption='')
        self.assertEqual(('', 'NO_AUTOMATIC_CAPTION'), resolve_caption(row, ''))
        report=self.check(row,self.choice(row,caption_override='',caption_effective='',
            caption_source='NO_AUTOMATIC_CAPTION'))
        self.assertIn('TEXT_ALLOCATION_UNREVIEWED_OR_EMPTY_NOT_ACKNOWLEDGED',report['blockers'])

    def test_multiple_captions_do_not_default(self):
        html='<figure><figcaption>First</figcaption><figcaption>Second</figcaption></figure>'
        row=self.row(html,caption='First Second')
        self.assertEqual('REQUIRES_MANUAL_REVIEW', row['verified_caption_status'])
        report=self.check(row,self.choice(row))
        self.assertIn('AMBIGUOUS_CAPTION_REQUIRES_MANUAL_REVIEW', report['blockers'])

    def test_caption_hyperlink_does_not_default(self):
        text='<figure><figcaption><a href="https://example.com">Linked caption</a></figcaption></figure>'
        self.assertEqual(('', 'REQUIRES_MANUAL_REVIEW'),extract_caption(text))

    def test_extra_text_still_requires_explicit_allocation(self):
        row=self.row(other='Other explanatory prose')
        report=self.check(row,self.choice(row))
        self.assertIn('TEXT_ALLOCATION_UNREVIEWED_OR_EMPTY_NOT_ACKNOWLEDGED',report['blockers'])

    def test_original_draft_v1_without_new_fields_still_valid(self):
        row=self.row()
        self.assertEqual(0,self.check(row,self.choice(row))['rowsWithBlockers'])

    def test_js_defaults_and_review_timestamps_present(self):
        self.assertIn('function beginReview(row)',JS)
        self.assertIn('new Date().toISOString()',JS)
        self.assertIn('global-reviewer',JS)
        self.assertIn('caption_override',JS)
        self.assertIn('caption_effective:currentCaption(r)[0]',JS)
        doc=make_html([self.row()], 'a'*64,'b'*64,{'84':{'text':'<figure>Whitley Park</figure>'}})
        self.assertIn('Caption override (blank = verified original figcaption)',doc)

if __name__=='__main__':
    unittest.main()
