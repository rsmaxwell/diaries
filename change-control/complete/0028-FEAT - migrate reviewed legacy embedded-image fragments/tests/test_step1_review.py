"""Synthetic tests for the offline 0028 Step 1 review assembler."""
import csv
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'tools'))
from step1_make_review import assemble, sha


def csv_write(path, fields, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fields, lineterminator='\n')
        writer.writeheader()
        writer.writerows(rows)


def json_write(path, obj):
    path.write_text(json.dumps(obj)+'\n', encoding='utf-8')


def manifest(directory):
    (directory/'SHA256SUMS.txt').write_text(''.join(
        f'{sha(p)}  {p.name}\n' for p in sorted(directory.iterdir())
        if p.is_file() and p.name != 'SHA256SUMS.txt'), encoding='utf-8')


def fixture(root):
    frozen = root/'frozen'; derived = root/'derived'; files = derived/'0024-dry-run'
    frozen.mkdir(); files.mkdir(parents=True)
    fragment_1 = {'fragment_id': 1, 'version': 4, 'type': None, 'image_id': None,
                  'page_id': 15, 'marquees': [{'id': 6, 'page_id': 15}],
                  'year': 1942, 'month': 1, 'day': 3, 'sequence': '1.0000',
                  'text': '<p>X<img src="/files/photos/a.jpg"></p>'}
    fragment_2 = {'fragment_id': 2, 'version': 2, 'type': None, 'image_id': None,
                  'page_id': None, 'marquees': [], 'year': 1942, 'month': 1,
                  'day': 4, 'sequence': '2.0000',
                  'text': '<img src="img-b.jpg" onerror="alert(1)">'}
    image = {'image_id': 7, 'relative_path': 'diary/photos/a.jpg', 'checksum': 'a'*64}
    csv_write(frozen/'current-schema-snapshot.PRIVATE.csv', ['kind','payload'], [
        {'kind':'fragment','payload':json.dumps(fragment_1)},
        {'kind':'fragment','payload':json.dumps(fragment_2)},
        {'kind':'image','payload':json.dumps(image)},
        {'kind':'identity','payload':json.dumps({'database':'testdb'})},
    ])
    def digest(s): return hashlib.sha256(s.encode('utf-8')).hexdigest()
    csv_write(frozen/'0028-dispositions.UNREVIEWED.csv',
        ['fragment_id','embedded_image_count','disposition','original_html_sha256','page_id','marquee_id','expected_fragment_version'], [
        {'fragment_id':'1','embedded_image_count':'1','disposition':'','original_html_sha256':digest(fragment_1['text']),'page_id':'15','marquee_id':'6','expected_fragment_version':'4'},
        {'fragment_id':'2','embedded_image_count':'1','disposition':'','original_html_sha256':digest(fragment_2['text']),'page_id':'','marquee_id':'','expected_fragment_version':'2'},
    ])
    src_a = '/files/photos/a.jpg'; src_b = 'img-b.jpg'
    csv_write(frozen/'0028-image-decisions.UNREVIEWED.csv',
        ['fragment_id','embedded_image_ordinal','original_src','original_src_sha256','occurrence_action'], [
        {'fragment_id':'1','embedded_image_ordinal':'1','original_src':src_a,'original_src_sha256':digest(src_a),'occurrence_action':''},
        {'fragment_id':'2','embedded_image_ordinal':'1','original_src':src_b,'original_src_sha256':digest(src_b),'occurrence_action':''},
    ])
    csv_write(frozen/'0028-structural-exceptions.csv', ['fragment_id','issue'], [
        {'fragment_id':'1','issue':'UNEXPECTED_FRAGMENT_TYPE'},
        {'fragment_id':'2','issue':'UNEXPECTED_FRAGMENT_TYPE'},
        {'fragment_id':'2','issue':'MISSING_PAGE_ID'},
    ])
    json_write(frozen/'0028-summary.json', {'candidateCoverage':'UNREVIEWED - no mutation authorised',
               'counts':{'unreviewed_legacy_candidates':2,'total_legacy_occurrences':2}})
    manifest(frozen)
    csv_write(derived/'0028-0024-candidates.PRIVATE.csv', ['database_fragment_id','legacy_image_reference'], [
        {'database_fragment_id':'1','legacy_image_reference':src_a},
        {'database_fragment_id':'2','legacy_image_reference':src_b},
    ])
    json_write(derived/'0028-page-ownership-summary.json', {
        'sourceInventorySnapshotSha256':sha(frozen/'current-schema-snapshot.PRIVATE.csv'),
        'sourceOccurrenceSha256':sha(frozen/'0028-image-decisions.UNREVIEWED.csv'),
        'sourceDispositionSha256':sha(frozen/'0028-dispositions.UNREVIEWED.csv'),
        'sourceInventorySummarySha256':sha(frozen/'0028-summary.json'),
        'candidateRows':2, 'occurrenceRows':2,
    })
    csv_write(files/'0024-candidate-cross-reference.csv',
        ['fragmentId','candidateIndex','sourceSha256','imageId','relativePath','status','matchMethod'], [
        {'fragmentId':'1','candidateIndex':'1','sourceSha256':digest(src_a),'imageId':'7',
         'relativePath':'diary/photos/a.jpg','status':'MATCHED_ONE_IMAGE','matchMethod':'UNIQUE_LOCAL_SUFFIX'},
        {'fragmentId':'2','candidateIndex':'1','sourceSha256':digest(src_b),'imageId':'',
         'relativePath':'img-b.jpg','status':'AMBIGUOUS_PATH','matchMethod':'UNIQUE_LOCAL_SUFFIX'},
    ])
    csv_write(files/'0024-file-inventory.csv',
        ['relativePath','imageId','status','sha256'], [
        {'relativePath':'diary/photos/a.jpg','imageId':'7','status':'CATALOGUED_MATCH','sha256':'a'*64},
    ])
    json_write(files/'0024-summary.json', {'outcome':'DRY_RUN_COMPLETE','mode':'dry-run','insertedRows':0})
    json_write(files/'0024-create-plan.json', {})
    json_write(files/'0024-post-apply-verification.json', {'verified':True,'candidateCrossReferenceComplete':True})
    csv_write(files/'0024-conflicts.csv', ['relativePath','imageId','status','sha256'], [])
    manifest(files); manifest(derived)
    return frozen, derived


