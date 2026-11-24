"""Synthetic offline tests for 0028 context triage. Never query production."""
import csv
from pathlib import Path
import json
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from step1_make_review import assemble as make_review, sha
from step1_triage_context import (
    date_context, fragment_date, history, historic_index, page_anchor,
    priority, assemble, order_key,
)
# Existing Step 1 test fixture is part of the repository.
from test_step1_review import fixture


def fragment(fid, seq, page, day=2, marquee=None):
    return dict(fragment_id=fid, sequence=seq, page_id=page,
                marquees=[] if marquee is None else [marquee],
                year=1942, month=1, day=day, text=f'<p>{fid}</p>')


class TriageTests(unittest.TestCase):
    def test_same_date_single_page_is_hint_not_assignment(self):
        unowned=fragment(2,'2.0000',None)
        prev=fragment(1,'1.0000',5)
        nxt=fragment(3,'3.0000',5)
        context=date_context(unowned,[nxt,unowned,prev])
        self.assertEqual(context['candidate_page_context'], 'NO_PAGE_ONE_DATE_PAGE_HINT_ONLY')
        self.assertEqual(context['date_other_page_ids_HINT_ONLY'], '5')
        self.assertEqual(context['adjacent_page_agreement_HINT_ONLY'],'BOTH_NEAREST_AGREE_NOT_PROOF')
        self.assertIsNone(unowned['page_id'])

    def test_conflicting_context_does_not_select_page(self):
        candidate=fragment(2,'2.0000',None)
        context=date_context(candidate,[fragment(1,'1',8),candidate,fragment(3,'3',9)])
        self.assertEqual(context['date_other_page_ids_HINT_ONLY'], '8|9')
        self.assertEqual(context['adjacent_page_agreement_HINT_ONLY'], 'NEAREST_DIFFER')
        self.assertEqual(context['candidate_page_context'], 'NO_PAGE_MULTIPLE_DATE_PAGES_HINT_ONLY')

    def test_no_context_is_not_made_up(self):
        candidate=fragment(2,'2',None)
        context=date_context(candidate,[fragment(1,'1',None),candidate])
        self.assertEqual(context['date_other_page_count'],'0')
        self.assertEqual(context['nearest_before_page_Hint'],'')
        self.assertEqual(context['candidate_page_context'], 'NO_PAGE_NO_DATE_ANCHORS')

    def test_page_mismatch_is_not_used_as_anchor(self):
        bad=fragment(1,'1',8,marquee={'page_id':9})
        candidate=fragment(2,'2',None)
        self.assertEqual(page_anchor(bad),'')
        self.assertEqual(date_context(candidate,[bad,candidate])['date_other_page_count'],'0')

    def test_history_id_and_sha_and_other_id_constraint(self):
        f=fragment(4,'1',None)
        import hashlib
        sha256=hashlib.sha256(f['text'].encode()).hexdigest()
        decision={'database_fragment_id':4,'resolution':'MATCH_EXACT',
                  'provenance':{'source_manifest':{'html_sha256':sha256,'date':fragment_date(f),'source_key':'a'}}}
        self.assertEqual(history(f,historic_index({'decisions':[decision]}))['historic_link_strength_HINT_ONLY'],
                         'ID_AND_HTML_SHA_AGREE_HISTORY_ONLY')
        other=fragment(5,'1',None)
        self.assertEqual(history(other,historic_index({'decisions':[decision]}))['historic_link_strength_HINT_ONLY'],
                         'NO_UNIQUE_HISTORY_LINK')

    def test_history_id_mismatch_is_flag_not_approval(self):
        f=fragment(4,'1',None)
        d={'database_fragment_id':4,'resolution':'MATCH_EDITED_KEEP_SOURCE',
           'provenance':{'source_manifest':{'html_sha256':'a'*64,'date':fragment_date(f)}}}
        h=history(f,historic_index({'decisions':[d]}))
        self.assertEqual(h['historic_link_strength_HINT_ONLY'],'ID_LINK_HTML_NOT_MATCHED_HISTORY_ONLY')
        self.assertEqual(h['historic_resolution_HINT_ONLY'],'MATCH_EDITED_KEEP_SOURCE')

    def test_ambiguous_image_trumps_context(self):
        pri, checks=priority({'0024_status':'AMBIGUOUS_PATH','catalogue_cross_check':'NOT_RESOLVED',
                            'page_ownership':'NO_PAGE_NO_MARQUEE'}, {'date_other_page_count':'1'})
        self.assertEqual(pri,'P0_IMAGE_AMBIGUOUS_OR_INVALID')
        self.assertIn('RESOLVE_UNMATCHED_IMAGE_OR_DEFER',checks)

    def create_evidence(self, base):
        private=base/'private';private.mkdir()
        frozen, derived=fixture(private)
        review=private/'review';make_review(frozen,derived,review)
        ledger=base/'review-ledger.json'
        ledger.write_text(json.dumps({'schema_version':1,'decisions':[]}),encoding='utf-8')
        return frozen, derived, review, ledger, private

    def test_integrated_offline_assembly_has_no_decisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen,derived,review,ledger,private=self.create_evidence(Path(tmp))
            result=assemble(frozen,derived,review,ledger,private/'triage')
            self.assertEqual(result['candidateFragments'],2)
            self.assertEqual(result['candidateOccurrences'],2)
            self.assertEqual(result['counts']['P0_IMAGE_AMBIGUOUS_OR_INVALID'],1)
            self.assertEqual(result['counts']['P4_PAGE_AGREES_BUT_SUFFIX_UNREVIEWED'],1)
            with (private/'triage'/'0028-context-triage.PRIVATE.csv').open(newline='') as f:
                rows=list(csv.DictReader(f))
            self.assertEqual(len(rows),2)
            self.assertTrue(all(not r['review_disposition'] and not r['review_occurrence_action'] for r in rows))
            self.assertIn('NO_UNIQUE_HISTORY_LINK',rows[0]['historic_link_strength_HINT_ONLY'])
            self.assertTrue((private/'triage'/'SHA256SUMS.txt').is_file())
            self.assertTrue(all(len(line.split('  '))==2 for line in (private/'triage'/'SHA256SUMS.txt').read_text().splitlines()))

    def test_refuse_public_output_and_existing_directory(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            frozen,derived,review,ledger,private=self.create_evidence(root)
            with self.assertRaisesRegex(ValueError,'inside the existing private'):
                assemble(frozen,derived,review,ledger,root/'unprotected')
            out=private/'triage';out.mkdir()
            with self.assertRaisesRegex(ValueError,'already exists'):
                assemble(frozen,derived,review,ledger,out)

    def test_tamper_fails_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen,derived,review,ledger,private=self.create_evidence(Path(tmp))
            worksheet=review/'0028-review-worksheet.PRIVATE.csv'
            worksheet.write_text(worksheet.read_text()+'garbage')
            with self.assertRaisesRegex(ValueError,'mismatched evidence'):
                assemble(frozen,derived,review,ledger,private/'triage')
            self.assertFalse((private/'triage').exists())

    def test_differing_review_evidence_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            frozen,derived,review,ledger,private=self.create_evidence(Path(tmp))
            p=review/'0028-review-summary.json'
            j=json.loads(p.read_text())
            j['inputEvidenceSha256']['frozenSnapshot']='a'*64
            p.write_text(json.dumps(j))
            sums=review/'SHA256SUMS.txt'
            new=[]
            for l in sums.read_text().splitlines():
                _,name=l.split('  ')
                new.append(f'{sha(review/name)}  {name}')
            sums.write_text('\n'.join(new)+'\n')
            with self.assertRaisesRegex(ValueError,'different input evidence'):
                assemble(frozen,derived,review,ledger,private/'triage')

if __name__ == '__main__':
    unittest.main()
