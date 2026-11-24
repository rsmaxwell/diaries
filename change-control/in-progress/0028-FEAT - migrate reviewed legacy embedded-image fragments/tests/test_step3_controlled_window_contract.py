#!/usr/bin/env python3
"""Pure regression tests: no network, Docker, PostgreSQL or production actions."""
import importlib.util
import pathlib
import unittest

FEATURE=pathlib.Path(__file__).resolve().parent.parent
TOOL=FEATURE/'tools'/'inspect-0028-step3-controlled-window.py'
spec=importlib.util.spec_from_file_location('controlled_window',TOOL)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def sample():
    def c(name,service):
        return {'name':name,'service':service,'running':True,'ports':{},
                'mounts':[],'restart':'unless-stopped'}
    d={'containers':{n:c(n,s) for n,s in mod.CONTAINERS.items()},
       'units':{n:{'LoadState':'loaded'} for n in mod.UNITS},
       'files':{n:{'exists':True} for n in ['backup-dataset.sh','fixed-dataset-capture.py','compose.yaml']},
       'backup_capture_source_sha256':mod.SOURCE_FIXED_SHA256,
       'database':{'rules':[{'type':'local','auth':'trust','address':None,'error':None},
           {'type':'host','auth':'trust','address':'127.0.0.1','error':None},
           {'type':'host','auth':'trust','address':'::1','error':None},
           {'type':'host','auth':'scram-sha-256','address':'all','error':None}],
           'clients':1},'errors':[]}
    d['containers']['diaries-postgres']['ports']={'5432/tcp':[{'HostIp':'0.0.0.0','HostPort':'5433'}]}
    d['containers']['diaries-responder']['mounts']=[{'destination':'/data/files','rw':True}]
    return d

class Tests(unittest.TestCase):
    def test_valid_read_only_contract_never_grants_approval(self):
        a=mod.assess(sample())
        self.assertTrue(a['complete'])
        self.assertFalse(a['production_apply_authorised'])
        self.assertFalse(a['writer_isolation_verified'])
        self.assertFalse(a['immutable_rollback_point_verified'])
    def test_unexpected_hba_trust_is_rejected(self):
        d=sample();d['database']['rules'].append({'type':'host','auth':'trust','address':'all','error':None})
        self.assertFalse(mod.assess(d)['complete'])
    def test_missing_general_scram_rejected(self):
        d=sample();d['database']['rules'][-1]['auth']='reject'
        self.assertFalse(mod.assess(d)['complete'])
    def test_hba_parse_error_rejected(self):
        d=sample();d['database']['rules'][-1]['error']='bad config'
        self.assertFalse(mod.assess(d)['complete'])
    def test_different_fixed_capture_source_rejected(self):
        d=sample();d['backup_capture_source_sha256']='0'*64
        self.assertFalse(mod.assess(d)['complete'])
    def test_postgres_port_change_rejected(self):
        d=sample();d['containers']['diaries-postgres']['ports']['5432/tcp'][0]['HostPort']='15432'
        self.assertFalse(mod.assess(d)['complete'])
    def test_missing_backup_timer_rejected(self):
        d=sample();del d['units']['diaries-complete-backup-publish.timer']
        self.assertFalse(mod.assess(d)['complete'])
    def test_wrong_service_name_rejected(self):
        d=sample();d['containers']['diaries-postgres']['service']='some-other-db'
        self.assertFalse(mod.assess(d)['complete'])
    def test_rw_files_mount_required(self):
        d=sample();d['containers']['diaries-responder']['mounts'][0]['rw']=False
        self.assertFalse(mod.assess(d)['complete'])
    def test_missing_backup_script_rejected(self):
        d=sample();d['files']['backup-dataset.sh']['exists']=False
        self.assertFalse(mod.assess(d)['complete'])
    def test_reduced_docker_data_omits_env(self):
        obj={'Name':'/diaries-postgres','Config':{'Image':'postgres:18-alpine',
            'Env':['POSTGRES_PASSWORD=SHOULD_NOT_APPEAR'],
            'Labels':{'com.docker.compose.service':'diaries-db'}},
            'HostConfig':{'RestartPolicy':{'Name':'unless-stopped'}},
            'State':{'Running':True},'NetworkSettings':{'Ports':{},'Networks':{}}}
        self.assertNotIn('SHOULD_NOT_APPEAR',str(mod.reduced_container(obj)))
    def test_source_never_performs_mutations(self):
        t=TOOL.read_text()
        for forbidden in ('docker stop','systemctl stop','docker compose stop','pg_reload_conf',
                         'ALTER SYSTEM','CREATE TABLE','--permit-production-apply'):
            self.assertNotIn(forbidden,t)

if __name__=='__main__': unittest.main(verbosity=2)
