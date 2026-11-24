#!/usr/bin/env python3
"""0028 Step 3: bounded, read-only inspection of a retained Diaries dataset pair.

Remote mode runs as root through existing sudo -n ONLY to read privileged snapshots;
no data is changed. It does NOT hash full dump/Files bytes or verify restore.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

BACKUP_ID_RE = re.compile(r'^\d{8}-\d{6}Z$')
HEX64 = re.compile(r'^[0-9a-f]{64}$')
HISTORY = '/usr/local/sbin/diaries-backup-history'
DB_FILES = ('database/diaries.dump', 'database/diaries.sql')
CHECK_FILES = ('verification/database.sha256', 'verification/files.sha256', 'verification/inventory.json')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def canonical_relative(value):
    require(isinstance(value, str) and value and not value.startswith('/') and '\\' not in value,
            'unsafe relative component path')
    parts = value.split('/')
    require(all(p and p not in ('.', '..') for p in parts), 'unsafe path traversal')
    return parts


def safe_member(root, rel, *, directory=False):
    path = root
    for part in canonical_relative(rel):
        path = path / part
        meta = path.lstat()  # never follow symlinks in retained media
        require(not stat.S_ISLNK(meta.st_mode), 'symlink in retained component: ' + rel)
    mode = path.lstat().st_mode
    require(stat.S_ISDIR(mode) if directory else stat.S_ISREG(mode), 'missing/nonregular retained component: ' + rel)
    return path


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def descriptor(manifest, label, expected_path, root):
    row = manifest.get(label)
    require(isinstance(row, dict) and row.get('path') == expected_path, 'manifest descriptor changed: ' + label)
    size = row.get('sizeBytes')
    digest = row.get('sha256')
    require(type(size) is int and size > 0 and isinstance(digest, str) and HEX64.fullmatch(digest),
            'invalid manifest descriptor size/hash: ' + label)
    real = safe_member(root, expected_path)
    require(real.stat().st_size == size, 'retained component size mismatch: ' + expected_path)
    return {'sha256': digest, 'bytes': size}


def parse_hashes(data):
    found = {}
    for line in data.splitlines():
        require(len(line) > 66 and line[64:66] == '  ' and HEX64.fullmatch(line[:64]), 'invalid hash-list line')
        rel = line[66:]
        canonical_relative(rel)
        require(rel not in found, 'duplicate hash-list entry')
        found[rel] = line[:64]
    return found


def inspect_dataset(root, backup_id, expected_manifest_sha):
    require(isinstance(root, Path) and root.is_dir(), 'dataset path not a directory')
    require(root.resolve(strict=True) == root and not root.is_symlink(), 'dataset root not canonical')
    manifest_path = safe_member(root, 'dataset-manifest.json')
    manifest_sha = sha256(manifest_path)
    require(manifest_sha == expected_manifest_sha, 'history and dataset manifest hash mismatch')
    manifest = read_json(manifest_path)
    require(manifest.get('schemaVersion') == 2 and manifest.get('backupType') == 'complete-dataset'
            and manifest.get('completeDatasetBackup') is True and manifest.get('status') == 'complete',
            'not a completed schema-2 dataset')
    require(manifest.get('backupId') == backup_id and manifest.get('logicalDataset') == 'production',
            'dataset identity mismatch')
    db = manifest.get('database')
    files = manifest.get('files')
    require(isinstance(db, dict) and isinstance(files, dict), 'database/files missing in manifest')
    d1 = descriptor(db, 'customDump', DB_FILES[0], root)
    d2 = descriptor(db, 'sqlDump', DB_FILES[1], root)
    require(safe_member(root, 'files', directory=True).is_dir(), 'Files root missing')
    require(not (root/'files'/'.image-staging').exists(), 'transient image staging present in retained backup')
    snap = files.get('snapshot')
    require(isinstance(snap, dict) and snap.get('path') == 'files'
            and snap.get('verification') == 'verified', 'Files snapshot manifest invalid')
    count, total = snap.get('fileCount'), snap.get('totalBytes')
    require(type(count) is int and count > 0 and type(total) is int and total > 0,
            'Files snapshot counts missing/invalid')
    hashes = {}
    for rel in CHECK_FILES:
        path = safe_member(root, rel)
        digest = sha256(path)  # small metadata only, no payload bytes
        hashes[rel] = digest
    require(hashes['verification/files.sha256'] == snap.get('hashListSha256')
            and hashes['verification/inventory.json'] == snap.get('inventorySha256'),
            'Files index/hash-list checksum mismatch')
    db_hashes = parse_hashes(safe_member(root, 'verification/database.sha256').read_text(encoding='utf-8'))
    require(db_hashes == {DB_FILES[0]: d1['sha256'], DB_FILES[1]: d2['sha256']},
            'database hash list differs from manifest')
    inv = read_json(safe_member(root, 'verification/inventory.json'))
    require(inv.get('schemaVersion') == 1 and inv.get('root') == 'files'
            and inv.get('fileCount') == count and inv.get('totalBytes') == total,
            'Files inventory header mismatch')
    entries = inv.get('files')
    require(isinstance(entries, list) and len(entries) == count, 'Files inventory record count mismatch')
    seen = set()
    total_listed = 0
    for item in entries:
        require(isinstance(item, dict), 'invalid Files inventory row')
        path, length, digest = item.get('path'), item.get('sizeBytes'), item.get('sha256')
        canonical_relative(path)
        require(path.startswith('files/') and path not in seen and type(length) is int and length >= 0
                and isinstance(digest, str) and HEX64.fullmatch(digest), 'invalid or duplicate Files inventory row')
        seen.add(path)
        total_listed += length
    require(total_listed == total, 'Files inventory totals mismatch')
    file_hashes = parse_hashes(safe_member(root, 'verification/files.sha256').read_text(encoding='utf-8'))
    require(file_hashes == {e['path']: e['sha256'] for e in entries}, 'Files hash-list mismatch')
    # The full snapshot has already been verified at capture. Sample a bounded set of
    # component paths as a cheap availability check; not a full restore/content check.
    samples = sorted({0, len(entries)//2, len(entries)-1})
    for i in samples:
        file = safe_member(root, entries[i]['path'])
        require(file.stat().st_size == entries[i]['sizeBytes'], 'sample retained Files size mismatch')
    return {
      'schema': 1, 'backupId': backup_id, 'logicalDataset': 'production',
      'manifestSha256': manifest_sha, 'database': {
          'customDump': d1, 'sqlDump': d2,
          'hashListSha256': hashes['verification/database.sha256']},
      'files': {'fileCount': count, 'totalBytes': total,
                'inventorySha256': hashes['verification/inventory.json'],
                'hashListSha256': hashes['verification/files.sha256'],
                'sampleFilesPresentWithExpectedSize': len(samples)},
      'validationClass': 'MANIFEST_METADATA_AND_COMPONENT_PRESENCE_ONLY',
      'fullFileContentVerified': False, 'restoreVerified': False,
      'productionApplyAuthorised': False
    }


def remote(backup_id):
    require(BACKUP_ID_RE.fullmatch(backup_id) is not None, 'backup ID must be UTC timestamp format')
    result = subprocess.run([HISTORY, '--json', 'show', backup_id, '--logical-dataset', 'production'],
                            text=True, capture_output=True, timeout=180)
    require(result.returncode == 0, 'backup-history show failed: ' + result.stderr.strip()[:300])
    data = json.loads(result.stdout)
    require(data.get('backupId') == backup_id and data.get('logicalDataset') == 'production',
            'backup-history show identity mismatch')
    occur = data.get('occurrences')
    require(isinstance(occur, list) and occur, 'no retained occurrences')
    manifest_hashes = {v.get('manifestSha256') for v in occur}
    require(len(manifest_hashes) == 1, 'inconsistent manifests among retained occurrences')
    newest = max(occur, key=lambda v: v['snapshot'])
    root = Path(newest['path'])
    receipt = inspect_dataset(root, backup_id, newest['manifestSha256'])
    receipt['selectedRetainedSnapshot'] = newest['snapshot']
    print(json.dumps(receipt, indent=2, sort_keys=True))


def selected_backup(status1, status2):
    items = []
    for s in (status1, status2):
        require(s.get('health') == 'healthy' and s.get('component') == 'diaries'
                and s.get('conflictedBackups') == 0, 'backup host not healthy')
        latest = s.get('latest')
        require(isinstance(latest, dict) and latest.get('logicalDataset') == 'production',
                'latest backup not production')
        value = latest.get('backupId')
        require(isinstance(value, str) and BACKUP_ID_RE.fullmatch(value), 'latest backup ID invalid')
        items.append(value)
    require(items[0] == items[1], 'host latest backup identities differ')
    return items[0]


def summarize(folder):
    folder = Path(folder)
    statuses = [read_json(folder / (host+'-status.json')) for host in ('mars','backup')]
    backup_id = selected_backup(*statuses)
    a, b = [read_json(folder/(host+'-contents.json')) for host in ('mars','backup')]
    for result in (a,b):
        require(result.get('backupId') == backup_id and result.get('logicalDataset') == 'production',
                'content receipt backup identity mismatch')
        require(result.get('validationClass') == 'MANIFEST_METADATA_AND_COMPONENT_PRESENCE_ONLY'
                and result.get('fullFileContentVerified') is False and result.get('restoreVerified') is False,
                'unexpected verification claims in content receipt')
        require(result.get('productionApplyAuthorised') is False, 'unexpected production authorisation')
    fields = ('manifestSha256','database','files')
    for field in fields:
        require(a.get(field) == b.get(field), 'mars/backup retained component metadata mismatch: '+field)
    return {'schema':1, 'feature':'0028-FEAT', 'backupId':backup_id,
            'inspectionResult':'MATCHING_RETAINED_COMPONENT_METADATA',
            'marshalledHosts':{'mars':a.get('selectedRetainedSnapshot'),
                              'backup':b.get('selectedRetainedSnapshot')},
            'manifestSha256': a['manifestSha256'],
            'database':a['database'], 'files':a['files'],
            'fullFileContentVerified':False, 'restoreVerified':False,
            'freshPostWriterStopPointVerified':False,
            'writerIsolationVerified':False, 'productionApplyAuthorised':False}


def main(argv):
    try:
        if len(argv) == 2 and BACKUP_ID_RE.fullmatch(argv[1]):
            remote(argv[1])
        elif len(argv) == 3 and argv[1] == '--select':
            folder = Path(argv[2]); print(selected_backup(read_json(folder/'mars-status.json'),read_json(folder/'backup-status.json')))
        elif len(argv) == 3 and argv[1] == '--summarize':
            result=summarize(argv[2]); folder=Path(argv[2]); out=folder/'RETAINED-CONTENTS-RESULT.json'
            out.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
            print('PASS: matching retained manifest and component metadata: '+result['backupId'])
            print('PASS: DB custom+SQL dumps present; Files inventory/hash list present; sampled Files paths exist')
            print('NOT VERIFIED: full content hashes, complete restore, fresh writer-stopped recovery point')
            print('PRODUCTION APPLY NOT AUTHORISED')
            print('Private result: '+str(out))
        else:
            raise ValueError('usage: script <backupId> | --select <folder> | --summarize <folder>')
        return 0
    except (OSError, ValueError, KeyError, subprocess.SubprocessError, TypeError, json.JSONDecodeError) as exc:
        print('FAIL: '+str(exc), file=sys.stderr);return 2

if __name__ == '__main__':
    sys.exit(main(sys.argv))
