#!/usr/bin/env python3
"""0028 evidence-only Step 3 maintenance decision analysis (Python 3.8+).

Reads EXISTING private evidence; never contacts any host, Docker or database.
Does not grant owner approval, verify writer isolation or authorise apply.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys

EXPECTED = ('diaries-postgres', 'diaries-mosquitto', 'diaries-responder',
            'diaries-client', 'diaries-web')
EXPECTED_COUNTS = {'fragments': 2331, 'marquees': 2270,
                   'images': 85, 'pages': 683}
BACKUP_ID = '20261124-003112Z'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read_object(path):
    path = Path(path)
    require(path.is_file(), 'missing evidence: ' + path.name)
    raw = path.read_bytes()
    require(len(raw) > 20, 'empty evidence: ' + path.name)
    obj = json.loads(raw)
    require(isinstance(obj, dict), 'expected JSON object: ' + path.name)
    return obj, hashlib.sha256(raw).hexdigest()


def assess(writer, recovery, hashes):
    require(writer.get('inspection') == 'PRODUCTION_WRITER_CHANNELS_READ_ONLY',
            'unrecognised live-writer survey')
    require(writer.get('writerIsolationVerified') is False and
            writer.get('productionApplyAuthorised') is False,
            'writer survey must not claim authorization')
    containers = writer.get('containers')
    require(isinstance(containers, dict), 'container identities missing')
    require(set(containers) == set(EXPECTED), 'production container names differ from recorded survey')
    for name in EXPECTED:
        c = containers[name]
        require(isinstance(c, dict) and c.get('name') == name and
                c.get('image') and c.get('imageId') and c.get('state'),
                'missing container identity: ' + name)
    pg = containers['diaries-postgres']
    require('postgres:18' in pg['image'], 'unexpected production PostgreSQL image')
    require('publishedPorts' in pg, 'missing PostgreSQL port bindings')
    ports = pg['publishedPorts']
    require(isinstance(ports, dict), 'malformed host PostgreSQL ports')
    require(bool(ports) == writer.get('databasePortPublished'),
            'published port survey is internally inconsistent')
    units = writer.get('systemdUnits')
    require(isinstance(units, dict) and
            {'diaries-compose.service', 'diaries-complete-backup-publish.timer',
             'diaries-complete-backup-publish.service'}.issubset(units),
            'missing backup/compose supervisor survey')
    groups = writer.get('databaseClientGroups')
    require(isinstance(groups, list), 'database client groups missing')
    count = 0
    states = {}
    for group in groups:
        require(isinstance(group, str), 'invalid PostgreSQL client group')
        fields = group.split('|')
        require(len(fields) == 5 and fields[4].isdigit(), 'invalid PostgreSQL group shape')
        count += int(fields[4]); state = fields[3].strip() or 'unknown'
        states[state] = states.get(state, 0) + int(fields[4])
    require(recovery.get('feature') == '0028-FEAT' and
            recovery.get('recoveryClass') == 'RETAINED_DB_RESTORE_VERIFIED' and
            recovery.get('backupId') == BACKUP_ID and
            recovery.get('databaseRestoreVerified') is True and
            recovery.get('productionApplyAuthorised') is False,
            'restore result not the accepted 0028 retained verification')
    require(recovery.get('restoredCounts') == EXPECTED_COUNTS,
            'retained restore counts differ from acceptance evidence')
    require(recovery.get('filesPayloadSampleHashesVerified') == 3 and
            recovery.get('allFilesPayloadsVerified') is False,
            'unexpected Files verification extent')
    require(recovery.get('productionWriterIsolationVerified') is False and
            recovery.get('freshWriterStoppedRecoveryPointVerified') is False,
            'restore evidence incorrectly claims an execution gate')
    require(isinstance(recovery.get('customDumpSha256'), str) and
            len(recovery['customDumpSha256']) == 64 and
            all(c in '0123456789abcdef' for c in recovery['customDumpSha256']),
            'missing or malformed accepted dump digest')
    return {
        'schema': 1, 'feature': '0028-FEAT',
        'result': 'PREPARATION_EVIDENCE_REVIEWED_NOT_RELEASED',
        'writerSurveySha256': hashes['writer'],
        'recoveryReceiptSha256': hashes['recovery'],
        'backupId': BACKUP_ID,
        'databaseRecoveryVerified': True,
        'restoredCounts': EXPECTED_COUNTS,
        'filesSampleChecks': 3,
        'completeFilesRestoreVerified': False,
        'productionContainers': {name: {
            'image': containers[name]['image'],
            'restartPolicy': containers[name].get('restartPolicy'),
            'stateAtSurvey': containers[name]['state']}
            for name in EXPECTED},
        'databaseHostPortExposedAtSurvey': bool(ports),
        'observedPostgresClientCount': count,
        'observedPostgresClientStates': states,
        'backupTimerAtSurvey': units['diaries-complete-backup-publish.timer'],
        'composeSupervisorAtSurvey': units['diaries-compose.service'],
        'remainingHardGates': [
            'Owner formal Step 1 and Step 2 acceptance',
            'Exact compatible migration runtime and source/submodule commit identities',
            'Controlled ingress stop and responder/drain plan approved',
            'Direct PostgreSQL ingress positively blocked and all sessions accounted for',
            'Backup timer/service coordinated so responder cannot restart during maintenance',
            'Fresh writer-stopped, matching DB+Files backup/replication/rollback receipt',
            'Final writer-stopped production freshness and lock preflight',
            'Exact production plan/approval file with owner approval',
            'Production migration, journal postflight, MQTT replay, GUI smoke',
            'Separate formal feature closure decision'
        ],
        'productionWriterIsolationVerified': False,
        'productionApplyAuthorised': False,
        'featureClosed': False,
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--writer', required=True)
    parser.add_argument('--recovery', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    try:
        writer, wh = read_object(args.writer)
        recovery, rh = read_object(args.recovery)
        result = assess(writer, recovery, {'writer': wh, 'recovery': rh})
        output = Path(args.output)
        require(not output.exists(), 'refusing to overwrite evidence')
        require(output.parent.is_dir(), 'output directory absent')
        output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print('PASS: accepted retained DB recovery and production writer survey evidence validated')
        print('PostgreSQL host port exposed at survey:', result['databaseHostPortExposedAtSurvey'])
        print('Observed PostgreSQL sessions at survey:', result['observedPostgresClientCount'])
        print('OPEN: writer isolation, fresh consistent DB+Files recovery point, compatible runtime, owner approval')
        print('PRODUCTION APPLY NOT AUTHORISED')
        return 0
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print('FAIL: release-gate evidence invalid: ' + str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
