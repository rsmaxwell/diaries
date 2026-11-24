#!/usr/bin/env python3
"""0028: read-only maintenance window contract. No production operations authorised.

Called on Windows/Cygwin. Executes a single read-only Python probe over SSH to
pluto. The output contains no credentials or production config file contents.
Detailed network/mount IDs stay inside the feature-private evidence directory.
"""
from __future__ import annotations
import datetime
import hashlib
import json
from pathlib import Path
import subprocess
import sys

MARKER='0028-CONTROLLED-WINDOW-READONLY-V1'
ROOT='/home/richard/projects/diaries'
CONTAINERS={'diaries-postgres':'diaries-db', 'diaries-responder':'diaries-responder',
            'diaries-mosquitto':'diaries-mqtt'}
UNITS=('diaries-compose.service','diaries-complete-backup-publish.timer',
       'diaries-complete-backup-publish.service')
SOURCE_FIXED_SHA256='5a9c2f33c008e53b90281e6335abd7cbeb47526f5a69214f33231a4b26ab09eb'
SQL="""SELECT json_build_object(
 'hba_path', current_setting('hba_file'),
 'rules', (SELECT json_agg(json_build_object('line',line_number,
             'type',type,'address',address,'auth',auth_method,'error',error)
             ORDER BY line_number) FROM pg_hba_file_rules),
 'clients', (SELECT count(*) FROM pg_stat_activity
             WHERE backend_type='client backend' AND pid<>pg_backend_pid())
)::text;"""


def call(argv, timeout=25):
    try:
        p=subprocess.run(argv,capture_output=True,text=True,timeout=timeout,check=False)
        return p.returncode,p.stdout,p.stderr[:300]
    except (OSError,subprocess.TimeoutExpired) as e:
        return 99,'',str(e)[:300]


def reduced_container(info):
    config=info.get('Config') or {}
    host=info.get('HostConfig') or {}
    network=info.get('NetworkSettings') or {}
    return {'name': (info.get('Name') or '').lstrip('/'),
        'running': bool((info.get('State') or {}).get('Running')),
        'image':config.get('Image'),
        'image_id':info.get('Image'),
        'service':(config.get('Labels') or {}).get('com.docker.compose.service'),
        'project':(config.get('Labels') or {}).get('com.docker.compose.project'),
        'restart':((host.get('RestartPolicy') or {}).get('Name')),
        'ports':(network.get('Ports') or {}),
        'networks':sorted((network.get('Networks') or {}).keys()),
        'mounts':[{'destination':m.get('Destination'),'type':m.get('Type'),
                   'name':m.get('Name') if m.get('Type')=='volume' else None,
                   'rw':m.get('RW')}
                  for m in (info.get('Mounts') or [])]}


def assess(d):
    errors=list(d.get('errors') or [])
    for name,service in CONTAINERS.items():
        c=d.get('containers',{}).get(name) or {}
        if c.get('name')!=name or c.get('service')!=service or not c.get('running'):
            errors.append('Unexpected container/service state: '+name)
    pg=(d.get('containers') or {}).get('diaries-postgres') or {}
    bindings=(pg.get('ports') or {}).get('5432/tcp') or []
    if not any(b.get('HostPort')=='5433' for b in bindings):
        errors.append('Expected published PostgreSQL port 5433 missing')
    resp=(d.get('containers') or {}).get('diaries-responder') or {}
    if not any(m.get('destination')=='/data/files' and m.get('rw') is True
               for m in resp.get('mounts') or []):
        errors.append('Responder Files mount is not the expected RW volume')
    for name in UNITS:
        if not (d.get('units') or {}).get(name,{}).get('LoadState')=='loaded':
            errors.append('Missing systemd contract: '+name)
    rules=(d.get('database') or {}).get('rules')
    if not isinstance(rules,list):
        errors.append('PostgreSQL pg_hba_file_rules not available')
    else:
        errors.extend('PostgreSQL HBA parse error at line '+str(x.get('line'))
                      for x in rules if x.get('error'))
        tcp=[x for x in rules if x.get('type')=='host']
        if not any(x.get('address')=='all' and x.get('auth')=='scram-sha-256' for x in tcp):
            errors.append('General SCRAM TCP rule not found')
        if any(x.get('auth')=='trust' and x.get('address') not in {'127.0.0.1','::1'} for x in tcp):
            errors.append('Non-loopback TCP trust rule detected')
    files=d.get('files') or {}
    for name in ['backup-dataset.sh','fixed-dataset-capture.py','compose.yaml']:
        if not (files.get(name) or {}).get('exists'):
            errors.append('Installed production file unavailable: '+name)
    if d.get('backup_capture_source_sha256')!=SOURCE_FIXED_SHA256:
        errors.append('Installed fixed-capture code differs from uploaded source bundle; review before execution')
    return {'complete':not errors,'errors':errors,
        'production_changes_performed':False,'writer_isolation_verified':False,
        'immutable_rollback_point_verified':False,'dry_run_performed':False,
        'production_apply_authorised':False}


