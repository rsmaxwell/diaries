#!/usr/bin/env python3
"""0040 Step 12: inspect/optionally archive one obsolete receiver journal.

`audit` makes NO changes. `archive` performs one rename of the validated legacy
journal into a root-only rollback directory, with both historical receiver
locks held. A published, readonly candidate with a matching valid receipt is
permitted only with explicit --allow-completed-candidate and receipt hash
pinning. It never deletes/modifies Btrfs subvolumes, receipts or parent state.

Run on the actual endpoint via `sudo -n python3 - ... < this-file` from mango.
"""
import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

B = '20261101-140039Z'
SOURCE_ROOT = Path('/media/usb/@snapshots/@data')
RECEIVER_ROOT = Path('/@data/mars-received/@data')
STATE = Path('/@data/mars-received/.replication-state')
JOURNAL = STATE / '.agreed-parent-transfer-pending.json'
ARCHIVE_DIR = STATE / '.0040-retired-legacy'
MANAGER = Path('/run/lock/btrfs-snapshot-manager.lock')
WRITER = STATE / 'writer.lock'
SOURCE_FS = '72d1d8ea-900e-4fca-837f-1b1febec036c'
RECEIVER_FS = 'b915f967-7cb4-4c14-b11b-f52209637a22'
SIMPLE_SOURCE = SOURCE_ROOT.parent / '.simple-agreed-parent.json'
SIMPLE_RECEIVER = STATE / '.simple-agreed-parent.json'
STAMP = re.compile(r'[0-9]{8}-[0-9]{6}Z\Z')
UUID = re.compile(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\Z')
NONCE = re.compile(r'[0-9a-f]{64}\Z')
REQUIRED_OWNER_UID = 0  # root on production hosts; tests patch this constant only

class Refuse(RuntimeError):
    pass

def check(predicate, why):
    if not predicate:
        raise Refuse(why)

def checked_run(*args):
    return subprocess.run(args, text=True, capture_output=True, check=True).stdout

def safe_dir(path):
    check(not path.is_symlink() and path.is_dir(), f'Unsafe directory: {path}')

def filesystem(role):
    mount = '/media/usb' if role == 'source' else '/'
    expected = SOURCE_FS if role == 'source' else RECEIVER_FS
    result = checked_run('btrfs', 'filesystem', 'show', mount)
    check(re.search(r'\buuid:\s*' + re.escape(expected) + r'\b', result, re.I),
          f'Filesystem identity mismatch on {mount}')
    print(f'Filesystem identity: VERIFIED {expected}')

def info(root, name):
    check(STAMP.fullmatch(name) is not None, 'Invalid snapshot timestamp')
    safe_dir(root)
    p = root / name
    check(not p.is_symlink(), f'Symlink snapshot: {p}')
    if not p.exists():
        return None
    check(p.is_dir(), f'Unexpected non-directory snapshot: {p}')
    data = checked_run('btrfs', 'subvolume', 'show', str(p))
    fields = dict(re.findall(r'^\s*(UUID|Received UUID|Flags|Parent UUID):\s*(.*?)\s*$', data, re.M))
    check(set(fields) == {'UUID', 'Received UUID', 'Flags', 'Parent UUID'} and
          UUID.fullmatch(fields['UUID']) is not None, f'Unexpected Btrfs identity: {p}')
    return fields

def brief(label, data):
    if data is None:
        print(f'{label}: ABSENT')
    else:
        print(f'{label}: UUID={data["UUID"]} Received UUID={data["Received UUID"]} Flags={data["Flags"]}')

def identity(obj):
    check(type(obj) is dict and set(obj) == {'timestamp', 'uuid'} and
          isinstance(obj['timestamp'], str) and STAMP.fullmatch(obj['timestamp']) and
          isinstance(obj['uuid'], str) and UUID.fullmatch(obj['uuid']),
          'Unexpected journal parent/candidate identity')
    return obj

def read_journal():
    safe_dir(STATE)
    check(not JOURNAL.is_symlink() and JOURNAL.is_file(), 'Missing/unsafe journal')
    fd = os.open(JOURNAL, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        st = os.fstat(stream.fileno())
        check(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and st.st_uid == REQUIRED_OWNER_UID and
              stat.S_IMODE(st.st_mode) == 0o600 and 0 < st.st_size <= 65536,
              'Unsafe journal ownership, links, mode or size')
        content = stream.read(65537)
    value = json.loads(content)
    check(type(value) is dict and value.get('schema') == 1 and
          set(value) <= {'schema', 'status', 'parent', 'candidate', 'nonce',
                         'scope_unit', 'scope_binding', 'receiver_boot_id',
                         'staging', 'publication_witness'} and
          value.get('status') == 'receiving' and
          isinstance(value.get('nonce'), str) and NONCE.fullmatch(value['nonce']),
          'Unexpected journal format')
    parent, candidate = identity(value.get('parent')), identity(value.get('candidate'))
    check(parent['timestamp'] < candidate['timestamp'], 'Journal does not advance parent')
    print(f'Journal: root 0600, bytes={len(content)}, sha256={hashlib.sha256(content).hexdigest()}')
    print('Journal mtime UTC:', datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat())
    print(f'Journal: parent={parent} candidate={candidate}')
    print('Journal fields:', ', '.join(sorted(value)))
    return value, hashlib.sha256(content).hexdigest()

def marker_summary():
    for name in ('.agreed-parent-transfer-pending.json',
                 '.receiver-prune-pending.json', '.agreed-parent-provisional.json'):
        p = STATE / name
        print(f'Legacy marker {name}: {"PRESENT" if p.exists() or p.is_symlink() else "ABSENT"}')

def simple(path):
    if path.is_symlink():
        raise Refuse('Symlinked simplified parent file')
    if not path.exists():
        print(f'Simplified parent {path}: ABSENT (expected before bootstrap)')
        return
    check(path.is_file(), 'Non-file simplified parent')
    st = path.stat()
    check(st.st_uid == REQUIRED_OWNER_UID and stat.S_IMODE(st.st_mode) == 0o600,
          'Unexpected simplified parent file permissions')
    value = json.loads(path.read_text())
    print(f'Simplified parent {path}: {value}')

def read_accepted_receipt(value):
    """Validate the *published* legacy candidate receipt without changing it.

    The old receiver's `receipt()` acceptance contract is reproduced here,
    plus the journal's exact parent lineage. Avoid importing the retired
    receiver (which has operational side effects and different privileges).
    """
    candidate, parent = value['candidate'], value['parent']
    stamp, uuid = candidate['timestamp'], candidate['uuid']
    receipt_path = STATE / (stamp + '.json')
    check(not receipt_path.is_symlink() and receipt_path.is_file(),
          'Completed candidate receipt missing/unsafe')
    fd = os.open(receipt_path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    with os.fdopen(fd, 'rb') as stream:
        st = os.fstat(stream.fileno())
        check(stat.S_ISREG(st.st_mode) and st.st_nlink == 1 and
              stat.S_IMODE(st.st_mode) == 0o600 and 0 < st.st_size <= 65536,
              'Completed candidate receipt ownership/mode/size unsafe')
        raw = stream.read(65537)
    receipt = json.loads(raw)
    check(type(receipt) is dict and receipt.get('schema') == 1 and
          receipt.get('transport') == 'btrfs-incremental' and
          receipt.get('snapshot') == stamp and
          receipt.get('source_uuid') == uuid and
          receipt.get('received_uuid') == uuid and
          receipt.get('source_filesystem_uuid') == SOURCE_FS and
          receipt.get('receiver_filesystem_uuid') == RECEIVER_FS and
          receipt.get('destination') == str(RECEIVER_ROOT / stamp) and
          receipt.get('read_only_verified') is True and
          receipt.get('source_send_exit') == 0 and
          receipt.get('receiver_receive_exit') == 0 and
          receipt.get('parent_snapshot') == parent['timestamp'] and
          receipt.get('parent_source_uuid') == parent['uuid'],
          'Completed candidate receipt does not match journal lineage and Btrfs transport')
    snapshot = info(RECEIVER_ROOT, stamp)
    check(snapshot is not None and snapshot['Flags'] == 'readonly' and
          snapshot['Received UUID'] == uuid,
          'Completed candidate Btrfs identity/read-only mismatch')
    return hashlib.sha256(raw).hexdigest()


def journal_details(value):
    candidate = value['candidate']
    brief('Receiver journal parent', info(RECEIVER_ROOT, value['parent']['timestamp']))
    candidate_info = info(RECEIVER_ROOT, candidate['timestamp'])
    brief('Receiver journal candidate', candidate_info)
    receipt = STATE / (candidate['timestamp'] + '.json')
    has_receipt = receipt.exists() or receipt.is_symlink()
    print('Journal candidate receipt:', 'PRESENT' if has_receipt else 'ABSENT')
    if candidate_info is not None and has_receipt:
        digest = read_accepted_receipt(value)
        print('Candidate and accepted legacy receipt: VERIFIED (readonly, exact parent lineage)')
        print('Candidate receipt sha256:', digest)
    elif candidate_info is not None or has_receipt:
        print('Candidate/receipt classification: INCOMPLETE OR MISMATCHED; archive prohibited')
    else:
        print('Candidate/receipt classification: BOTH ABSENT')
    stage = RECEIVER_ROOT / ('.receive-' + value['nonce'])
    sidecar = STATE / ('.agreed-parent-stage-ownership-' + value['nonce'] + '.json')
    print('Nonce-bound private staged object:', 'PRESENT' if stage.exists() or stage.is_symlink() else 'ABSENT')
    print('Nonce-bound ownership sidecar:', 'PRESENT' if sidecar.exists() or sidecar.is_symlink() else 'ABSENT')
    print('Staging bound:', 'staging' in value)
    print('Publication witnessed:', 'publication_witness' in value)
    return stage, sidecar, receipt

def audit(role):
    filesystem(role)
    root = SOURCE_ROOT if role == 'source' else RECEIVER_ROOT
    p = info(root, B)
    check(p is not None and p['Flags'] == 'readonly', f'Initial parent {B} missing/not read-only')
    if role == 'source':
        check(p['Received UUID'] == '-', 'Source parent is a received subvolume')
    else:
        check(UUID.fullmatch(p['Received UUID']) is not None, 'Receiver parent has no received UUID')
    brief('Proposed common parent ' + B, p)
    simple(SIMPLE_SOURCE if role == 'source' else SIMPLE_RECEIVER)
    if role == 'receiver':
        marker_summary()
        if JOURNAL.exists() or JOURNAL.is_symlink():
            value, digest = read_journal()
            journal_details(value)
            print('Archive candidate sha256:', digest)
    print('PASS: read-only ' + role + ' audit; no state changed')

def locked_file(stack, path):
    check(not path.is_symlink(), 'Symlink lock')
    fd = os.open(path, os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW)
    st = os.fstat(fd)
    check(stat.S_ISREG(st.st_mode), 'Unsafe lock object')
    stack.callback(os.close, fd)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        raise Refuse('Replication/snapshot lock busy; do not retire journal') from exc

def archive(expected_sha, expected_candidate, *, allow_completed=False, expected_receipt_sha=None):
    filesystem('receiver')
    safe_dir(STATE)
    with ExitStack() as stack:
        locked_file(stack, MANAGER)
        locked_file(stack, WRITER)
        check(not SIMPLE_RECEIVER.exists() and not SIMPLE_RECEIVER.is_symlink(),
              'Simplified receiver bootstrap already exists; stop for review')
        # A retired journal is not a general cleanup permission.
        for name in ('.receiver-prune-pending.json', '.agreed-parent-provisional.json'):
            other = STATE / name
            check(not other.exists() and not other.is_symlink(), 'Additional active legacy transaction')
        value, digest = read_journal()
        check(digest == expected_sha.lower(), 'Journal changed since audit')
        check(value['candidate']['timestamp'] == expected_candidate, 'Unexpected journal candidate')
        check('staging' not in value and 'publication_witness' not in value,
              'Staging/publication state requires separate review')
        check(info(RECEIVER_ROOT, B) is not None, 'Initial parent missing')
        common = info(RECEIVER_ROOT, B)
        check(common['Flags'] == 'readonly' and
              UUID.fullmatch(common['Received UUID']) is not None, 'Common parent not verified')
        stage, sidecar, receipt = journal_details(value)
        check(not any(p.exists() or p.is_symlink() for p in (stage, sidecar)),
              'Journal has an associated staged object or ownership record')
        candidate_path = RECEIVER_ROOT / expected_candidate
        has_candidate = candidate_path.exists() or candidate_path.is_symlink()
        has_receipt = receipt.exists() or receipt.is_symlink()
        if has_candidate or has_receipt:
            check(allow_completed, 'Journal candidate exists or has a receipt; explicit completed-candidate opt-in required')
            check(has_candidate and has_receipt, 'Completed candidate must have both snapshot and receipt')
            check(expected_candidate < B, 'Completed legacy candidate not older than initial agreed parent')
            check(expected_receipt_sha is not None and
                  NONCE.fullmatch(expected_receipt_sha.lower()),
                  'Exact audited receipt SHA-256 required for completed candidate')
            check(read_accepted_receipt(value) == expected_receipt_sha.lower(),
                  'Legacy receipt changed since audit')
        else:
            check(not allow_completed, 'Completed-candidate opt-in used with absent candidate')
        # The only mutation: rename a 0600 root-owned JSON file into a fixed
        # root-only rollback directory. No Btrfs data, receipt or state is deleted.
        if not ARCHIVE_DIR.exists():
            ARCHIVE_DIR.mkdir(mode=0o700)
        safe_dir(ARCHIVE_DIR)
        check(ARCHIVE_DIR.stat().st_uid == REQUIRED_OWNER_UID and
              stat.S_IMODE(ARCHIVE_DIR.stat().st_mode) == 0o700,
              'Archive directory not root-owned 0700')
        target = ARCHIVE_DIR / ('.agreed-parent-transfer-pending.' + digest + '.json')
        check(not target.exists() and not target.is_symlink(), 'Journal already archived')
        os.rename(JOURNAL, target)
        for directory in (STATE, ARCHIVE_DIR):
            dfd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                os.fsync(dfd)
            finally:
                os.close(dfd)
        check(not JOURNAL.exists() and target.is_file(), 'Archive readback failed')
        check(hashlib.sha256(target.read_bytes()).hexdigest() == digest,
              'Archived journal checksum changed')
        print('PASS: obsolete receiver journal archived; snapshots and parent files untouched')
        print('Rollback copy:', target)
        print('SHA256:', digest)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='action', required=True)
    a = sub.add_parser('audit', help='read-only endpoint state')
    a.add_argument('role', choices=['source', 'receiver'])
    r = sub.add_parser('archive', help='one guarded journal rename; backup only')
    r.add_argument('--expected-sha256', required=True)
    r.add_argument('--expected-candidate', required=True)
    r.add_argument('--allow-completed-candidate', action='store_true',
                   help='retire marker only when an older readonly candidate and valid receipt are verified')
    r.add_argument('--expected-receipt-sha256',
                   help='SHA-256 from the audited accepted candidate receipt (required with opt-in)')
    args = parser.parse_args()
    try:
        check(os.geteuid() == 0, 'Run as root via sudo -n')
        if args.action == 'audit':
            audit(args.role)
        else:
            check(re.fullmatch(r'[0-9a-fA-F]{64}', args.expected_sha256) is not None,
                  'Invalid expected SHA-256')
            check(STAMP.fullmatch(args.expected_candidate) is not None, 'Invalid expected candidate')
            archive(args.expected_sha256, args.expected_candidate,
                    allow_completed=args.allow_completed_candidate,
                    expected_receipt_sha=args.expected_receipt_sha256)
    except (OSError, Refuse, ValueError, KeyError, subprocess.CalledProcessError) as exc:
        print('FAIL: ' + str(exc), file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
