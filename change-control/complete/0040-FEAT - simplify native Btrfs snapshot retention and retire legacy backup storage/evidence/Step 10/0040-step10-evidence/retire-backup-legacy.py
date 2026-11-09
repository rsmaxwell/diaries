#!/usr/bin/env python3
"""0040 one-off, exact-manifest retirement of backup's numeric Snapper histories.

Run as root ON backup (e.g. via 'ssh backup sudo python3 -' from mango).
Never targets native received snapshots; does not call receiver-prune or alter config.
"""
import argparse
import fcntl
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import xml.etree.ElementTree as ET

EXPECTED_SHA256 = '1d25d3095b36fec8ce95cbab062ece9e2d5da2c72431c47eef78af0bbdfc1e64'
CONFIG = Path('/etc/btrfs-snapshot-manager.json')
ROOTS = ('/.snapshots', '/@data/.snapshots')
PATH_PATTERN = re.compile(r'^(/(?:\.snapshots|@data/\.snapshots)/([0-9]+)/snapshot)$')
UUID_PATTERN = re.compile(r'^\s*UUID:\s*([0-9a-f-]{36})\s*$', re.M)
ID_PATTERN = re.compile(r'^\s*Subvolume ID:\s*([0-9]+)\s*$', re.M)
FILELIST_PATTERN = re.compile(r'filelist-[0-9]+\.txt(?:\.gz)?')

class Stop(Exception):
    pass

def require(condition, message):
    if not condition:
        raise Stop(message)

def command(*args):
    p = subprocess.run(args, capture_output=True, text=True)
    if p.returncode:
        raise Stop(f'command failed ({p.returncode}): {args!r}; {p.stderr.strip()}')
    return p.stdout

def locks(config):
    lock = config.get('lock_path')
    writer = config.get('writer_lock_path')
    state = config.get('receiver_state_dir')
    require(lock == '/run/lock/btrfs-snapshot-manager.lock', 'unexpected manager lock')
    require(state == '/@data/mars-received/.replication-state', 'unexpected receiver state path')
    require(writer == state + '/writer.lock', 'unexpected writer lock')
    handles = []
    try:
        for name in (lock, writer):
            fd = os.open(name, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
            st = os.fstat(fd)
            require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, f'unsafe lock: {name}')
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise Stop(f'lock busy: {name}')
            handles.append(fd)
        return handles
    except BaseException:
        for fd in handles:
            os.close(fd)
        raise

def manifest_targets(raw):
    require(raw.get('feature') == '0040-FEAT' and raw.get('host') == 'backup', 'manifest identity mismatch')
    require(raw.get('expected_count') == 113, 'manifest count header mismatch')
    targets = raw.get('targets')
    require(isinstance(targets, list) and len(targets) == 113, 'manifest target count mismatch')
    result = {}
    uuids = set()
    for item in targets:
        require(isinstance(item, dict) and set(item) == {'path', 'uuid'}, 'unsafe manifest target')
        path, uuid = item['path'], item['uuid']
        require(isinstance(path, str) and isinstance(uuid, str), 'invalid manifest value')
        require(PATH_PATTERN.fullmatch(path) is not None, f'path outside approved legacy roots: {path}')
        require(re.fullmatch(r'[0-9a-f-]{36}', uuid) is not None, f'invalid uuid: {path}')
        require(path not in result and uuid not in uuids, 'duplicate manifest identity')
        result[path] = uuid
        uuids.add(uuid)
    return result

def exact_contents(directory, number, *, snapshot_expected=True):
    require(not directory.is_symlink() and directory.is_dir(), f'unsafe directory: {directory}')
    found = {e.name: e for e in os.scandir(directory)}
    required = {'info.xml', 'snapshot'} if snapshot_expected else {'info.xml'}
    require(required <= set(found), f'missing required entries: {directory}')
    extras = set(found) - required
    for name, entry in found.items():
        mode = entry.stat(follow_symlinks=False).st_mode
        if name == 'snapshot' and snapshot_expected:
            require(stat.S_ISDIR(mode), f'unsafe snapshot: {entry.path}')
        elif name == 'info.xml':
            require(stat.S_ISREG(mode), f'unsafe info.xml: {entry.path}')
        else:
            require(name in extras and FILELIST_PATTERN.fullmatch(name) is not None and stat.S_ISREG(mode),
                    f'unexpected entry: {entry.path}')
    root = ET.parse(directory / 'info.xml').getroot()
    require(root.tag == 'snapshot' and root.findtext('num') == number, f'metadata number mismatch: {directory}')
    return sorted(extras)