def remote():
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    d={'marker':MARKER,'collected_at_utc':now,'containers':{},'units':{},
       'files':{},'database':{},'errors':[]}
    for name in CONTAINERS:
        rc,out,err=call(['docker','inspect',name])
        if rc:
            d['errors'].append('Container inspect unavailable: '+name+': '+err)
            continue
        try:
            d['containers'][name]=reduced_container(json.loads(out)[0])
        except (ValueError,IndexError,KeyError) as e:
            d['errors'].append('Malformed container inspection: '+name+': '+str(e))
    for name in UNITS:
        rc,out,err=call(['systemctl','show',name,'--no-pager',
            '-p','LoadState','-p','ActiveState','-p','SubState',
            '-p','UnitFileState','-p','NextElapseUSecRealtime'])
        if rc: d['errors'].append('Systemd unavailable: '+name+': '+err)
        d['units'][name]=dict(line.split('=',1) for line in out.splitlines()
                              if '=' in line)
    files={'backup-dataset.sh':Path(ROOT)/'scripts'/'backup-dataset.sh',
           'fixed-dataset-capture.py':Path(ROOT)/'scripts'/'fixed-dataset-capture.py',
           'compose.yaml':Path(ROOT)/'compose.yaml'}
    for name,p in files.items():
        item={'exists':p.is_file() and not p.is_symlink()}
        if item['exists']: item['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()
        d['files'][name]=item
    d['backup_capture_source_sha256']=d['files']['fixed-dataset-capture.py'].get('sha256')
    rc,out,err=call(['docker','exec','diaries-postgres','sh','-c',
          'exec psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "$1"',
          'sh',SQL])
    if rc: d['errors'].append('SQL read-only inspection failed: '+err)
    else:
        try:
            d['database']=json.loads(out.strip())
            if not isinstance(d['database'],dict): raise ValueError('expected object')
        except ValueError as e: d['errors'].append('SQL JSON parse failure: '+str(e))
    d['assessment']=assess(d)
    print(json.dumps(d,sort_keys=True,indent=2))
    return 0 if d['assessment']['complete'] else 2


def local():
    feature=Path(__file__).resolve().parent.parent
    base=feature/'evidence'/'Step 3'/'private'
    base.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    receipt=base/(stamp+'-controlled-window-contract')
    receipt.mkdir(mode=0o700)
    source=Path(__file__).read_bytes()
    try:
        p=subprocess.run(['ssh','-o','BatchMode=yes','pluto','python3','-','--remote'],
              input=source,capture_output=True,timeout=110,check=False)
    except (OSError,subprocess.TimeoutExpired) as e:
        (receipt/'ERROR.txt').write_text('SSH failure: '+str(e)+'\n',encoding='utf-8')
        print('FAIL: SSH probe did not complete; see private receipt',file=sys.stderr)
        return 2
    if p.stderr:
        (receipt/'REMOTE-ERROR.txt').write_bytes(p.stderr[:8192])
    try:
        d=json.loads(p.stdout.decode('utf-8'))
        if d.get('marker')!=MARKER: raise ValueError('invalid result marker')
        a=assess(d)
        d['assessment']=a
    except (ValueError,UnicodeDecodeError) as e:
        (receipt/'ERROR.txt').write_text('Result invalid: '+str(e)+'\n',encoding='utf-8')
        print('FAIL: invalid remote result; see private receipt')
        return 2
    (receipt/'CONTRACT.json').write_text(json.dumps(d,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    r=d.get('containers') or {}
    db=d.get('database') or {}
    timer=(d.get('units') or {}).get('diaries-complete-backup-publish.timer') or {}
    report='\n'.join([
       '# 0028 — controlled-window execution contract (read-only)','',
       'Captured: '+d.get('collected_at_utc','?'),
       'Result: '+('PASS' if a['complete'] else 'INCOMPLETE'),'',
       'Production modifications: NONE',
       'Production migration: NOT AUTHORISED','',
       'Database host port 5433 observed: '+str(bool((r.get('diaries-postgres') or {}).get('ports',{}).get('5432/tcp'))),
       'Non-survey database clients: '+str(db.get('clients')),
       'Responder stop state before maintenance: '+str((r.get('diaries-responder') or {}).get('running')),
       'Backup timer active: '+str(timer.get('ActiveState')),
       'Next backup schedule: '+str(timer.get('NextElapseUSecRealtime')),
       'HBA rule path and detailed mount IDs are private in CONTRACT.json.',
       'Installed backup implementation SHA matches source: '+str(d.get('backup_capture_source_sha256')==SOURCE_FIXED_SHA256),
       '', 'Blocking checks: '+json.dumps(a['errors']), '',
       'OPEN: authorised maintenance window; service writer isolation; DB ingress and Files writer exclusion;',
       'matching new immutable recovery snapshot on mars+backup; final production dry-run; explicit apply approval.',
       ''])
    (receipt/'READOUT.md').write_text(report,encoding='utf-8')
    print('Private 0028 controlled-window evidence:',receipt)
    print('Contract:', 'PASS' if a['complete'] else 'INCOMPLETE')
    print('Published PostgreSQL port 5433:',bool((r.get('diaries-postgres') or {}).get('ports',{}).get('5432/tcp')))
    print('Observed database clients:',db.get('clients'))
    print('Backup timer:',timer.get('ActiveState'))
    print('Deployment fixed-capture source matches supplied bundle:',
          d.get('backup_capture_source_sha256')==SOURCE_FIXED_SHA256)
    if not a['complete'] or p.returncode:
        print('BLOCKED: live contract mismatch; inspect private evidence')
        return 2
    print('PASS: read-only pre-maintenance contract; writer isolation NOT started')
    print('PRODUCTION APPLY NOT AUTHORISED')
    return 0

if __name__=='__main__':
    sys.exit(remote() if '--remote' in sys.argv else local())
