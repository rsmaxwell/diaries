"""Offline contract regression for the disposable 0028 MQTT replay verifier."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

S=Path(__file__).resolve().parents[1] / 'tools' / '0028-replay-verify.py'
spec=importlib.util.spec_from_file_location('replay_check',S)
v=importlib.util.module_from_spec(spec)
spec.loader.exec_module(v)

class ReplayContract(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.manifest=self.root/'manifest';self.manifest.mkdir()
        self.output=self.root/'out';self.output.mkdir()
        self._write_manifest()

    def _write_manifest(self):
        d=[];i=[];x=[]
        for fid in [*range(1,72),1564]:
            convert=fid!=1564
            d.append(dict(fragment_id=fid,disposition='CONVERT_TO_IMAGE' if convert else 'DEFER'))
            i.append(dict(fragment_id=fid,embedded_image_ordinal=1,
                resolved_image_id=fid if convert else '',
                resolved_relative_path=f'images/file-{fid}.png' if convert else '',
                image_text=f'caption-{fid}',occurrence_action='REPLACE' if convert else 'DEFER'))
            x.append(dict(fragment_id=fid,embedded_image_ordinal=1,approved_page_id=999,
                image_link_url_PRIVATE='https://example.org/' if fid==1 else '',
                marquee_handling='PRESERVE' if 2<=fid<=23 else 'NOT_APPLICABLE',
                source_marquee_id=10000+fid if 2<=fid<=23 else ''))
        for name,records in [('0028-dispositions.csv',d),('0028-image-decisions.csv',i),
            ('0028-v2-preservation-decisions.PRIVATE.csv',x)]:
            with (self.manifest/name).open('w',newline='',encoding='utf8') as stream:
                writer=csv.DictWriter(stream,fieldnames=records[0].keys())
                writer.writeheader();writer.writerows(records)

    def _make_retained(self):
        expected=json.loads((self.output/'EXPECTED.PRIVATE.json').read_text())
        payload=[]
        for e in expected:
            entry={'id':e['fragment_id'],'type':'IMAGE','imageId':e['image_id'],
                   'pageId':e['page_id'],'text':e['text'],
                   'imageLinkUrl':e['link'],'marqueeId':e['marquee_id']}
            payload.append(f'diaries/fragments/{e["fragment_id"]}|||{json.dumps(entry)}\n')
        path=self.root/'retained.txt';path.write_text(''.join(payload),encoding='utf8')
        return path

    def test_generate_isolated_config_and_71_expected(self):
        v.generate(self.manifest,self.output)
        e=json.loads((self.output/'EXPECTED.PRIVATE.json').read_text())
        r=json.loads((self.output/'responder.ISOLATED.PRIVATE.json').read_text())
        w=json.loads((self.output/'reader.ISOLATED.PRIVATE.json').read_text())
        self.assertEqual(len(e),71)
        self.assertEqual(e[0]['link'],'https://example.org/')
        self.assertEqual(e[1]['marquee_id'],10002)
        self.assertEqual(len(json.loads((self.output/'EXPECTED-MARQUEES.PRIVATE.json').read_text())),22)
        self.assertFalse(r['normaliseOnStartup'])
        self.assertEqual(r['db']['host'],'diaries-0028-rehearsal-db')
        self.assertEqual(w['mqtt']['host'],'diaries-0028-replay-broker')
        self.assertIn('allow_anonymous true',(self.output/'mosquitto.ISOLATED.conf').read_text())

    def test_retained_71_payloads_pass(self):
        v.generate(self.manifest,self.output)
        v.validate_retained(self.output/'EXPECTED.PRIVATE.json',self._make_retained())

    def test_missing_marquee_fails(self):
        v.generate(self.manifest,self.output)
        p=self._make_retained()
        p.write_text(p.read_text().replace('"marqueeId": 10002','"marqueeId": null'))
        with self.assertRaisesRegex(ValueError,'Marquee association'):v.validate_retained(self.output/'EXPECTED.PRIVATE.json',p)

    def test_new_unreviewed_marquee_fails(self):
        v.generate(self.manifest,self.output)
        p=self._make_retained()
        p.write_text(p.read_text().replace('"marqueeId": null','"marqueeId": 23456',1))
        with self.assertRaisesRegex(ValueError,'Marquee association'):v.validate_retained(self.output/'EXPECTED.PRIVATE.json',p)

    def test_changed_image_or_page_or_link_fails(self):
        v.generate(self.manifest,self.output)
        for search,replace in [('"imageId": 1','"imageId": 1234'),
                              ('"pageId": 999','"pageId": 123'),
                              ('https://example.org/','https://changed.example/')]:
            p=self._make_retained();p.write_text(p.read_text().replace(search,replace,1))
            with self.assertRaises(ValueError):v.validate_retained(self.output/'EXPECTED.PRIVATE.json',p)

    def _make_marquees(self):
        expected=json.loads((self.output/'EXPECTED-MARQUEES.PRIVATE.json').read_text())
        lines=[]
        for m in expected:
            p={'id':m['marquee_id'],'fragmentId':m['fragment_id'],
               'pageId':m['page_id'],
               'rectangle':{'x':-10.0,'y':200.5,'width':0.0,'height':75.25}}
            lines.append(f'diaries/marquees/{m["marquee_id"]}|||{json.dumps(p)}\n')
        path=self.root/'marquees.txt';path.write_text(''.join(lines),encoding='utf-8')
        return path

    def test_all_marquee_topics_allow_changed_positions(self):
        v.generate(self.manifest,self.output)
        v.validate_marquees(self.output/'EXPECTED-MARQUEES.PRIVATE.json',self._make_marquees())

    def test_marquee_missing_or_reassigned_fails(self):
        v.generate(self.manifest,self.output)
        path=self._make_marquees()
        with path.open('r+',encoding='utf-8') as stream:
            text=stream.read().replace('"fragmentId": 2','"fragmentId": 999',1)
            stream.seek(0);stream.write(text);stream.truncate()
        with self.assertRaisesRegex(ValueError,'reassignment'):
            v.validate_marquees(self.output/'EXPECTED-MARQUEES.PRIVATE.json',path)
        path=self._make_marquees();path.write_text(''.join(path.read_text().splitlines(True)[:-1]))
        with self.assertRaisesRegex(ValueError,'Missing retained'):
            v.validate_marquees(self.output/'EXPECTED-MARQUEES.PRIVATE.json',path)

    def test_missing_topic_fails(self):
        v.generate(self.manifest,self.output)
        p=self._make_retained();p.write_text(''.join(p.read_text().splitlines(True)[:-1]))
        with self.assertRaisesRegex(ValueError,'Missing MQTT'):v.validate_retained(self.output/'EXPECTED.PRIVATE.json',p)

    def test_no_overwrite_of_prepared_evidence(self):
        v.generate(self.manifest,self.output)
        with self.assertRaisesRegex(ValueError,'non-empty'):v.generate(self.manifest,self.output)

    def test_unreviewed_defer_missing_fails(self):
        rows=v.load_rows(self.manifest/'0028-dispositions.csv')
        rows[-1]['disposition']='CONVERT_TO_IMAGE'
        with (self.manifest/'0028-dispositions.csv').open('w',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=rows[0].keys());writer.writeheader();writer.writerows(rows)
        with self.assertRaisesRegex(ValueError,'71 conversions'):v.load_manifest(self.manifest)

if __name__=='__main__':unittest.main()
