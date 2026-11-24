#!/usr/bin/env python3
"""0028 read-only production writer access survey. All output is private evidence.

The remote branch reads Docker metadata, systemd properties and SELECT-only
pg_stat_activity. It never prints Docker environment variables or SQL query text.
It does not claim that writers are isolated.
"""
import datetime
import json
import os
from pathlib import Path
import re
import subprocess
import sys

CONTAINERS = ('diaries-responder', 'diaries-postgres', 'diaries-mosquitto', 'diaries-client', 'diaries-web')
UNITS = ('diaries-compose.service', 'diaries-complete-backup-publish.service', 'diaries-complete-backup-publish.timer')
MARKER = '0028-WRITER-ACCESS-READONLY-V1'
SQL = """SELECT COALESCE(json_agg(json_build_object(
    'pid', pid, 'database', datname, 'user', usename,
    'application', application_name, 'client_address', client_addr::text,
    'state', state, 'transaction_start', xact_start::text,
    'backend_start', backend_start::text
) ORDER BY pid), '[]'::json)
FROM pg_stat_activity
WHERE backend_type = 'client backend' AND pid <> pg_backend_pid();"""


def call(argv, timeout=30):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
        return {'ok': r.returncode == 0, 'out': r.stdout, 'error': r.stderr.strip()[:600], 'code': r.returncode}
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {'ok': False, 'out': '', 'error': str(exc)[:600], 'code': -1}


def concise_inspection(info):
    if not isinstance(info, dict):
        raise ValueError('invalid Docker inspect record')
    config = info.get('Config') or {}
    host = info.get('HostConfig') or {}
    network = info.get('NetworkSettings') or {}
    ports = network.get('Ports') or {}
    return {
        'name': (info.get('Name') or '').lstrip('/'),
        'running': bool((info.get('State') or {}).get('Running')),
        'restart_policy': ((host.get('RestartPolicy') or {}).get('Name') or ''),
        'ports': {str(p): [
            {'host_ip': str(x.get('HostIp','')), 'host_port': str(x.get('HostPort',''))}
            for x in (bindings or [])] for p, bindings in ports.items()},
        'mounts': [{'destination': m.get('Destination'), 'rw': m.get('RW'), 'type': m.get('Type')}
                   for m in (info.get('Mounts') or [])],
        'compose_service': (config.get('Labels') or {}).get('com.docker.compose.service'),
        'compose_project': (config.get('Labels') or {}).get('com.docker.compose.project'),
    }


def parse_units(text):
    # systemctl show emits sectionless key=value; separate one invocation per unit.
    return dict(line.split('=',1) for line in text.splitlines()
                if '=' in line and line.split('=',1)[0] in
                {'LoadState','ActiveState','SubState','UnitFileState','Result','FragmentPath'})


def assess(data):
    failures=[]
    containers=data.get('containers') or {}
    for name in CONTAINERS:
        c=containers.get(name)
        if not isinstance(c,dict) or c.get('name') != name:
            failures.append('Container inspection unavailable: '+name)
    units=data.get('systemd') or {}
    for unit in UNITS:
        if not units.get(unit) or not units[unit].get('LoadState'):
            failures.append('Systemd unit inspection unavailable: '+unit)
    sessions=data.get('database_sessions')
    if not isinstance(sessions,list):
        failures.append('PostgreSQL session query failed')
    db=containers.get('diaries-postgres') or {}
    published=(db.get('ports') or {}).get('5432/tcp') or []
    # A published socket might include IPv6, wildcard, loopback or unusual bindings.
    responder=containers.get('diaries-responder') or {}
    files_rw=any(m.get('destination') == '/data/files' and m.get('rw') is True
                 for m in responder.get('mounts') or [])
    return {'complete': not failures, 'errors': failures, 'database_host_bindings': published,
            'database_published': bool(published), 'observed_database_sessions':
            len(sessions) if isinstance(sessions,list) else None,
            'responder_files_rw': files_rw,
            'backup_service_running': (units.get('diaries-complete-backup-publish.service') or {}).get('ActiveState') == 'active',
            'production_writer_isolation_verified': False,
            'fresh_immutable_rollback_point_verified': False,
            'production_migration_authorised': False}


def remote():
    data={'schema':1,'marker':MARKER,'collected_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
          'containers':{},'systemd':{},'database_sessions':None,'errors':[]}
    for name in CONTAINERS:
        r=call(['docker','inspect',name],timeout=25)
        if not r['ok']:
            data['errors'].append('docker inspect '+name+': '+r['error'])
            continue
        try:
            payload=json.loads(r['out'])
            data['containers'][name]=concise_inspection(payload[0])
        except (ValueError,IndexError,KeyError) as exc:
            data['errors'].append('docker inspect '+name+' parse: '+str(exc))
    for name in UNITS:
        r=call(['systemctl','show',name,'--property=LoadState,ActiveState,SubState,UnitFileState,Result,FragmentPath','--no-pager'])
        if not r['ok']:
            data['errors'].append('systemctl show '+name+': '+r['error'])
        data['systemd'][name]=parse_units(r['out'])
    # Expand POSTGRES_USER/POSTGRES_DB only inside the DB container. Never inspect
    # or print environment values, database passwords, SQL queries or live configs.
    r=call(['docker','exec','diaries-postgres','sh','-c',
            'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"',
            'sh', SQL],timeout=30)
    if not r['ok']:
        data['errors'].append('read-only PostgreSQL activity query: '+r['error'])
    else:
        try:
            sessions=json.loads(r['out'].strip())
            if not isinstance(sessions,list):
                raise ValueError('expected JSON array')
            data['database_sessions']=sessions
        except ValueError as exc:
            data['errors'].append('PostgreSQL session JSON invalid: '+str(exc))
    data['assessment']=assess(data)
    print(json.dumps(data,indent=2,sort_keys=True))
    return 0 if data['assessment']['complete'] and not data['errors'] else 2


