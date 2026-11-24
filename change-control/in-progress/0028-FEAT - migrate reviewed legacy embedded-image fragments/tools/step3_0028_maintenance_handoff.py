#!/usr/bin/env python3
"""Evidence-bound 0028 maintenance handoff. Python 3.8+, local and read-only.

No SSH, Docker, SQL, production backup, migration, service, or Git changes.
This program does not verify writer isolation or authorize an application.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
import zipfile

FEATURE = '0028-FEAT'
BACKUP = '20261124-003112Z'
CONTAINERS = {'diaries-postgres': 'diaries-db',
              'diaries-mosquitto': 'diaries-mqtt',
              'diaries-responder': 'diaries-responder',
              'diaries-client': 'diaries-client',
              'diaries-web': 'diaries-web'}
CLASS = 'com/rsmaxwell/diaries/responder/migration/migration0028/Migration0028ReviewedFragments.class'
SQL = 'migration0028/001-create-journal.sql'
EXPECTED_COUNTS = {'fragments': 2331, 'marquees': 2270, 'images': 85, 'pages': 683}
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HEX40 = re.compile(r'^[0-9a-f]{40}$')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read_json(path):
    raw = Path(path).read_bytes()
    obj = json.loads(raw)
    require(isinstance(obj, dict), 'evidence must contain a JSON object: ' + str(path))
    return obj, hashlib.sha256(raw).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as inp:
        for block in iter(lambda: inp.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def artifact_identity(directory):
    root = Path(directory)
    lines = (root / 'ARTIFACT-IDENTITY.txt').read_text(encoding='utf-8').splitlines()
    record = {}
    for line in lines:
        key, sep, value = line.partition('=')
        require(sep and key and key not in record, 'invalid artifact receipt key')
        record[key] = value
    require(record.get('schema') == '1' and record.get('feature') == FEATURE,
            'unexpected migration artifact receipt')
    require(record.get('status') == 'BUILT_NOT_DEPLOYED_NOT_APPROVED',
            'artifact receipt must not claim deployment/approval')
    require(HEX40.fullmatch(record.get('source_commit', '')) is not None,
            'missing artifact Git source revision')
    require(HEX64.fullmatch(record.get('artifact_sha256', '')) is not None,
            'invalid artifact checksum')
    require(record.get('artifact') == 'diaries-0028-reviewed-migration-fat.jar',
            'unexpected artifact filename')
    jar = root / record['artifact']
    require(jar.is_file() and not jar.is_symlink(), 'artifact missing or symbolic link')
    require(sha256_file(jar) == record['artifact_sha256'], 'migration JAR checksum mismatch')
    with zipfile.ZipFile(jar) as z:
        for key in (CLASS, SQL):
            require(z.namelist().count(key) == 1, 'JAR entry missing/duplicated: ' + key)
            info = z.getinfo(key)
            require(info.file_size > 0, 'JAR entry empty: ' + key)
            content = z.read(key)
            require(len(content) == info.file_size, 'JAR entry size mismatch: ' + key)
        raw = z.read(CLASS)
    require(raw[:4] == b'\xca\xfe\xba\xbe', 'migration class invalid')
    major = int.from_bytes(raw[6:8], 'big')
    require(major <= 69 and major >= 65,
            'unexpected migration Java class major version')
    return record, major


def assess(candidate, runtime, recovery, artifact, class_major, source_commit):
    require(candidate.get('result') == 'RELEASE_CANDIDATE_PREPARED_NO_PRODUCTION_PERMISSION' and
            candidate.get('productionApplyAuthorised') is False and
            candidate.get('writerIsolationVerified') is False,
            'release-candidate receipt must remain unapproved')
    require(candidate.get('migrationJarSha256') == artifact['artifact_sha256'] and
            candidate.get('responderGitCommit') == artifact['source_commit'] and
            candidate.get('retainedDatabaseRecoveryBackupId') == BACKUP,
            'release-candidate/artifact/backup identity drift')
    require(candidate.get('retainedDatabaseRestoreVerified') is True and
            candidate.get('fullFilesRestoreVerified') is False,
            'unexpected previous restore acceptance')
    require(source_commit == artifact['source_commit'], 'local responder revision differs from built JAR source')
    require(runtime.get('mode') == 'READ_ONLY_RELEASE_CONTRACT' and
            runtime.get('writerIsolationVerified') is False and
            runtime.get('productionApplyAuthorised') is False,
            'runtime receipt must be read-only and unapproved')
    containers = runtime.get('containers')
    require(isinstance(containers, dict) and set(containers) == set(CONTAINERS),
            'unexpected live container identities')
    for name, service in CONTAINERS.items():
        require(containers[name].get('name') == name and
                containers[name].get('composeService') == service and
                containers[name].get('imageId'), 'unexpected Compose contract: ' + name)
    require('postgres:18' in containers['diaries-postgres'].get('image', ''), 'wrong PostgreSQL major version')
    require(candidate.get('currentResponderImage') == containers['diaries-responder'].get('image'),
            'responder image differs from release-candidate receipt')
    require(runtime.get('publishedPostgresHostPort') is True and
            bool(containers['diaries-postgres'].get('portBindings')),
            'PostgreSQL host-port contract has changed; review isolation anew')
    require(runtime.get('freshBackupVerified') is False,
            'survey must not claim a fresh writer-stopped backup')
    mounts = containers['diaries-responder'].get('mounts') or []
    require(isinstance(mounts, list), 'missing responder mount inventory')
    destinations = {x.get('destination'): x for x in mounts if isinstance(x, dict)}
    require('/config/responder.json' in destinations and '/data/files' in destinations,
            'responder config/Files mounts not proven')
    units = runtime.get('units')
    for name in ('diaries-compose.service',
                 'diaries-complete-backup-publish.service',
                 'diaries-complete-backup-publish.timer'):
        require(isinstance(units, dict) and name in units and
                units[name].get('LoadState') == 'loaded',
                'missing/unknown systemd unit: ' + name)
    require(recovery.get('backupId') == BACKUP and
            recovery.get('databaseRestoreVerified') is True and
            recovery.get('restoredCounts') == EXPECTED_COUNTS and
            recovery.get('allFilesPayloadsVerified') is False and
            recovery.get('productionWriterIsolationVerified') is False and
            recovery.get('productionApplyAuthorised') is False,
            'previous restored-backup acceptance drift')
    return {
        'schema': 1, 'feature': FEATURE,
        'result': 'OPERATOR_HANDOFF_PREPARED_NOT_APPROVED',
        'responderSourceCommit': source_commit,
        'migrationJarSha256': artifact['artifact_sha256'],
        'migrationClassMajor': class_major,
        'requiredJavaMajor': class_major - 44,
        'databaseRestoreVerifiedBackupId': BACKUP,
        'selectedCurrentResponderImage': containers['diaries-responder']['image'],
        'postgresqlPublishedPort': True,
        'backupPublicationMutatesWorkingCopy': True,
        'freshWriterStoppedRecoveryPointVerified': False,
        'productionWriterIsolationVerified': False,
        'productionDryRunVerified': False,
        'ownerStep1Step2Accepted': False,
        'productionApplyAuthorised': False,
        'remainingHardGates': [
            'Formal Step 1 and Step 2 owner acceptance',
            'Confirm Java 25 compatibility and one-shot Compose-run contract',
            'Agree and enforce Editor/MQTT, responder and direct PostgreSQL isolation',
            'Pause/coordinate backup timer and wait for active capture service to end',
            'Perform writer-stopped fixed production capture and verify its schema-2 marker',
            'Pull to mars, create/pin immutable Btrfs snapshot and replicate/verify on backup',
            'Repeat fresh writer-stopped source/Fragment-lock preflight',
            'Perform production dry-run using pinned CLI with its own new output directory',
            'Freeze production plan/manifest and separately approve exact apply',
            'Create/check separately reviewed migration SQL journal, then run approved apply',
            'Validate journal, reconcile retained MQTT and visually smoke test Editor/Reader',
            'Retain rollback material and obtain formal closure approval'
        ]
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--candidate', required=True)
    p.add_argument('--runtime', required=True)
    p.add_argument('--recovery', required=True)
    p.add_argument('--artifact-dir', required=True)
    p.add_argument('--source-commit', required=True)
    p.add_argument('--output', required=True)
    a = p.parse_args(argv)
    try:
        require(HEX40.fullmatch(a.source_commit) is not None, 'invalid local Git source revision')
        candidate, ch = read_json(a.candidate)
        runtime, rh = read_json(a.runtime)
        recovery, bh = read_json(a.recovery)
        artifact, major = artifact_identity(a.artifact_dir)
        result = assess(candidate, runtime, recovery, artifact, major, a.source_commit)
        result['evidenceSha256'] = {'candidate': ch, 'runtime': rh, 'recovery': bh}
        out = Path(a.output)
        require(out.parent.is_dir() and not out.exists(), 'refusing to overwrite/create evidence directory')
        out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n', encoding='utf-8')
        print('PASS: bound migration JAR / release candidate / live-runtime survey / restored backup')
        print('Migration class Java major:', major, '(Java {} required)'.format(major - 44))
        print('OPEN: live writer isolation, fresh immutable rollback backup, production dry-run, approvals')
        print('PRODUCTION APPLY NOT AUTHORISED')
        return 0
    except (OSError, ValueError, KeyError, TypeError, zipfile.BadZipFile, json.JSONDecodeError) as ex:
        print('FAIL: 0028 maintenance handoff: {}'.format(ex), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