def inspect(path, expected_uuid):
    match = PATH_PATTERN.fullmatch(path)
    require(match is not None, f'path outside scope: {path}')
    number = match.group(2)
    directory = Path(path).parent
    extras = exact_contents(directory, number)
    require(not Path(path).is_symlink(), f'symlink target: {path}')
    info = command('btrfs', 'subvolume', 'show', path)
    uuid = UUID_PATTERN.search(info)
    sid = ID_PATTERN.search(info)
    require(uuid is not None and sid is not None and uuid.group(1) == expected_uuid,
            f'UUID/subvolume identity mismatch: {path}')
    require(re.search(r'^\s*Received UUID:\s*-\s*$', info, re.M) is not None,
            f'not an ordinary legacy snapshot: {path}')
    return sid.group(1), extras

def live_inventory():
    raw = command('btrfs', 'subvolume', 'list', '-u', '/')
    matches = {}
    for line in raw.splitlines():
        match = re.search(r'\buuid ([0-9a-f-]{36}) path ((?:\.snapshots|@data/\.snapshots)/[0-9]+/snapshot)$', line)
        if match:
            path = '/' + match.group(2)
            require(path not in matches, 'duplicate live snapshot path')
            matches[path] = match.group(1)
    return matches

def recovery_clean():
    output = command('btrfs-snapshot-manager', 'receiver-recovery-plan')
    require('"state": "CLEAN"' in output and '"authorizes_repair": false' in output,
            'receiver recovery is not CLEAN')

def execute_one(path, expected):
    before_id, extras = inspect(path, expected)
    # Repeat immediately before mutation to detect replacement.
    again_id, again_extras = inspect(path, expected)
    require((again_id, again_extras) == (before_id, extras), 'candidate changed before deletion')
    print(f'DELETE-BEGIN {path} UUID={expected} ID={before_id}', flush=True)
    command('btrfs', 'subvolume', 'delete', path)
    require(not Path(path).exists(), f'snapshot path remains after deletion: {path}')
    directory = Path(path).parent
    number = PATH_PATTERN.fullmatch(path).group(2)
    require(exact_contents(directory, number, snapshot_expected=False) == extras,
            f'unexpected metadata change: {directory}')
    # No recursive delete. Remove exact verified files, then require empty directory.
    for name in extras + ['info.xml']:
        (directory / name).unlink()
    directory.rmdir()
    require(not directory.exists(), f'directory remains: {directory}')
    print(f'DELETE-COMPLETE {path} UUID={expected}', flush=True)

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--manifest', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--max-delete', type=int, default=5)
    args = p.parse_args()
    require(os.geteuid() == 0, 'must run as root on backup')
    require(os.uname().nodename.split('.')[0] == 'backup', 'host must be backup')
    require(1 <= args.max_delete <= 20, 'max-delete must be 1..20')
    data = Path(args.manifest).read_bytes()
    require(hashlib.sha256(data).hexdigest() == EXPECTED_SHA256, 'manifest checksum mismatch')
    targets = manifest_targets(json.loads(data))
    config = json.loads(CONFIG.read_text())
    require(config.get('mode') == 'receiver' and config.get('receiver_prune_enabled') is False,
            'receiver safeguards not in expected state')
    # Recovery command acquires these same locks: run before, never while held.
    recovery_clean()
    fds = locks(config)
    try:
        current = live_inventory()
        require(set(current) <= set(targets), f'unapproved numeric snapshots exist: {set(current)-set(targets)}')
        missing = sorted(set(targets)-set(current))
        # Two pilot deletions are excluded from the manifest; all others must either
        # still exist or have fully disappeared (including their metadata directory).
        for path in missing:
            require(not Path(path).parent.exists(), f'incomplete earlier deletion: {path}')
        for path, uuid in current.items():
            require(targets[path] == uuid, f'live UUID mismatch: {path}')
        for path in sorted(current):
            inspect(path, targets[path])
        print(f'PLAN approved=113 remaining={len(current)} completed={len(missing)} '
              f'mode={"EXECUTE" if args.execute else "READ_ONLY"} max_delete={args.max_delete}', flush=True)
        if not args.execute:
            print('NO DELETION AUTHORISED', flush=True)
            return
        for path in sorted(current)[:args.max_delete]:
            execute_one(path, targets[path])
        print(f'BATCH-COMPLETE deleted={min(args.max_delete, len(current))} '
              f'remaining={len(live_inventory())}', flush=True)
    finally:
        for fd in reversed(fds):
            os.close(fd)
    recovery_clean()

if __name__ == '__main__':
    try:
        main()
    except (Stop, OSError, ValueError, ET.ParseError, KeyError) as exc:
        print(f'STOP: {exc}', file=sys.stderr)
        sys.exit(2)
