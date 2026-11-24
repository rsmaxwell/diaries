#!/usr/bin/env python3
"""Offline contract tests; no SSH, Docker or production data."""
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

SCRIPT = Path(__file__).resolve().parents[1] / 'tools' / 'step3_0028_maintenance_handoff.py'
spec = importlib.util.spec_from_file_location('step3_0028_maintenance_handoff', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
GIT = '7aa6296' + 'b' * 33


def fixtures():
    rt = {
        'mode':'READ_ONLY_RELEASE_CONTRACT','productionApplyAuthorised':False,
        'writerIsolationVerified':False,'freshBackupVerified':False,
        'publishedPostgresHostPort':True,
        'containers':{},
        'units':{u:{'LoadState':'loaded','ActiveState':'active'} for u in
                 ('diaries-compose.service','diaries-complete-backup-publish.timer',
                  'diaries-complete-backup-publish.service')},
    }
    for name, service in mod.CONTAINERS.items():
        rt['containers'][name]={'name':name,'composeService':service,'imageId':'sha256:a',
            'image':'postgres:18-alpine' if name=='diaries-postgres' else
            ('rsmaxwell/diaries-responder:0.0.9-build-86' if name=='diaries-responder' else 'x'),
            'mounts':[{'destination':'/data/files'},{'destination':'/config/responder.json'}]
                     if name=='diaries-responder' else [],
            'portBindings':{'5432/tcp':[{'HostIp':'0.0.0.0','HostPort':'5433'}]}
                 if name=='diaries-postgres' else {}}
    candidate = {'result':'RELEASE_CANDIDATE_PREPARED_NO_PRODUCTION_PERMISSION',
                 'productionApplyAuthorised':False,'writerIsolationVerified':False,
                 'migrationJarSha256':'a'*64,'responderGitCommit':GIT,
                 'retainedDatabaseRecoveryBackupId':mod.BACKUP,
                 'retainedDatabaseRestoreVerified':True,'fullFilesRestoreVerified':False,
                 'currentResponderImage':'rsmaxwell/diaries-responder:0.0.9-build-86'}
    recovery = {'backupId':mod.BACKUP, 'databaseRestoreVerified':True,
                'restoredCounts':mod.EXPECTED_COUNTS.copy(),
                'allFilesPayloadsVerified':False,
                'productionWriterIsolationVerified':False,
                'productionApplyAuthorised':False}
    artifact = {'artifact_sha256':'a'*64,'source_commit':GIT}
    return candidate, rt, recovery, artifact


class Tests(unittest.TestCase):
    def ok(self):
        return mod.assess(*fixtures(), 69, GIT)

    def test_good_evidence_still_unapproved(self):
        out=self.ok()
        self.assertEqual(out['result'],'OPERATOR_HANDOFF_PREPARED_NOT_APPROVED')
        self.assertFalse(out['productionApplyAuthorised'])
        self.assertFalse(out['freshWriterStoppedRecoveryPointVerified'])
        self.assertEqual(out['requiredJavaMajor'],25)

    def test_production_approval_is_never_inferred(self):
        args=list(fixtures());args[0]['productionApplyAuthorised']=True
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_source_revision_must_equal_artifact(self):
        with self.assertRaises(ValueError): mod.assess(*fixtures(),69,'c'*40)

    def test_artifact_digest_must_match_release_candidate(self):
        args=list(fixtures());args[0]['migrationJarSha256']='f'*64
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_database_port_must_be_accounted_for(self):
        args=list(fixtures());args[1]['publishedPostgresHostPort']=False
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_backup_service_inventory_must_exist(self):
        args=list(fixtures()); del args[1]['units']['diaries-complete-backup-publish.timer']
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_unexpected_postgres_service_name_fails(self):
        args=list(fixtures());args[1]['containers']['diaries-postgres']['composeService']='diaries-postgres'
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_files_mount_must_exist(self):
        args=list(fixtures());args[1]['containers']['diaries-responder']['mounts']=[]
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_database_restore_counts_drift_fails(self):
        args=list(fixtures());args[2]['restoredCounts']['fragments']=2300
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_claimed_complete_files_restore_fails(self):
        args=list(fixtures());args[2]['allFilesPayloadsVerified']=True
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_wrong_latest_backup_id_fails(self):
        args=list(fixtures());args[2]['backupId']='20261123-003111Z'
        with self.assertRaises(ValueError): mod.assess(*args,69,GIT)

    def test_jar_class_and_sql_and_java25(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            jar=root/'diaries-0028-reviewed-migration-fat.jar'
            with zipfile.ZipFile(jar,'w') as z:
                z.writestr(mod.CLASS,b'\xca\xfe\xba\xbe\x00\x00\x00E' + b'bytecode')
                z.writestr(mod.SQL,b'create table journal(x int);')
            digest=hashlib.sha256(jar.read_bytes()).hexdigest()
            data={'schema':'1','feature':'0028-FEAT','status':'BUILT_NOT_DEPLOYED_NOT_APPROVED',
                  'source_commit':GIT,'artifact_sha256':digest,'artifact':jar.name}
            (root/'ARTIFACT-IDENTITY.txt').write_text(''.join('{}={}\n'.format(k,v) for k,v in data.items()))
            found,major=mod.artifact_identity(root)
            self.assertEqual(found['source_commit'],GIT)
            self.assertEqual(major,69)
            with zipfile.ZipFile(jar,'w') as z:
                z.writestr(mod.CLASS,b'\xca\xfe\xba\xbe\x00\x00\x00E' + b'bytecode')
            with self.assertRaises(ValueError): mod.artifact_identity(root)

    def test_jar_mutation_digest_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            (root/'diaries-0028-reviewed-migration-fat.jar').write_bytes(b'not a jar')
            fields=['schema=1','feature=0028-FEAT','status=BUILT_NOT_DEPLOYED_NOT_APPROVED',
                    'source_commit='+GIT,'artifact_sha256='+'e'*64,
                    'artifact=diaries-0028-reviewed-migration-fat.jar']
            (root/'ARTIFACT-IDENTITY.txt').write_text('\n'.join(fields)+'\n')
            with self.assertRaises(ValueError): mod.artifact_identity(root)

    def test_shell_does_not_mutate_production(self):
        script=(SCRIPT.parent/'prepare-0028-step3-operator-handoff.sh').read_text()
        self.assertIn('docker exec diaries-responder java -version',script)
        self.assertNotIn('docker compose stop ',script)
        self.assertNotIn('systemctl stop ',script)
        self.assertNotIn('docker compose run ',script)
        self.assertNotIn('--mode apply',script)


if __name__=='__main__':
    unittest.main(verbosity=2)
