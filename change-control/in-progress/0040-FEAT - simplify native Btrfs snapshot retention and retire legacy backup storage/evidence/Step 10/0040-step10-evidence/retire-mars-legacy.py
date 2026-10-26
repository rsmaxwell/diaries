#!/usr/bin/env python3
"""0040-FEAT: one-time UUID/ID-guarded retirement of mars legacy @data Snapper history.

Default is read-only. This is not the periodic retention manager. Never targets native snapshots.
"""
import argparse
import contextlib
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

MANIFEST_SHA256 = '643c3dff637be45da4188f9991a2bddb27a8bb894d474aebd2318c5ebfa412b4'
MANAGER_CONFIG = Path('/etc/btrfs-snapshot-manager.json')
ROOT = Path('/media/usb/@data/.snapshots')
PATH_RE = re.compile(r'^/media/usb/@data/\.snapshots/([1-9][0-9]*)/snapshot$')
UUID_RE = re.compile(r'^\s*UUID:\s*([0-9a-f-]{36})\s*$', re.M)
ID_RE = re.compile(r'^\s*Subvolume ID:\s*([0-9]+)\s*$', re.M)
FILELIST_RE = re.compile(r'filelist-[0-9]+\.txt(?:\.gz)?\Z')
PROTECTED_FILES = ('/media/usb/@snapshots/.checkpoint-holds.json',
                   '/media/usb/@snapshots/.replication-protection.json')

class Stop(Exception):
    pass

def require(test, reason):
    if not test:
        raise Stop(reason)

def cmd(*args):
    p = subprocess.run(args, capture_output=True, text=True)
    require(p.returncode == 0, f'command failed: {args!r}: {p.stderr.strip()}')
    return p.stdout

def manifest_targets(raw):
    require(isinstance(raw, dict) and raw.get('feature') == '0040-FEAT' and
            raw.get('host') == 'mars' and raw.get('expected_count') == 17,
            'invalid manifest header')
    items = raw.get('targets')
    require(isinstance(items, list) and len(items) == 17, 'expected exactly 17 targets')
    result = {}
    ids = set()
    uuids = set()
    for t in items:
        require(isinstance(t, dict) and set(t) == {'path', 'uuid', 'subvolume_id', 'snapper_number'},
                'unexpected manifest target fields')
        path, uid, sid, number = (t[k] for k in ('path', 'uuid', 'subvolume_id', 'snapper_number'))
        require(isinstance(path, str) and PATH_RE.fullmatch(path) is not None, 'path outside retirement scope')
        require(type(number) is int and int(PATH_RE.fullmatch(path).group(1)) == number, 'Snapper number mismatch')
        require(type(sid) is int and sid > 0, 'invalid subvolume ID')
        require(isinstance(uid, str) and re.fullmatch(r'[0-9a-f-]{36}', uid) is not None, 'invalid UUID')
        require(path not in result and uid not in uuids and sid not in ids, 'duplicate target identity')
        result[path] = (uid, sid)
        ids.add(sid); uuids.add(uid)
    return result

def contents(path, *, present=True):
    directory = Path(path).parent
    require(not directory.is_symlink() and directory.is_dir(), 'unsafe Snapper metadata directory')
    expected = {'info.xml', 'snapshot'} if present else {'info.xml'}
    entries = {e.name: e for e in os.scandir(directory)}
    require(expected <= set(entries), 'missing expected Snapper metadata')
    extras = set(entries) - expected
    for name, entry in entries.items():
        mode = entry.stat(follow_symlinks=False).st_mode
        if name == 'snapshot' and present:
            require(stat.S_ISDIR(mode), 'unexpected snapshot entry')
        elif name == 'info.xml':
            require(stat.S_ISREG(mode), 'unexpected info.xml')
        else:
            require(name in extras and FILELIST_RE.fullmatch(name) is not None and stat.S_ISREG(mode),
                    'unexpected Snapper directory contents')
    root = ET.parse(directory / 'info.xml').getroot()
    require(root.tag == 'snapshot' and root.findtext('num') == PATH_RE.fullmatch(path).group(1),
            'Snapper metadata ID mismatch')
    return sorted(extras)

def identity(path, expected):
    require(PATH_RE.fullmatch(path) is not None, 'invalid path')
    require(not Path(path).is_symlink(), 'symlink candidate')
    extras = contents(path)
    output = cmd('btrfs', 'subvolume', 'show', path)
    uuid, sid = UUID_RE.search(output), ID_RE.search(output)
    require(uuid is not None and sid is not None and (uuid.group(1), int(sid.group(1))) == expected,
            f'live UUID/subvolume ID mismatch: {path}')
    require(re.search(r'^\s*Received UUID:\s*-\s*$', output, re.M) is not None,
            'received snapshot not eligible')
    return extras

def live_inventory():
    output = cmd('btrfs', 'subvolume', 'list', '-u', '/media/usb')
    result = {}
    for line in output.splitlines():
        if ' path @data/.snapshots/' not in line:
            continue
        m = re.fullmatch(r'ID ([0-9]+) gen [0-9]+ top level [0-9]+ uuid ([0-9a-f-]{36}) path (@data/\.snapshots/[0-9]+/snapshot)', line)
        require(m is not None, f'unrecognised legacy subvolume: {line}')
        path = '/media/usb/' + m.group(3)
        require(PATH_RE.fullmatch(path) and path not in result, 'invalid/duplicate legacy path')
        result[path] = (m.group(2), int(m.group(1)))
    return result

