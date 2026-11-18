"""Offline tests of the Step 1 0024 compatibility input generator."""
import csv
import hashlib
import importlib.util
import io
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

TOOL = Path(__file__).resolve().parents[1] / "tools" / "step1_prepare_0024.py"
spec = importlib.util.spec_from_file_location("step1_prepare_0024", TOOL)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def write_csv(path, fields, rows):
    with path.open('w', encoding='utf8', newline='') as stream:
        w = csv.DictWriter(stream, fieldnames=fields, lineterminator='\n')
        w.writeheader()
        w.writerows(rows)


class PrepareTests(unittest.TestCase):
    def setup_inventory(self, root, src='/files/sample.jpg', page=None, marquee_page=84):
        directory = root / 'inventory'
        directory.mkdir()
        write_csv(directory/'0028-dispositions.UNREVIEWED.csv',
                  ['fragment_id', 'disposition', 'embedded_image_count'],
                  [{'fragment_id': '10', 'disposition': '', 'embedded_image_count': '1'}])
        write_csv(directory/'0028-image-decisions.UNREVIEWED.csv',
                  ['fragment_id', 'embedded_image_ordinal', 'original_src', 'original_src_sha256', 'occurrence_action'],
                  [{'fragment_id': '10', 'embedded_image_ordinal': '1', 'original_src': src,
                    'original_src_sha256': hashlib.sha256(src.encode()).hexdigest(), 'occurrence_action': ''}])
        snap = [{'kind': 'identity','payload':json.dumps({'database':'test'})},
                {'kind': 'fragment', 'payload': json.dumps({'fragment_id':10, 'page_id':page,
                      'marquees':[{'id':5, 'page_id':marquee_page}]})}]
        write_csv(directory/'current-schema-snapshot.PRIVATE.csv', ['kind','payload'],snap)
        (directory/'0028-summary.json').write_text(json.dumps({
            'candidateCoverage':'UNREVIEWED - no mutation authorised',
            'counts':{'unreviewed_legacy_candidates':1,'total_legacy_occurrences':1}
        }))
        (directory/'SHA256SUMS.txt').write_text(''.join(
            f'{mod.sha_file(p)}  {p.name}\n' for p in directory.iterdir()))
        return directory

    def test_legacy_input_shape_and_indirect_page(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            inv=self.setup_inventory(root)
            out=root/'derived'
            report=mod.prepare(inv,out)
            self.assertEqual(report['pageOwnership']['missing_page_one_marquee_with_page'],1)
            with (out/'0028-0024-candidates.PRIVATE.csv').open(newline='') as stream:
                data=list(csv.DictReader(stream))
            self.assertEqual(data,[{'database_fragment_id':'10','legacy_image_reference':'/files/sample.jpg'}])
            self.assertTrue((out/'SHA256SUMS.txt').exists())
            mod.checked_inputs(inv)

    def test_direct_page_populated(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            inv=self.setup_inventory(root,page=85,marquee_page=85)
            result=mod.prepare(inv,root/'derived')
            self.assertEqual(result['pageOwnership']['direct_page_id_populated'],1)
            self.assertEqual(result['pageOwnership']['direct_page_and_marquee_page_both_populated'],1)

    def test_stale_input_hash_blocks(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            inv=self.setup_inventory(root)
            (inv/'0028-summary.json').write_text('tampered')
            with self.assertRaisesRegex(ValueError,'SHA256 mismatch'):
                mod.prepare(inv,root/'derived')
            self.assertFalse((root/'derived').exists())

    def test_separator_ambiguity_blocks(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            inv=self.setup_inventory(root,src='a | b')
            with self.assertRaisesRegex(ValueError,'separator'):
                mod.prepare(inv,root/'derived')
            self.assertFalse((root/'derived').exists())

    def test_duplicate_occurrence_ordinal_blocks(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            inv=self.setup_inventory(root)
            occurrence=inv/'0028-image-decisions.UNREVIEWED.csv'
            with occurrence.open('a',encoding='utf8') as stream:
                stream.write('10,1,/files/sample.jpg,'+hashlib.sha256(b'/files/sample.jpg').hexdigest()+',\n')
            files=sorted(p for p in inv.iterdir() if p.name!='SHA256SUMS.txt')
            (inv/'SHA256SUMS.txt').write_text(''.join(
                f'{mod.sha_file(p)}  {p.name}\n' for p in files))
            with self.assertRaisesRegex(ValueError, 'ordinals|counts'):
                mod.prepare(inv,root/'derived')


if __name__ == '__main__':
    unittest.main()
