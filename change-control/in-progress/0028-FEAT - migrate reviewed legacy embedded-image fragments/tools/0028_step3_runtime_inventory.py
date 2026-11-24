#!/usr/bin/env python3
"""Read-only pluto runtime/maintenance contract; run only via SSH stdin. No secrets.
Does not run backup tools or change services. Tested against production names.
"""
import json
import subprocess
import sys

NAMES = ('diaries-postgres','diaries-mosquitto','diaries-responder','diaries-client','diaries-web')
UNITS = ('diaries-compose.service','diaries-complete-backup-publish.timer','diaries-complete-backup-publish.service')

def execute(command):
    p=subprocess.run(command, capture_output=True, text=True, timeout=40, check=False)
    if p.returncode:
        raise RuntimeError('{} failed with exit {}'.format(' '.join(command[:2]),p.returncode))
    return p.stdout

def extract(d):
    if not isinstance(d,list) or len(d)!=1: raise ValueError('inspect expects one item')
    a=d[0]; c=a.get('Config') or {}; h=a.get('HostConfig') or {}
    lbl=c.get('Labels') or {}
    mounts=a.get('Mounts') or []
    # Only destination, readonly and type; do NOT expose NAS credentials or source paths.
    return {
        'name':str(a.get('Name','')).lstrip('/'),
        'image':c.get('Image'), 'imageId':a.get('Image'),
        'state':(a.get('State') or {}).get('Status'),
        'restart':(h.get('RestartPolicy') or {}).get('Name'),
        'portBindings':h.get('PortBindings') or {},
        'mounts':[{'destination':x.get('Destination'),'type':x.get('Type'),'rw':x.get('RW')} for x in mounts],
        'composeService':lbl.get('com.docker.compose.service'),
        'composeProject':lbl.get('com.docker.compose.project'),
        'composeWorkingDir':lbl.get('com.docker.compose.project.working_dir'),
        'composeFiles':lbl.get('com.docker.compose.project.config_files'),
        'networks':sorted((a.get('NetworkSettings') or {}).get('Networks') or {}),
    }

def collect():
    containers={}
    for name in NAMES:
        record=extract(json.loads(execute(['docker','inspect',name])))
        if record['name']!=name: raise ValueError('unexpected Docker container identity '+name)
        containers[name]=record
    units={}
    for name in UNITS:
        lines=execute(['systemctl','show',name,'--no-pager','--property=LoadState,ActiveState,SubState,UnitFileState,Result,NextElapseUSecRealtime'])
        units[name]=dict(x.split('=',1) for x in lines.splitlines() if '=' in x)
    post=containers['diaries-postgres']
    if post['composeService']!='diaries-db': raise ValueError('Compose DB service identity drift')
    if containers['diaries-mosquitto']['composeService']!='diaries-mqtt': raise ValueError('Compose MQTT service identity drift')
    if containers['diaries-responder']['composeService']!='diaries-responder': raise ValueError('Responder Compose service identity drift')
    if '/data/files' not in [x['destination'] for x in containers['diaries-responder']['mounts']]:
        raise ValueError('Responder Files-root mount not found')
    if '/config/responder.json' not in [x['destination'] for x in containers['diaries-responder']['mounts']]:
        raise ValueError('Responder config mount not found')
    return {'schema':1,'feature':'0028-FEAT','mode':'READ_ONLY_RELEASE_CONTRACT',
            'containers':containers,'units':units,
            'publishedPostgresHostPort':bool(post['portBindings']),
            'writerIsolationVerified':False,'freshBackupVerified':False,
            'migrationArtifactDeployed':False,'productionApplyAuthorised':False}

def main():
    try:
        result=collect(); print(json.dumps(result,indent=2,sort_keys=True)); return 0
    except (OSError,ValueError,RuntimeError,KeyError,subprocess.TimeoutExpired) as e:
        print('FAIL: live release survey: '+str(e),file=sys.stderr); return 2
if __name__=='__main__': sys.exit(main())
