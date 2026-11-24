import hashlib
import json
import tempfile
import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'tools'))
from step1_review_portal import (
    assess_decisions, digest, make_html, verify_manifest, write_with_checksums
)


class PortalTests(unittest.TestCase):
    def row(self, *, page='', link='', image_status='MATCHED_ONE_IMAGE', marquee='', caption=''):
        return dict(fragment_id='12', embedded_image_ordinal='1', date='1830-01-02',
            original_html_sha256=digest(b'<img src="a.png">'), original_src_sha256=digest(b'a.png'),
            page_id=page, marquee_id=marquee, page_ownership='NO_PAGE_NO_MARQUEE',
            triage_priority='P2', candidate_page_context='NO_PAGE_ONE_DATE_PAGE_HINT_ONLY',
            **{'0024_status':image_status, '0024_match_method':'UNIQUE_LOCAL_SUFFIX'},
            catalogue_cross_check='MATCHED_SNAPSHOT_AND_FILE',
            proposal_external_image_hrefs_PRIVATE=link,
            proposal_caption_plaintext_PRIVATE=caption,
            proposal_unallocated_text_PRIVATE='')

    def decision(self, row, choice='DEFER', **overrides):
        d=dict(fragment_id=row['fragment_id'], embedded_image_ordinal=row['embedded_image_ordinal'],
            original_html_sha256=row['original_html_sha256'], original_src_sha256=row['original_src_sha256'],
            disposition=choice, occurrence_action={
                'DEFER':'DEFER','KEEP_LEGACY':'KEEP_INLINE',
                'CONVERT_TO_IMAGE':'REMOVE_AS_IMAGE','SPLIT_MARQUEE_AND_IMAGE':'REMOVE_AS_IMAGE'
            }[choice], approved_page_id='', page_provenance='', suffix_verified='',
            marquee_handling='', link_handling='', text_allocation='',
            review_note='Explicitly reviewed test case', reviewed_by='Example reviewer',
            reviewed_at='2026-11-18T11:00:00Z')
        d.update(overrides)
        return d

    def assess(self, row, decision):
        return assess_decisions([row], 'proposalhash', 'inventoryhash', dict(schema='0028-human-review-v1',
            source_sha256='proposalhash', source_inventory_sha256='inventoryhash',
            decisions=[decision]))

    def test_offline_html_escapes_script_in_original_html(self):
        row=self.row()
        malicious='</script><img src="https://outside.example/track"><script>alert(1)</script>'
        doc=make_html([row], 'a'*64,'b'*64, {'12': {'text':malicious}})
        self.assertNotIn(malicious,doc)
        self.assertIn(r'\u003c/script\u003e',doc)
        self.assertIn("img-src 'none'; connect-src 'none'",doc)
        self.assertIn("setText('original',row.original_html_PRIVATE)",doc)
        self.assertIn('NO AUTOMATIC CONVERSIONS',doc)
        self.assertIn('0028-human-review-v1',doc)

    def test_frozen_noop_defer_is_allowed_as_a_review_not_apply(self):
        row=self.row(link='https://example.com',image_status='AMBIGUOUS_PATH')
        status=self.assess(row,self.decision(row))
        self.assertEqual(0,status['rowsWithBlockers'])
        self.assertFalse(status['migrationApproved'])
        self.assertFalse(status['productionApplyAllowed'])

    def test_keep_legacy_is_noop_for_linked_image(self):
        row=self.row(page='22',link='https://example.com',marquee='5')
        status=self.assess(row,self.decision(row,'KEEP_LEGACY'))
        self.assertEqual(0,status['rowsWithBlockers'])
        self.assertEqual({'KEEP_LEGACY':1},status['byDisposition'])

    def test_linked_conversion_unconditionally_blocked_even_with_claimed_support(self):
        row=self.row(page='22',link='https://example.com',marquee='5')
        d=self.decision(row,'CONVERT_TO_IMAGE',suffix_verified='YES',
            marquee_handling='REMOVE_CONFIRMED',link_handling='SUPPORTED_LOSSLESS')
        status=self.assess(row,d)
        self.assertIn('IMAGE_LINK_PRESERVATION_NOT_IMPLEMENTED',status['blockers'])

    def test_no_page_and_suffix_review_are_required_for_conversion(self):
        row=self.row()
        status=self.assess(row,self.decision(row,'CONVERT_TO_IMAGE',link_handling='NOT_PRESENT'))
        self.assertIn('NO_AUTHORISED_PAGE_ID',status['blockers'])
        self.assertIn('NO_PAGE_PROVENANCE',status['blockers'])
        self.assertIn('SUFFIX_NOT_INDEPENDENTLY_VERIFIED',status['blockers'])
        d=self.decision(row,'CONVERT_TO_IMAGE',approved_page_id='12',page_provenance='Verified scan',
                        suffix_verified='YES',link_handling='NOT_PRESENT',text_allocation='No caption; retain empty text')
        status=self.assess(row,d)
        self.assertEqual(0,status['rowsWithBlockers'])
        self.assertFalse(status['productionApplyAllowed'])

    def test_original_caption_defaults_without_manual_allocation(self):
        row=self.row(page='22',caption='Keep this caption')
        d=self.decision(row,'CONVERT_TO_IMAGE',suffix_verified='YES',link_handling='NOT_PRESENT')
        self.assertEqual(0,self.assess(row,d)['rowsWithBlockers'])
        d['text_allocation']='Keep original caption and verify reader'
        self.assertEqual(0,self.assess(row,d)['rowsWithBlockers'])

    def test_ambiguous_image_blocks_conversion(self):
        row=self.row(page='22',image_status='AMBIGUOUS_PATH')
        d=self.decision(row,'CONVERT_TO_IMAGE',suffix_verified='YES',link_handling='NOT_PRESENT')
        self.assertIn('UNRESOLVED_IMAGE',self.assess(row,d)['blockers'])

    def test_source_drift_and_duplicate_identity_rejected(self):
        row=self.row(); d=self.decision(row)
        with self.assertRaisesRegex(ValueError,'fingerprint'):
            assess_decisions([row],'proposalhash','inventoryhash',dict(schema='0028-human-review-v1',
                source_sha256='other',source_inventory_sha256='inventoryhash',decisions=[d]))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            assess_decisions([row,row],'proposalhash','inventoryhash',dict(schema='0028-human-review-v1',
                source_sha256='proposalhash',source_inventory_sha256='inventoryhash',decisions=[d,d]))
        with self.assertRaisesRegex(ValueError,'hash'):
            d['original_src_sha256']='changed'
            self.assess(row,d)

    def test_write_manifest_hashes_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/'out'
            write_with_checksums(dest,{'test.txt':b'hello'})
            verify_manifest(dest)
            with self.assertRaisesRegex(ValueError,'overwrite'):
                write_with_checksums(dest,{'test.txt':b'again'})
            (dest/'test.txt').write_text('altered')
            with self.assertRaisesRegex(ValueError,'HASH MISMATCH'):
                verify_manifest(dest)

    def test_invalid_review_timestamp_is_blocker(self):
        row=self.row();d=self.decision(row, reviewed_at='yesterday')
        self.assertIn('INVALID_REVIEW_TIMESTAMP',self.assess(row,d)['blockers'])

if __name__=='__main__':
    unittest.main()
