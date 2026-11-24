#!/usr/bin/env python3
"""Read-only 0028 recovery-probe receipt; collection success != recovery acceptance."""
import datetime
import json
import pathlib
import re
import sys


def parse_status(data):
    """Extract JSON from a diagnostic file without trusting surrounding shell text."""
    decoder = json.JSONDecoder()
    begin = data.find('=== DIARIES BACKUP STATUS ===')
    if begin < 0:
        return {'health': 'unavailable', 'reason': 'status section absent'}
    chunk = data[begin:]
    match = re.search(r'(?m)^DIARIES_BACKUP_STATUS_EXIT=(\d+)\s*$', chunk)
    if not match or match.group(1) != '0':
        return {'health': 'error', 'reason': 'host-local Diaries status exit is not zero or missing'}
    for line in chunk.splitlines()[1:]:
        if line.strip().startswith('{'):
            try:
                result, _ = decoder.raw_decode(chunk[chunk.index(line):])
                if isinstance(result, dict) and result.get('component') == 'diaries':
                    return result
            except (ValueError, KeyError):
                pass
    return {'health': 'error', 'reason': 'no valid Diaries JSON status'}


def summarize(results_path):
    folder = pathlib.Path(results_path).parent
    lines = pathlib.Path(results_path).read_text(encoding='utf-8').splitlines()
    if not lines or lines[0] != 'host\tprobe\texit_status':
        raise ValueError('Invalid probe status file')
    probes=[]
    for line in lines[1:]:
        host, check, code = line.split('\t')
        probes.append({'host':host,'probe':check,'exitStatus':int(code)})
    if {p['host'] for p in probes} != {'pluto', 'mars', 'backup'} or len(probes)!=3:
        raise ValueError('Expected exactly pluto, mars and backup probes')
    summaries={}
    for host in ('mars','backup'):
        log_file=folder/('{}.log'.format(next(p['host']+'-'+p['probe'] for p in probes if p['host']==host)))
        if log_file.is_file():
            status=parse_status(log_file.read_text(encoding='utf-8',errors='replace'))
        else:
            status={'health':'unavailable','reason':'missing remote log'}
        latest=status.get('latest')
        summaries[host]={
            'health': status.get('health','unknown'),
            'latestBackupId': latest.get('backupId') if isinstance(latest,dict) else None,
            'latestRetainedUtc': latest.get('lastRetainedSnapshot') if isinstance(latest,dict) else None,
            'evidenceClass': status.get('evidence','missing'),
            'warningsCount':len(status.get('warnings',[])) if isinstance(status.get('warnings'),list) else None
        }
    identities=[summaries[h]['latestBackupId'] for h in ('mars','backup')]
    alignment='SAME_LATEST_BACKUP_ID_NOT_RESTORE_VERIFIED' if identities[0] and identities[0]==identities[1] else 'NOT_CONFIRMED'
    result={
        'schema':1,'feature':'0028-FEAT',
        'collectedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'probeCollection':'COMPLETE' if all(p['exitStatus']==0 for p in probes) else 'INCOMPLETE',
        'probes':probes,'backups':summaries,'retainedIdentityAlignment':alignment,
        'matchingFreshProductionDBAndFilesRecoveryPoint':'NOT_VERIFIED',
        'fullDatasetRestoreFromBackup':'NOT_REHEARSED_IN_THIS_INCREMENT',
        'productionWriterIsolation':'NOT_PERFORMED',
        'productionDeployedRevisionCompatibility':'REQUIRES_OPERATOR_REVIEW',
        'formalStep1Acceptance':'OPEN',
        'productionApplyAuthorised':False,
        'note': 'Retained backup manifest metadata alone is not a full-content recovery proof. Do not infer production readiness from successful probe collection.'
    }
    return result


def main(argv):
    if len(argv)!=3:
        print('usage: summary.py PROBE-STATUS.tsv OUTPUT.json',file=sys.stderr);return 2
    try:
        result=summarize(argv[1])
        pathlib.Path(argv[2]).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    except (OSError,ValueError) as exc:
        print('FAIL: '+str(exc),file=sys.stderr);return 2
    print('Probe collection:',result['probeCollection'])
    for host in ('mars','backup'):
        print('{}: {} latest {} last retained {}'.format(host,result['backups'][host]['health'],result['backups'][host]['latestBackupId'],result['backups'][host]['latestRetainedUtc']))
    print('Retained dataset identity:',result['retainedIdentityAlignment'])
    print('PRODUCTION GATE: OPEN; backup restore, verified fresh recovery point, writer isolation and approval remain separate')
    print('Private result:',argv[2])
    return 0 if result['probeCollection']=='COMPLETE' else 2

if __name__=='__main__':
    sys.exit(main(sys.argv))