def sha(path):
    p = Path(path)
    require(p.is_file() and not p.is_symlink(), f'missing or symlinked protection file: {path}')
    return hashlib.sha256(p.read_bytes()).hexdigest()

def guard_configuration(config):
    require(isinstance(config, dict) and config.get('snapshot_root') == '/media/usb/@snapshots',
            'unexpected source configuration')
    require(config.get('lock_path') == '/run/lock/btrfs-snapshot-manager.lock', 'unexpected manager lock')
    require(config.get('writer_lock_path') == '/media/usb/@data/backup/.btrfs-snapshot-writer.lock',
            'unexpected writer lock')
    require(config.get('creation_source_names') == ['root', '@data'] and
            config.get('required_snapshot_sources') == ['root', '@data'],
            'native source contract changed')
    require({s.get('name'): s.get('path') for s in config.get('sources', [])} ==
            {'root': '/media/usb', '@data': '/media/usb/@data'}, 'unexpected snapshot sources')
    require(config.get('checkpoint_holds', {}).get('required') is True and
            config.get('replication_protection', {}).get('required') is True,
            'native protection no longer required')

@contextlib.contextmanager
def manager_lock(config):
    path = config['lock_path']
    fd = os.open(path, os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC)
    try:
        st = os.fstat(fd)
        require(stat.S_ISREG(st.st_mode) and st.st_nlink == 1, 'unsafe manager lock')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as e:
            raise Stop('snapshot manager busy') from e
        yield
    finally:
        os.close(fd)

def approval_ok(path, manifest_checksum):
    p = Path(path)
    require(not p.is_symlink(), 'approval symlink forbidden')
    st = p.stat()
    require(stat.S_ISREG(st.st_mode) and st.st_uid == 0 and not (st.st_mode & 0o022),
            'approval must be root-owned and not group/world-writable')
    policy = json.loads(p.read_text())
    require(type(policy) is dict and set(policy) == {'feature','host','manifest_sha256','allow_delete',
                                                      'accept_legacy_history_loss'}, 'unexpected approval fields')
    require(policy == {'feature': '0040-FEAT', 'host': 'mars', 'manifest_sha256': manifest_checksum,
                       'allow_delete': True, 'accept_legacy_history_loss': True},
            'explicit historical-recovery retirement approval absent')

def delete_one(path, expected):
    extras = identity(path, expected)
    require(identity(path, expected) == extras, 'candidate changed immediately before deletion')
    print(f'DELETE-BEGIN {path} UUID={expected[0]} ID={expected[1]}', flush=True)
    cmd('btrfs', 'subvolume', 'delete', path)
    require(not Path(path).exists(), f'deletion incomplete: {path}')
    require(contents(path, present=False) == extras, 'metadata changed after deletion')
    directory = Path(path).parent
    for name in extras + ['info.xml']:
        (directory / name).unlink()
    directory.rmdir()
    require(not directory.exists(), 'metadata directory still exists')
    print(f'DELETE-COMPLETE {path}', flush=True)

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', required=True)
    p.add_argument('--execute', action='store_true')
    p.add_argument('--approval-file', help='root-owned explicit historical recovery loss acceptance; required for execution')
    p.add_argument('--max-delete', type=int, default=1)
    a = p.parse_args(argv)
    require(os.geteuid() == 0 and os.uname().nodename.split('.')[0] == 'mars', 'run as root on mars only')
    require(1 <= a.max_delete <= 3, 'bounded batches must be 1..3')
    data = Path(a.manifest).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    require(digest == MANIFEST_SHA256, 'manifest checksum mismatch')
    targets = manifest_targets(json.loads(data))
    require(not a.execute or a.approval_file is not None, 'execution requires an approval file')
    if a.execute:
        approval_ok(a.approval_file, digest)
    config = json.loads(MANAGER_CONFIG.read_text())
    guard_configuration(config)
    with manager_lock(config):
        protected_before = {p: sha(p) for p in PROTECTED_FILES}
        live = live_inventory()
        require(set(live) <= set(targets), 'unexpected legacy numeric snapshot')
        for path in set(targets) - set(live):
            require(not Path(path).parent.exists(), f'incomplete earlier deletion: {path}')
        for path, actual in live.items():
            require(actual == targets[path], f'identity mismatch: {path}')
            identity(path, targets[path])
        print(f'PLAN approved=17 remaining={len(live)} completed={17-len(live)} '
              f'mode={"EXECUTE" if a.execute else "READ_ONLY"} max_delete={a.max_delete}', flush=True)
        if not a.execute:
            print('NO DELETION AUTHORISED', flush=True)
            return
        for path in sorted(live, key=lambda p: int(PATH_RE.fullmatch(p).group(1)))[:a.max_delete]:
            require({p: sha(p) for p in PROTECTED_FILES} == protected_before,
                    'native protection metadata changed')
            require(live_inventory().get(path) == targets[path], 'live target changed')
            delete_one(path, targets[path])
        require({p: sha(p) for p in PROTECTED_FILES} == protected_before,
                'native protection metadata changed during retirement')
        print(f'BATCH-COMPLETE remaining={len(live_inventory())}', flush=True)

if __name__ == '__main__':
    try:
        main()
    except (Stop, OSError, ValueError, ET.ParseError, KeyError, TypeError) as e:
        print(f'STOP: {e}', file=sys.stderr)
        sys.exit(2)
