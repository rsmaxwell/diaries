#!/usr/bin/env python3
"""Offline tests for 0028 retained recovery verification; NO SSH/Docker needed."""
import importlib.util
import hashlib
import io
from unittest import mock
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

TOOLS=pathlib.Path(__file__).resolve().parent.parent/'tools'
spec=importlib.util.spec_from_file_location('retained_tool', TOOLS/'step3_retained_restore_stream.py')
r=importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
spec2=importlib.util.spec_from_file_location('writer_tool', TOOLS/'step3_writer_channel_inventory.py')
w=importlib.util.module_from_spec(spec2)
spec2.loader.exec_module(w)
BACKUP='20261124-003112Z'


def sha(data): return hashlib.sha256(data).hexdigest()


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name)
        self.dump=b'PGDMP0123456789\n'
        (self.root/'database').mkdir()
        (self.root/'database'/'diaries.dump').write_bytes(self.dump)
        (self.root/'verification').mkdir()
        (self.root/'files').mkdir()
        self.samples=[]
        for n in range(3):
            name=f'files/sample{n}.jpg'
            data=b'IMAGE'+bytes([n])
            (self.root/name).write_bytes(data)
            self.samples.append({'path':name,'sizeBytes':len(data),'sha256':sha(data)})
        (self.root/'verification'/'inventory.json').write_text(json.dumps({'files':self.samples}))
        self.m={'schemaVersion':2,'status':'complete','logicalDataset':'production','backupId':BACKUP,
                'database':{'customDump':{'path':'database/diaries.dump','sizeBytes':len(self.dump),'sha256':sha(self.dump)}},
                'files':{'snapshot':{'inventorySha256':r.digest(self.root/'verification'/'inventory.json')}}}
        self.write_manifest()

    def write_manifest(self):
        (self.root/'dataset-manifest.json').write_text(json.dumps(self.m))
        self.manifestsha=r.digest(self.root/'dataset-manifest.json')

    def run_history(self,cmd,**kw):
        self.assertEqual(cmd[0],r.HISTORY)
        report={'backupId':BACKUP,'logicalDataset':'production',
                'occurrences':[{'snapshot':'20261124T020011Z','path':str(self.root),'manifestSha256':self.manifestsha}]}
        return subprocess.CompletedProcess(cmd,0,stdout=json.dumps(report),stderr='')

    def meta(self):
        return r.read_dump_metadata(BACKUP,runner=self.run_history)

    def test_valid_bound_retained_source(self):
        meta=self.meta()
        self.assertEqual(meta['customDumpSha256'],sha(self.dump))
        self.assertEqual(len(r.sample_files(meta)),3)


    def test_remote_stream_checks_full_digest(self):
        meta=self.meta()
        sink=io.BytesIO()
        class Output:
            buffer=sink
        with mock.patch.object(r,'read_dump_metadata',return_value=meta), \
             mock.patch.object(r.sys,'stdout',Output()):
            r.remote_stream(BACKUP,self.manifestsha,sha(self.dump),str(len(self.dump)))
        self.assertEqual(sink.getvalue(),self.dump)

    def test_remote_stream_rejects_invalid_hash_before_output(self):
        meta=self.meta()
        sink=io.BytesIO()
        class Output:
            buffer=sink
        with mock.patch.object(r,'read_dump_metadata',return_value=meta), \
             mock.patch.object(r.sys,'stdout',Output()):
            with self.assertRaises(ValueError):
                r.remote_stream(BACKUP,self.manifestsha,'0'*64,str(len(self.dump)))
        self.assertEqual(sink.getvalue(),b'')

    def test_inventory_integrity_hash_mismatch_blocks_sample(self):
        meta=self.meta()
        (self.root/'verification/inventory.json').write_text('{"files":[]}')
        with self.assertRaises(ValueError): r.sample_files(meta)

    def test_missing_dump_rejected(self):
        (self.root/'database'/'diaries.dump').unlink()
        with self.assertRaises(OSError): self.meta()

    def test_changed_dump_size_rejected(self):
        (self.root/'database'/'diaries.dump').write_bytes(b'altered')
        with self.assertRaises(ValueError): self.meta()

    def test_manifest_wrong_identity_rejected(self):
        self.m['backupId']='20261123-003111Z'
        self.write_manifest()
        with self.assertRaises(ValueError): self.meta()

    def test_manifest_unapproved_dump_type_rejected(self):
        self.m['database']['customDump']['path']='database/other.dump'
        self.write_manifest()
        with self.assertRaises(ValueError): self.meta()

    def test_sample_hash_drift_rejected(self):
        meta=self.meta()
        (self.root/'files/sample1.jpg').write_bytes(b'OTHER!')
        with self.assertRaises(ValueError): r.sample_files(meta)

    def test_sample_symlink_escape_rejected(self):
        meta=self.meta()
        (self.root/'files/sample1.jpg').unlink()
        (self.root/'files/sample1.jpg').symlink_to(self.root/'dataset-manifest.json')
        with self.assertRaises(ValueError): r.sample_files(meta)

    def test_unsafe_traversal_rejected(self):
        for item in ('../secrets','files/../a','/tmp/passwd','files//a','files\\a'):
            with self.subTest(item=item),self.assertRaises(ValueError):
                r.regular_inside(self.root,item)

    def test_good_pair_binding(self):
        meta={'backupId':BACKUP,'manifestSha256':self.manifestsha,
              'customDumpSha256':sha(self.dump),'customDumpBytes':len(self.dump),
              'sampleFilesVerified':3}
        paired={'inspectionResult':'MATCHING_RETAINED_COMPONENT_METADATA',
                'productionApplyAuthorised':False,'backupId':BACKUP,
                'manifestSha256':self.manifestsha,
                'database':{'customDump':{'sha256':sha(self.dump),'bytes':len(self.dump)}}}
        self.assertEqual(r.compare_pair(paired,meta)['backupId'],BACKUP)

    def test_mismatched_pair_blocked(self):
        meta={'backupId':BACKUP,'manifestSha256':self.manifestsha,
              'customDumpSha256':sha(self.dump),'customDumpBytes':len(self.dump),
              'sampleFilesVerified':3}
        paired={'inspectionResult':'MATCHING_RETAINED_COMPONENT_METADATA',
                'productionApplyAuthorised':False,'backupId':BACKUP,
                'manifestSha256':'0'*64,'database':{'customDump':{'sha256':sha(self.dump),'bytes':len(self.dump)}}}
        with self.assertRaises(ValueError): r.compare_pair(paired,meta)

    def test_bad_history_id_rejected(self):
        with self.assertRaises(ValueError): r.choose_occurrence('../secrets',self.run_history)

    def test_docker_run_is_network_disabled_and_one_shot(self):
        text=(TOOLS/'verify-0028-step3-retained-restore-and-writers.sh').read_text()
        self.assertIn('--network none',text)
        self.assertIn('--pull never',text)
        self.assertIn('docker container inspect "$container"',text)
        self.assertIn('docker volume inspect "$volume"',text)
        self.assertIn('PRODUCTION APPLY NOT AUTHORISED',text)
        self.assertNotIn('docker rm ',text)
        self.assertNotIn('docker volume rm ',text)

    def test_writer_uses_verified_pluto_container_names(self):
        expected = ('diaries-postgres', 'diaries-mosquitto', 'diaries-responder',
                    'diaries-client', 'diaries-web')
        self.assertEqual(w.CONTAINERS, expected)
        self.assertEqual(w.POSTGRES_CONTAINER, 'diaries-postgres')

    def test_writer_sql_queries_actual_postgres_container(self):
        with mock.patch.object(w, 'run', return_value='postgres|healthy\n') as runner:
            result = w.sql('SELECT 1')
        self.assertEqual(result, ['postgres|healthy'])
        # Access mock calls using the tuple protocol for older Cygwin Python.
        # call_args.args is unavailable in some supported interpreter versions.
        argv = runner.call_args[0][0]
        self.assertEqual(argv[:3], ['docker', 'exec', 'diaries-postgres'])
        self.assertEqual(argv[-1], 'SELECT 1')

    def test_writer_collect_inspects_all_real_names_and_correct_db_ports(self):
        visited = []

        def fake_run(args, seconds=30):
            if args[:2] == ['docker', 'inspect']:
                name = args[2]
                visited.append(name)
                doc = {'Name':'/'+name, 'Config':{'Image':'postgres:18-alpine'},
                       'Image':'sha256:abc','State':{'Status':'running'},
                       'HostConfig':{'PortBindings':{'5432/tcp':[{'HostIp':'127.0.0.1','HostPort':'5433'}]} if name == 'diaries-postgres' else {},
                                     'NetworkMode':'bridge','RestartPolicy':{'Name':'unless-stopped'}}}
                return json.dumps([doc])
            if args[0] == 'systemctl':
                return 'LoadState=loaded\nActiveState=active\n'
            raise AssertionError('Unexpected external command: '+str(args))

        with mock.patch.object(w,'run',side_effect=fake_run), \
             mock.patch.object(w,'sql',side_effect=[['postgres|psql|local|active|1'],['postgres|true|true']]):
            report = w.collect()
        self.assertEqual(tuple(visited), w.CONTAINERS)
        self.assertTrue(report['databasePortPublished'])
        self.assertFalse(report['writerIsolationVerified'])
        self.assertFalse(report['productionApplyAuthorised'])
        self.assertEqual(report['containers']['diaries-postgres']['publishedPorts']['5432/tcp'][0]['HostPort'],'5433')

    def test_writer_parser_omits_secrets(self):
        doc=[{'Name':'/diaries-postgres', 'Config':{'Image':'postgres:18-alpine','Env':['PASSWORD=private']},
             'Image':'sha256:abc', 'State':{'Status':'running'},
             'HostConfig':{'NetworkMode':'bridge','PortBindings':{'5432/tcp':[{'HostPort':'5433'}]},
                           'RestartPolicy':{'Name':'unless-stopped'}}}]
        info=w.inspect_from_doc(doc)
        self.assertEqual(info['publishedPorts']['5432/tcp'][0]['HostPort'],'5433')
        self.assertNotIn('private',json.dumps(info))


if __name__=='__main__': unittest.main(verbosity=2)
