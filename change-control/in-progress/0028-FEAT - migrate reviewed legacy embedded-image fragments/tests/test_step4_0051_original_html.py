"""Private, inert source-display tests (synthetic only; no production writes)."""
import copy
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent/'tools'))
from step4_0051_compatibility_review import (
    SCHEMA, image_tag_ranges, portal, sha, source_previews,
)


class OriginalHtmlTests(unittest.TestCase):
    ORIGINAL = ('<h2>Heading</h2><p>Before &amp; after</p>\n'
                '<!-- fake <img src="comment.png"> -->\n'
                '<figure><img class="a" title="1 > 0"\n'
                'src="images/first.jpg"><figcaption>Caption one</figcaption></figure>'
                '<p>Second</p><img src="images/second.png" onerror="window.PWNED=1">'
                '<script>window.PWNED=2; const x="</script>";</script>')

    def make(self, root, original=None, ordinal='2'):
        original = self.ORIGINAL if original is None else original
        folder = root/'private/20261118T093606Z'
        folder.mkdir(parents=True, exist_ok=True)
        snapshot = folder/'current-schema-snapshot.PRIVATE.csv'
        payload = {'fragment_id':9,'version':3,'page_id':None,'text':original,'marquees':[]}
        with snapshot.open('w', encoding='utf-8', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=['kind','payload'])
            writer.writeheader();writer.writerow({'kind':'fragment','payload':json.dumps(payload)})
        (folder/'SHA256SUMS.txt').write_text(sha(snapshot.read_bytes())+'  '+snapshot.name+'\n')
        row = {'fragment_id':'9','embedded_image_ordinal':ordinal,
               'source_html_sha256':sha(original),
               'source_img_sha256':sha('images/second.png' if ordinal=='2' else 'images/first.jpg'),
               'expected_fragment_version':'3','expected_page_id':'',
               'source_link_state':'NONE','source_link_url_PRIVATE':'',
               'source_marquee':{'status':'ABSENT','id':'','page_id':'','geometry_sha256':''},
               'legacy_review':{},'disposition':'','occurrence_action':'','reviewed_at':'',
               'reviewed_by':'','review_note':''}
        doc={'schema':SCHEMA, 'fingerprints':{'inventory_sha256':sha(snapshot.read_bytes())},
             'review_status':'UNREVIEWED_V2','productionApplyAllowed':False,'decisions':[row]}
        return doc,snapshot

    def test_image_highlight_exact_and_comment_ignored(self):
        ranges = image_tag_ranges(self.ORIGINAL)
        self.assertEqual(2,len(ranges))
        self.assertTrue(self.ORIGINAL[slice(*ranges[0])].startswith('<img class='))
        self.assertEqual('<img src="images/second.png" onerror="window.PWNED=1">',
                         self.ORIGINAL[slice(*ranges[1])])

    def test_full_html_readable_and_script_does_not_escape_json(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc,snapshot=self.make(Path(tmp))
            previews=source_previews(doc,snapshot)
            self.assertEqual(self.ORIGINAL,previews[0]['original_html_PRIVATE'])
            self.assertIn('[Image 2: images/second.png]',previews[0]['readable_text_PRIVATE'])
            self.assertNotIn('window.PWNED=2',previews[0]['readable_text_PRIVATE'])
            html=portal(doc,previews)
            self.assertIn('Original Fragment HTML (PRIVATE, read-only)',html)
            self.assertIn('source.appendChild(document.createTextNode(',html)
            self.assertIn('mark.textContent=html.slice(start,end)',html)
            self.assertNotIn('<img src="images/second.png"',html)
            self.assertNotIn('<script>window.PWNED=2',html)
            self.assertIn('\\u003cimg',html)
            # The same review schema and existing decisions are unchanged.
            self.assertEqual('',doc['decisions'][0]['disposition'])
            self.assertNotIn('original_html_PRIVATE',doc['decisions'][0])

    def test_mutated_snapshot_and_bad_fingerprint_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc,snapshot=self.make(Path(tmp))
            bad=copy.deepcopy(doc)
            bad['fingerprints']['inventory_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'fingerprint mismatch'):
                source_previews(bad,snapshot)
            snapshot.write_text(snapshot.read_text()+'\n')
            with self.assertRaisesRegex(ValueError,'checksum mismatch'):
                source_previews(doc,snapshot)

    def test_changed_html_and_image_src_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            doc,snapshot=self.make(Path(tmp))
            doc['decisions'][0]['source_html_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'original HTML SHA256 mismatch'):
                source_previews(doc,snapshot)
            doc['decisions'][0]['source_html_sha256']=sha(self.ORIGINAL)
            doc['decisions'][0]['source_img_sha256']='0'*64
            with self.assertRaisesRegex(ValueError,'IMG src SHA256 mismatch'):
                source_previews(doc,snapshot)


if __name__=='__main__': unittest.main()
