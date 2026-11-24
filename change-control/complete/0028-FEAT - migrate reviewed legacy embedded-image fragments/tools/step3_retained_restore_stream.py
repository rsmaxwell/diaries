#!/usr/bin/env python3
"""0028 read-only retained-Diaries dump inspection/stream and Windows receipt gates.

On mars this runs as `sudo -n python3 -` from a local feature script. Only
--stream writes its *stdout*, which contains the raw database backup bytes.
No files, snapshots, databases, or configuration are modified on mars.
"""
import hashlib
import json
import pathlib
import re
import stat
import subprocess
import sys

HISTORY = '/usr/local/sbin/diaries-backup-history'
NAME = re.compile(r'^\d{8}-\d{6}Z$')
SHA = re.compile(r'^[0-9a-f]{64}$')
MAX_METADATA = 40 * 1024 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def regular_inside(root, relative):
    require(isinstance(relative, str) and relative and not relative.startswith('/')
            and '\\' not in relative, 'unsafe file path')
    path = root
    for part in relative.split('/'):
        require(part not in ('', '.', '..'), 'unsafe file traversal')
        path = path / part
        mode = path.lstat().st_mode
        require(not stat.S_ISLNK(mode), 'symlink in retained component')
    require(stat.S_ISREG(path.lstat().st_mode), 'component is not regular file')
    return path


def read_json(path):
    require(path.stat().st_size < MAX_METADATA, 'unexpectedly large metadata file')
    return json.loads(path.read_text(encoding='utf-8'))


def choose_occurrence(backup_id, runner=None):
    require(NAME.fullmatch(backup_id), 'invalid backup ID')
    if runner is None:
        runner = subprocess.run
    proc = runner([HISTORY, '--json', 'show', backup_id, '--logical-dataset', 'production'],
                  text=True, capture_output=True, timeout=180)
    require(proc.returncode == 0, 'history show failed: ' + (proc.stderr or '')[:350])
    doc = json.loads(proc.stdout)
    require(doc.get('backupId') == backup_id and doc.get('logicalDataset') == 'production',
            'history backup identity mismatch')
    occ = doc.get('occurrences')
    require(isinstance(occ, list) and occ, 'no retained occurrences')
    hashes = {v.get('manifestSha256') for v in occ if isinstance(v, dict)}
    require(len(hashes) == 1 and all(SHA.fullmatch(h or '') for h in hashes),
            'conflicting retained manifests')
    chosen = max(occ, key=lambda o: o['snapshot'])
    root = pathlib.Path(chosen['path'])
    require(root.is_dir() and not root.is_symlink() and root.resolve(strict=True) == root,
            'retained path is not canonical')
    return root, chosen['snapshot'], chosen['manifestSha256']


def read_dump_metadata(backup_id, *, runner=None):
    root, snapshot, expected_manifest = choose_occurrence(backup_id, runner)
    mpath = regular_inside(root, 'dataset-manifest.json')
    require(digest(mpath) == expected_manifest, 'snapshot manifest checksum mismatch')
    m = read_json(mpath)
    require(m.get('schemaVersion') == 2 and m.get('status') == 'complete'
            and m.get('logicalDataset') == 'production' and m.get('backupId') == backup_id,
            'not a complete production schema-2 dataset')
    db = m.get('database')
    require(isinstance(db, dict), 'missing database descriptors')
    custom = db.get('customDump')
    require(isinstance(custom, dict) and custom.get('path') == 'database/diaries.dump',
            'unexpected custom dump path')
    size, sha = custom.get('sizeBytes'), custom.get('sha256')
    require(type(size) is int and 0 < size <= 2 * 1024 * 1024 * 1024
            and isinstance(sha, str) and SHA.fullmatch(sha),
            'invalid custom dump manifest descriptor')
    path = regular_inside(root, 'database/diaries.dump')
    require(path.stat().st_size == size, 'retained dump length differs from manifest')
    return {'backupId': backup_id, 'logicalDataset': 'production',
            'manifestSha256': expected_manifest, 'customDumpSha256': sha,
            'customDumpBytes': size, 'snapshot': snapshot,
            '_dump_path': path, '_root': root}


