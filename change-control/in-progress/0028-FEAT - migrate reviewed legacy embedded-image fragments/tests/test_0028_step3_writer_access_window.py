#!/usr/bin/env python3
"""Offline boundaries and source-only regression checks for 0028 read-only probe."""
from pathlib import Path
import importlib.util
import unittest
p=Path(__file__).resolve().parent.parent/'tools'/'inspect-0028-step3-writer-access-window.py'
spec=importlib.util.spec_from_file_location('writer_access_0028',p)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

def fixture():
    containers={}
    for n in m.CONTAINERS:
        containers[n]={'name':n,'running':True,'restart_policy':'unless-stopped','ports':{},'mounts':[]}
    containers['diaries-postgres']['ports']={'5432/tcp':[{'host_ip':'0.0.0.0','host_port':'5433'}]}
    containers['diaries-responder']['mounts']=[{'destination':'/data/files','rw':True,'type':'volume'}]
    units={n:{'LoadState':'loaded','ActiveState':'inactive','UnitFileState':'enabled'} for n in m.UNITS}
    return {'containers':containers,'systemd':units,'database_sessions':[{'pid':21,'client_address':'10.0.0.3'}]}

class Tests(unittest.TestCase):
    def test_valid_survey_not_writer_isolation(self):
        d=m.assess(fixture())
        self.assertTrue(d['complete'])
        self.assertFalse(d['production_writer_isolation_verified'])
        self.assertFalse(d['production_migration_authorised'])
    def test_zero_sessions_is_not_authorisation(self):
        f=fixture(); f['database_sessions']=[]
        self.assertTrue(m.assess(f)['complete'])
        self.assertFalse(m.assess(f)['production_writer_isolation_verified'])
    def test_missing_postgres_is_incomplete(self):
        f=fixture(); f['containers'].pop('diaries-postgres')
        self.assertFalse(m.assess(f)['complete'])
    def test_missing_timer_is_incomplete(self):
        f=fixture(); f['systemd'].pop('diaries-complete-backup-publish.timer')
        self.assertFalse(m.assess(f)['complete'])
    def test_failed_session_query_is_incomplete(self):
        f=fixture(); f['database_sessions']=None
        self.assertFalse(m.assess(f)['complete'])
    def test_reduced_docker_record_does_not_expose_environment(self):
        info={'Name':'/diaries-postgres','State':{'Running':True},
              'Config':{'Env':['POSTGRES_PASSWORD=SECRET'],'Labels':{}},
              'HostConfig':{'RestartPolicy':{'Name':'unless-stopped'}},
              'NetworkSettings':{'Ports':{'5432/tcp':[{'HostIp':'0.0.0.0','HostPort':'5433'}]}},
              'Mounts':[{'Source':'/PRIVATE','Destination':'/data/files','RW':True,'Type':'volume'}]}
        reduced=m.concise_inspection(info)
        self.assertNotIn('SECRET',str(reduced))
        self.assertNotIn('PRIVATE',str(reduced))
    def test_docker_port_binding_retained(self):
        f=fixture()
        self.assertEqual(m.assess(f)['database_host_bindings'][0]['host_port'],'5433')
    def test_systemd_fields_allowlist(self):
        self.assertEqual(m.parse_units('LoadState=loaded\nSecret=NEVER\nActiveState=inactive\n'),
                         {'LoadState':'loaded','ActiveState':'inactive'})
    def test_script_does_not_run_mutating_operations(self):
        source=p.read_text(encoding='utf-8')
        self.assertNotIn('docker stop',source)
        self.assertNotIn('systemctl stop',source)
        self.assertNotIn('docker compose down',source)
        self.assertNotIn('pg_terminate_backend',source)
        self.assertNotIn('rsync --delete',source)
        self.assertNotIn('ALTER ROLE',source)
        self.assertNotIn('sudo ',source)
    def test_select_only_query(self):
        self.assertEqual(m.SQL.lstrip()[:6],'SELECT')
        self.assertIn('pg_stat_activity',m.SQL)
        self.assertNotIn('query,',m.SQL)
    def test_no_environment_dump(self):
        source=p.read_text(encoding='utf-8')
        self.assertNotIn("docker inspect --format '{{json .Config.Env}}'",source)
    def test_risk_flags_do_not_depend_on_session_count(self):
        f=fixture(); f['database_sessions']=[]
        d=m.assess(f)
        self.assertTrue(d['database_published'])
        self.assertTrue(d['responder_files_rw'])

if __name__=='__main__':
    unittest.main(verbosity=2)
