#!/usr/bin/env python3
"""Read-only live pluto production writer exposure inventory. Prints no secrets."""
import json
import subprocess
import sys

# Verified on pluto 2026-11-24. Keep SQL and port lookup tied to this exact name.
POSTGRES_CONTAINER = 'diaries-postgres'
CONTAINERS = (POSTGRES_CONTAINER, 'diaries-mosquitto', 'diaries-responder', 'diaries-client', 'diaries-web')


def run(argv, seconds=30):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=seconds)
    if p.returncode:
        raise RuntimeError('command failed: {} / {}'.format(' '.join(argv[:2]), p.stderr[-300:]))
    return p.stdout


def sql(query):
    script = 'exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -A -t -F "|" -c "$1"'
    return run(['docker', 'exec', POSTGRES_CONTAINER, 'sh', '-c', script, 'sh', query], 60).strip().splitlines()


def inspect_from_doc(doc):
    if not isinstance(doc, list) or len(doc) != 1:
        raise ValueError('expected one Docker inspect record')
    item = doc[0]
    host = item.get('HostConfig') or {}
    state = item.get('State') or {}
    ports = host.get('PortBindings') or {}
    result = {'name': item['Name'].lstrip('/'), 'image': item['Config']['Image'],
              'imageId': item['Image'], 'state': state.get('Status'),
              'restartPolicy': (host.get('RestartPolicy') or {}).get('Name'),
              'networkMode': host.get('NetworkMode'), 'publishedPorts': ports}
    return result


def collect():
    containers = {}
    for name in CONTAINERS:
        raw = json.loads(run(['docker', 'inspect', name], 30))
        containers[name] = inspect_from_doc(raw)
    q = '''SELECT coalesce(usename,''),coalesce(application_name,''),
                   coalesce(client_addr::text,'local'),coalesce(state,'unknown'),count(*)::text
            FROM pg_stat_activity WHERE datname=current_database()
            GROUP BY usename,application_name,client_addr,state ORDER BY 1,2,3,4'''
    active = sql(q)
    roles = sql("SELECT rolname,rolsuper::text,rolcanlogin::text FROM pg_roles WHERE rolcanlogin ORDER BY rolname")
    units = {}
    for unit in ('diaries-compose.service','diaries-complete-backup-publish.timer',
                 'diaries-complete-backup-publish.service'):
        output = run(['systemctl', 'show', unit, '--no-pager',
                      '--property=LoadState,ActiveState,SubState,UnitFileState,NextElapseUSecRealtime,Result'], 30)
        units[unit] = dict(line.split('=',1) for line in output.splitlines() if '=' in line)
    dbports = containers[POSTGRES_CONTAINER]['publishedPorts']
    notes = ['Writer isolation has NOT been performed',
             'Stop the responder without Compose down (PostgreSQL must remain available)',
             'Control reconnecting/direct PostgreSQL clients, including published DB host port',
             'Coordinate any backup timer that might restart the responder',
             'Block Editor MQTT RPC ingress and wait for active sessions to drain',
             'Restore ingress only after migration, postflight and retained replay pass']
    return {'schema':1, 'feature':'0028-FEAT', 'inspection':'PRODUCTION_WRITER_CHANNELS_READ_ONLY',
            'containers':containers,'databaseClientGroups':active,'databaseLoginRoles':roles,
            'systemdUnits':units, 'databasePortPublished':bool(dbports),
            'isolationRequirements':notes, 'writerIsolationVerified':False,
            'productionApplyAuthorised':False}


def main():
    try:
        report = collect()
        print(json.dumps(report, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, subprocess.SubprocessError, RuntimeError, KeyError, json.JSONDecodeError) as e:
        print('FAIL: production writer inventory incomplete: '+str(e),file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