def sample_files(meta, *, limit=3, max_bytes=32 * 1024 * 1024):
    manifest = read_json(regular_inside(meta['_root'], 'dataset-manifest.json'))
    index_file = regular_inside(meta['_root'], 'verification/inventory.json')
    index_sha = (manifest.get('files') or {}).get('snapshot', {}).get('inventorySha256')
    require(isinstance(index_sha, str) and SHA.fullmatch(index_sha)
            and digest(index_file) == index_sha, 'Files inventory checksum changed')
    inv = read_json(index_file)
    rows = inv.get('files')
    require(isinstance(rows, list) and rows, 'Files inventory missing')
    eligible = [r for r in rows if isinstance(r, dict) and type(r.get('sizeBytes')) is int
                and 0 <= r['sizeBytes'] <= max_bytes and isinstance(r.get('sha256'), str)
                and SHA.fullmatch(r['sha256'])]
    require(len(eligible) >= limit, 'not enough bounded Files samples')
    picks = [eligible[0], eligible[len(eligible)//2], eligible[-1]]
    checked = []
    for row in picks:
        path = regular_inside(meta['_root'], row['path'])
        require(path.stat().st_size == row['sizeBytes'], 'sample Files size mismatch')
        require(digest(path) == row['sha256'], 'sample Files bytes do not match inventory')
        checked.append({'bytes': row['sizeBytes'], 'sha256': row['sha256']})
    return checked


def compare_pair(paired, remote):
    require(paired.get('inspectionResult') == 'MATCHING_RETAINED_COMPONENT_METADATA'
            and paired.get('productionApplyAuthorised') is False,
            'not the accepted paired metadata receipt')
    require(paired.get('backupId') == remote.get('backupId'), 'backup ID drift')
    require(paired.get('manifestSha256') == remote.get('manifestSha256'), 'manifest identity drift')
    desc = paired.get('database', {}).get('customDump', {})
    require(desc.get('sha256') == remote.get('customDumpSha256')
            and desc.get('bytes') == remote.get('customDumpBytes'), 'database dump descriptor drift')
    require(remote.get('sampleFilesVerified') == 3, 'retained Files sample was not verified')
    return {'backupId': remote['backupId'], 'manifestSha256': remote['manifestSha256'],
            'customDumpSha256': remote['customDumpSha256'],
            'customDumpBytes': remote['customDumpBytes'], 'sampleFilesVerified': 3}


def remote_inspect(backup_id):
    meta = read_dump_metadata(backup_id)
    checked = sample_files(meta)
    return {'backupId': backup_id, 'logicalDataset': 'production',
            'manifestSha256': meta['manifestSha256'], 'customDumpSha256': meta['customDumpSha256'],
            'customDumpBytes': meta['customDumpBytes'], 'selectedRetainedSnapshot': meta['snapshot'],
            'sampleFilesVerified': len(checked), 'sampleFileDigests': checked,
            'fullFilesVerified': False, 'productionApplyAuthorised': False}


def remote_stream(backup_id, expected_manifest, expected_sha, expected_size):
    require(SHA.fullmatch(expected_manifest) and SHA.fullmatch(expected_sha), 'invalid expected SHA')
    meta = read_dump_metadata(backup_id)
    require(meta['manifestSha256'] == expected_manifest and meta['customDumpSha256'] == expected_sha
            and str(meta['customDumpBytes']) == expected_size, 'restore source identity changed')
    h = hashlib.sha256()
    count = 0
    with meta['_dump_path'].open('rb') as src:
        while True:
            block = src.read(1024 * 1024)
            if not block: break
            h.update(block)
            count += len(block)
            sys.stdout.buffer.write(block)
    sys.stdout.buffer.flush()
    require(count == meta['customDumpBytes'] and h.hexdigest() == expected_sha,
            'dump content SHA-256 mismatch while streaming')
    print('PASS: full retained custom dump SHA-256 verified while streaming', file=sys.stderr)


def main(argv):
    try:
        if len(argv) == 3 and argv[1] == '--inspect':
            print(json.dumps(remote_inspect(argv[2]), indent=2, sort_keys=True))
        elif len(argv) == 6 and argv[1] == '--stream':
            remote_stream(*argv[2:])
        elif len(argv) == 5 and argv[1] == '--compare':
            paired = read_json(pathlib.Path(argv[2]))
            remote = read_json(pathlib.Path(argv[3]))
            pathlib.Path(argv[4]).write_text(json.dumps(compare_pair(paired, remote), indent=2, sort_keys=True)+'\n')
            print('PASS: retained source identity bound to accepted mars/backup pair')
        else:
            raise ValueError('usage: --inspect BACKUP_ID | --stream BACKUP_ID MANIFEST_SHA DUMP_SHA BYTES | --compare PAIRED REMOTE OUT')
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, subprocess.SubprocessError) as exc:
        print('FAIL: '+str(exc), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
