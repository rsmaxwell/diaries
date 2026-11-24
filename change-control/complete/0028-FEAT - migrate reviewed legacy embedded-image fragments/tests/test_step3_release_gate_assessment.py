#!/usr/bin/env python3
"""Local, synthetic regression tests. No SSH, Docker or PostgreSQL."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

source = Path(__file__).resolve().parent.parent / 'tools' / 'step3_release_gate_assessment.py'
spec = importlib.util.spec_from_file_location('release0028', str(source))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def writer():
    containers = {}
    for name in module.EXPECTED:
        containers[name] = dict(name=name,
                                image='postgres:18-alpine' if name == 'diaries-postgres' else 'local/diaries:1',
                                imageId='sha256:' + 'a'*64,
                                state='running', restartPolicy='unless-stopped',
                                publishedPorts={'5432/tcp': [{'HostIp': '0.0.0.0', 'HostPort': '5433'}]} if name == 'diaries-postgres' else {})
    return {'inspection': 'PRODUCTION_WRITER_CHANNELS_READ_ONLY',
            'writerIsolationVerified': False, 'productionApplyAuthorised': False,
            'containers': containers, 'databasePortPublished': True,
            'systemdUnits': {'diaries-compose.service': {'ActiveState': 'active'},
                             'diaries-complete-backup-publish.timer': {'ActiveState': 'active'},
                             'diaries-complete-backup-publish.service': {'ActiveState': 'inactive'}},
            'databaseClientGroups': ['app|jdbc|172.18.0.3|idle|2', 'postgres|psql|local|active|1'],
            'databaseLoginRoles': []}


def recovery():
    return {'feature': '0028-FEAT', 'recoveryClass': 'RETAINED_DB_RESTORE_VERIFIED',
            'backupId': module.BACKUP_ID, 'databaseRestoreVerified': True,
            'productionApplyAuthorised': False,
            'restoredCounts': dict(module.EXPECTED_COUNTS),
            'filesPayloadSampleHashesVerified': 3, 'allFilesPayloadsVerified': False,
            'productionWriterIsolationVerified': False,
            'freshWriterStoppedRecoveryPointVerified': False,
            'customDumpSha256': 'c'*64}


class Tests(unittest.TestCase):
    def call(self, w=None, r=None):
        return module.assess(w if w is not None else writer(),
                             r if r is not None else recovery(),
                             {'writer':'0'*64, 'recovery':'1'*64})

    def test_valid_evidence_remains_unapproved(self):
        result = self.call()
        self.assertFalse(result['productionApplyAuthorised'])
        self.assertFalse(result['productionWriterIsolationVerified'])
        self.assertEqual(result['observedPostgresClientCount'],3)
        self.assertTrue(result['databaseHostPortExposedAtSurvey'])
        self.assertEqual(len(result['remainingHardGates']), 10)

    def test_missing_container_rejected(self):
        w=writer(); del w['containers']['diaries-postgres']
        with self.assertRaises(ValueError): self.call(w=w)

    def test_wrong_name_rejected(self):
        w=writer(); w['containers']['diaries-postgres']['name']='diaries-db'
        with self.assertRaises(ValueError): self.call(w=w)

    def test_wrong_postgres_version_rejected(self):
        w=writer(); w['containers']['diaries-postgres']['image']='postgres:17'
        with self.assertRaises(ValueError): self.call(w=w)

    def test_port_flag_mismatch_rejected(self):
        w=writer(); w['databasePortPublished']=False
        with self.assertRaises(ValueError): self.call(w=w)

    def test_no_host_port_allowed_but_not_authorised(self):
        w=writer(); w['containers']['diaries-postgres']['publishedPorts']={};w['databasePortPublished']=False
        self.assertFalse(self.call(w=w)['productionApplyAuthorised'])

    def test_missing_compose_unit_rejected(self):
        w=writer(); del w['systemdUnits']['diaries-compose.service']
        with self.assertRaises(ValueError): self.call(w=w)

    def test_missing_backup_timer_rejected(self):
        w=writer(); del w['systemdUnits']['diaries-complete-backup-publish.timer']
        with self.assertRaises(ValueError): self.call(w=w)

    def test_bad_client_group_rejected(self):
        w=writer(); w['databaseClientGroups']=['postgres|bad']
        with self.assertRaises(ValueError): self.call(w=w)

    def test_no_client_sessions_still_not_authorised(self):
        w=writer(); w['databaseClientGroups']=[]
        self.assertFalse(self.call(w=w)['productionWriterIsolationVerified'])

    def test_claimed_isolation_in_survey_rejected(self):
        w=writer(); w['writerIsolationVerified']=True
        with self.assertRaises(ValueError): self.call(w=w)

    def test_wrong_backup_id_rejected(self):
        r=recovery();r['backupId']='20261123-003111Z'
        with self.assertRaises(ValueError): self.call(r=r)

    def test_wrong_restore_counts_rejected(self):
        r=recovery(); r['restoredCounts']['fragments']=1
        with self.assertRaises(ValueError): self.call(r=r)

    def test_incomplete_recovery_rejected(self):
        r=recovery();r['databaseRestoreVerified']=False
        with self.assertRaises(ValueError): self.call(r=r)

    def test_full_files_claim_not_assumed(self):
        result=self.call();self.assertFalse(result['completeFilesRestoreVerified'])

    def test_malformed_dump_digest_rejected(self):
        r=recovery();r['customDumpSha256']='abc'
        with self.assertRaises(ValueError): self.call(r=r)

    def test_prod_apply_claimed_by_receipt_rejected(self):
        r=recovery();r['productionApplyAuthorised']=True
        with self.assertRaises(ValueError): self.call(r=r)

    def test_missing_evidence_is_error(self):
        with self.assertRaises(ValueError):module.read_object('/does-not-exist-here')

    def test_cli_writes_private_result_without_executing_services(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp); (path/'w.json').write_text(json.dumps(writer()));(path/'r.json').write_text(json.dumps(recovery()))
            with patch.object(module, 'assess', wraps=module.assess) as spy:
                self.assertEqual(module.main(['--writer',str(path/'w.json'),'--recovery',str(path/'r.json'),
                                              '--output',str(path/'result.json')]),0)
                self.assertEqual(spy.call_count,1)
                result=json.loads((path/'result.json').read_text())
                self.assertFalse(result['productionApplyAuthorised'])
                self.assertEqual(module.main(['--writer',str(path/'w.json'),'--recovery',str(path/'r.json'),
                                              '--output',str(path/'result.json')]),2)


if __name__=='__main__': unittest.main(verbosity=2)