class ReviewTests(unittest.TestCase):
    def test_review_outputs_are_private_inert_and_unapproved(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            output=root/'new'
            result=assemble(frozen,derived,output)
            self.assertEqual(result['counts']['candidateFragments'],2)
            self.assertEqual(result['counts']['occurrences'],2)
            with (output/'0028-review-worksheet.PRIVATE.csv').open(newline='') as f:
                items=list(csv.DictReader(f))
            self.assertEqual(len(items),2)
            self.assertEqual(items[0]['catalogue_cross_check'],'MATCHED_SNAPSHOT_AND_FILE')
            self.assertIn('SUFFIX_MAPPING_REVIEW_REQUIRED',items[0]['review_blockers'])
            self.assertIn('PAGE_OWNERSHIP_UNRESOLVED',items[1]['review_blockers'])
            self.assertEqual(items[0]['review_disposition'],'')
            self.assertEqual(items[1]['review_occurrence_action'],'')
            html=(output/'0028-review-dossier.PRIVATE.html').read_text()
            self.assertIn('onerror=&quot;alert(1)&quot;',html)
            self.assertIn('default-src \'none\'',html)
            self.assertNotIn('<img src=',html)
            self.assertEqual(len(verified_for_test(output)),3)
    def test_tampering_rejected_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            p=derived/'0024-dry-run'/'0024-summary.json'
            p.write_text('{"outcome":"COMMITTED"}')
            with self.assertRaises(ValueError):
                assemble(frozen,derived,root/'new')
            self.assertFalse((root/'new').exists())
    def test_mismatched_0024_source_hash_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            p=derived/'0024-dry-run'/'0024-candidate-cross-reference.csv'
            content=p.read_text().replace('MATCHED_ONE_IMAGE','MATCHED_ONE_IMAGE')
            # Replace first valid source hash while preserving syntactic CSV.
            actual=hashlib.sha256('/files/photos/a.jpg'.encode()).hexdigest()
            p.write_text(content.replace(actual,'0'*64))
            manifest(p.parent)
            with self.assertRaisesRegex(ValueError, 'source SHA mismatch'):
                assemble(frozen,derived,root/'new')
    def test_missing_occurrence_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            p=derived/'0024-dry-run'/'0024-candidate-cross-reference.csv'
            all_lines=p.read_text().splitlines()
            p.write_text('\n'.join(all_lines[:2])+'\n')
            manifest(p.parent)
            with self.assertRaisesRegex(ValueError, 'coverage mismatch'):
                assemble(frozen,derived,root/'new')
    def test_mismatched_image_file_sha_fails_closed_in_worksheet(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            p=derived/'0024-dry-run'/'0024-file-inventory.csv'
            p.write_text(p.read_text().replace('a'*64,'b'*64))
            manifest(p.parent)
            result=assemble(frozen,derived,root/'new')
            with (root/'new'/'0028-review-worksheet.PRIVATE.csv').open(newline='') as f:
                first=list(csv.DictReader(f))[0]
            self.assertIn('CATALOGUE_OR_FILE_MISMATCH',first['review_blockers'])
            self.assertEqual(first['catalogue_cross_check'],'MISMATCH')
    def test_existing_output_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp); frozen,derived=fixture(root)
            output=root/'new';output.mkdir()
            with self.assertRaisesRegex(ValueError, 'Output already exists'):
                assemble(frozen,derived,output)


def verified_for_test(dir):
    from step1_make_review import verified
    return verified(dir, {'0028-review-worksheet.PRIVATE.csv', '0028-review-dossier.PRIVATE.html','0028-review-summary.json'})

if __name__ == '__main__':
    unittest.main()