def local():
    # Never use /tmp as permanent evidence. Feature-local private evidence only.
    feature=Path(__file__).resolve().parent.parent
    parent=feature / 'evidence' / 'Step 3' / 'private'
    parent.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    evidence=parent/(stamp+'-writer-access-window')
    evidence.mkdir()
    source=Path(__file__).read_bytes()
    try:
        r=subprocess.run(['ssh','-o','BatchMode=yes','pluto','python3','-','--remote'],
            input=source,capture_output=True,timeout=100,check=False)
    except (OSError,subprocess.TimeoutExpired) as exc:
        (evidence/'ERROR.txt').write_text('SSH probe failed: '+str(exc)+'\n',encoding='utf-8')
        print('FAIL: SSH probe failed; see private evidence',file=sys.stderr)
        return 2
    if r.stderr:
        (evidence/'REMOTE-ERROR.txt').write_bytes(r.stderr[:8192])
    try:
        data=json.loads(r.stdout.decode('utf-8'))
        if data.get('marker') != MARKER:
            raise ValueError('unexpected probe identity')
    except (UnicodeDecodeError,ValueError) as exc:
        (evidence/'ERROR.txt').write_text('Remote JSON invalid: '+str(exc)+'\n',encoding='utf-8')
        print('FAIL: invalid remote result; private error receipt saved')
        return 2
    (evidence/'WRITER-ACCESS.json').write_text(json.dumps(data,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    a=data['assessment']
    report=['# 0028 — Live production writer access (read-only)',
      '', 'Collected: '+data.get('collected_utc','unknown'),
      '', 'Survey complete: **'+('YES' if a['complete'] else 'NO')+'**',
      '', 'Production writer isolation: **NOT VERIFIED**',
      '', 'Production migration: **NOT AUTHORISED**',
      '', 'Current database sessions (excluding survey session): **'+str(a['observed_database_sessions'])+'**',
      'PostgreSQL host port published: **'+str(a['database_published'])+'**',
      'Responder /data/files RW mount: **'+str(a['responder_files_rw'])+'**',
      'Backup publisher active now: **'+str(a['backup_service_running'])+'**',
      '', '## PostgreSQL published host bindings',
      '', '```json', json.dumps(a['database_host_bindings'],indent=2), '```',
      '', '## Container restart policies', '']
    for name in CONTAINERS:
        c=data.get('containers',{}).get(name) or {}
        report.append('- '+name+': running='+str(c.get('running'))+'; restart='+str(c.get('restart_policy')))
    report.extend(['', '## systemd supervision', ''])
    for unit in UNITS:
        u=data.get('systemd',{}).get(unit) or {}
        report.append('- '+unit+': active='+str(u.get('ActiveState'))+'; enabled='+str(u.get('UnitFileState')))
    report.extend(['', '## Database connection inventory', '',
      'Exact users, source addresses and app names appear only in WRITER-ACCESS.json.',
      'Do not equate zero observed connections with blocked future connections.',
      '', '## Open controls (not implemented by this tool)', '',
      '1. Identify and positively exclude every application, direct SQL and Files-root writer.',
      '2. Coordinate active backup service and timer before changing responder state.',
      '3. Choose a reversible direct-DB ingress control and verify denied connection attempts.',
      '4. Establish fresh matched immutable DB+Files rollback snapshots on mars and backup.',
      '5. Run new production dry-run, obtain formal approvals, then consider apply.',
      '', 'Errors: '+repr(data.get('errors',[])+a.get('errors',[])), ''])
    (evidence/'READOUT.md').write_text('\n'.join(report),encoding='utf-8')
    print('Private 0028 writer-access evidence:', evidence)
    print('Survey complete:',a['complete'])
    print('PostgreSQL host port published:',a['database_published'])
    print('Observed DB clients:',a['observed_database_sessions'])
    print('Responder Files mount RW:',a['responder_files_rw'])
    print('Backup service active:',a['backup_service_running'])
    print('PRODUCTION WRITER ISOLATION: NOT VERIFIED; APPLY NOT AUTHORISED')
    if r.returncode != 0 or not a['complete'] or data.get('errors'):
        print('FAIL: writer-access survey incomplete; inspect private report')
        return 2
    print('PASS: read-only writer-access survey collected; controls still OPEN')
    return 0

if __name__ == '__main__':
    sys.exit(remote() if '--remote' in sys.argv else local())
