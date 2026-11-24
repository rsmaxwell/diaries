#!/usr/bin/env python3
"""Offline release preparation unit tests. No SSH, Docker, Gradle or writes outside tmp."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

R=Path(__file__).resolve().parent.parent

def import_tool(name):
    path=R/'tools'/name
    spec=importlib.util.spec_from_file_location(name.replace('.py',''),str(path))
    mod=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

c=import_tool('0028_step3_release_candidate.py')
r=import_tool('0028_step3_runtime_inventory.py')

def fixtures():
    sha='a'*64
    artifact={'source_commit':'b'*40,'artifact_sha256':sha,'status':'BUILT_NOT_DEPLOYED_NOT_APPROVED'}
    containers={}
    for name,service in [('diaries-postgres','diaries-db'),('diaries-mosquitto','diaries-mqtt'),
                         ('diaries-responder','diaries-responder'),('diaries-client','diaries-client'),('diaries-web','diaries-web')]:
        containers[name]={'name':name,'imageId':'sha256:'+sha,'image':'postgres:18-alpine' if name=='diaries-postgres' else 'rsmaxwell/x:1',
                          'composeService':service}
    runtime={'mode':'READ_ONLY_RELEASE_CONTRACT','writerIsolationVerified':False,
             'productionApplyAuthorised':False,'containers':containers,'publishedPostgresHostPort':True}
    recovery={'backupId':'20261124-003112Z','databaseRestoreVerified':True,
              'restoredCounts':{'fragments':2331,'marquees':2270,'images':85,'pages':683},
              'productionApplyAuthorised':False,'productionWriterIsolationVerified':False}
    return artifact,runtime,recovery,sha

class Tests(unittest.TestCase):
    def test_valid_candidate_is_still_unapproved(self):
        a,b,x,sha=fixtures()
        result=c.assessment(a,b,x,sha)
        self.assertFalse(result['productionApplyAuthorised'])
        self.assertFalse(result['writerIsolationVerified'])
        self.assertTrue(result['currentPostgresPortPublished'])
        self.assertEqual(result['result'],'RELEASE_CANDIDATE_PREPARED_NO_PRODUCTION_PERMISSION')
        self.assertEqual(result['migrationCliLifecycle'], 'DISPOSABLE_ONESHOT_RETAIN_UNTIL_ACCEPTED_ROLLBACK_WINDOW_CLOSED')
        self.assertFalse(result['permanentResponderDependency'])
    def test_jar_hash_mismatch_blocks(self):
        a,b,x,sha=fixtures()
        with self.assertRaisesRegex(ValueError,'JAR bytes differ'):
            c.assessment(a,b,x,'c'*64)
    def test_source_revision_invalid_blocks(self):
        a,b,x,sha=fixtures();a['source_commit']='dirty'
        with self.assertRaisesRegex(ValueError,'source revision'):
            c.assessment(a,b,x,sha)
    def test_approval_flag_in_runtime_blocks(self):
        a,b,x,sha=fixtures();b['productionApplyAuthorised']=True
        with self.assertRaisesRegex(ValueError,'invalid claim'):
            c.assessment(a,b,x,sha)
    def test_unrecognised_container_blocks(self):
        a,b,x,sha=fixtures();b['containers']['diaries-db']=b['containers'].pop('diaries-postgres')
        with self.assertRaisesRegex(ValueError,'identities differ'):
            c.assessment(a,b,x,sha)
    def test_sql_compose_service_name_blocks(self):
        a,b,x,sha=fixtures();b['containers']['diaries-postgres']['composeService']='diaries-postgres'
        with self.assertRaisesRegex(ValueError,'Compose identity'):
            c.assessment(a,b,x,sha)
    def test_mqtt_compose_name_blocks(self):
        a,b,x,sha=fixtures();b['containers']['diaries-mosquitto']['composeService']='diaries-mosquitto'
        with self.assertRaisesRegex(ValueError,'Compose identity'):
            c.assessment(a,b,x,sha)
    def test_pg_version_drift_blocks(self):
        a,b,x,sha=fixtures();b['containers']['diaries-postgres']['image']='postgres:17-alpine'
        with self.assertRaisesRegex(ValueError,'version drift'):
            c.assessment(a,b,x,sha)
    def test_restore_counts_drift_blocks(self):
        a,b,x,sha=fixtures();x['restoredCounts']['images']=84
        with self.assertRaisesRegex(ValueError,'recovery receipt'):
            c.assessment(a,b,x,sha)
    def test_recovery_permission_drift_blocks(self):
        a,b,x,sha=fixtures();x['productionApplyAuthorised']=True
        with self.assertRaisesRegex(ValueError,'production permission'):
            c.assessment(a,b,x,sha)
    def test_parse_kv_duplicate_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/'id.txt';p.write_text('x=a\nx=b\n')
            with self.assertRaisesRegex(ValueError,'invalid identity'):
                c.parse_kv(p)
    def test_runtime_extract_filters_credentials_and_sources(self):
        obj=[{'Name':'/diaries-responder','Config':{'Image':'img:1',
              'Labels':{'com.docker.compose.service':'diaries-responder'}},
              'Image':'sha256:'+'a'*64,'State':{'Status':'running'},
              'Mounts':[{'Destination':'/data/files','Type':'volume','RW':True,'Source':'/very/private/secret'}],
              'HostConfig':{'PortBindings':{},'RestartPolicy':{'Name':'unless-stopped'}},
              'NetworkSettings':{'Networks':{'infrastructure_shared':{}}}}]
        result=r.extract(obj)
        self.assertEqual(result['name'],'diaries-responder')
        self.assertNotIn('/very/private/secret',json.dumps(result))
        self.assertNotIn('Source',json.dumps(result))
        self.assertEqual(result['mounts'][0]['destination'],'/data/files')
    def test_runtime_requires_single_record(self):
        with self.assertRaises(ValueError):r.extract([])
    def test_build_and_live_runner_have_no_mutating_ssh(self):
        text=(R/'tools/inspect-0028-step3-release-runtime.sh').read_text()
        self.assertNotIn('ssh pluto sudo',text)
        self.assertNotIn('systemctl stop',text)
        self.assertNotIn('docker run',text)
        self.assertIn('ssh pluto',text)

if __name__=='__main__':unittest.main(verbosity=2)
