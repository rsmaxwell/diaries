#!/usr/bin/env python3
"""0045 read-only static installation fingerprint. Run via sudo -n python3 - on mars/backup.

Outputs no file contents, secret values or mutable Btrfs state. Hashes for managed
configuration and raw POSIX ACL xattrs only; requires no getfacl executable.
Does not traverse backup data or snapshot/state directories.
V2 adds package versions, directory metadata, loaded unit command digests and
metadata-only checks for selected mutable protection/lock files.
"""
import datetime
import errno
import hashlib
import json
import os
import pwd
import stat
import subprocess
import sys

UNIT_NAMES = [
    'diaries-pull.service', 'diaries-pull.timer',
    'btrfs-snapshot-create.service', 'btrfs-snapshot-create.timer',
    'btrfs-snapshot-prune.service', 'btrfs-snapshot-prune.timer',
    'btrfs-native-push.service', 'btrfs-native-push.timer',
    'btrfs-receiver-simple-prune.service', 'btrfs-receiver-simple-prune.timer',
    'btrfs-clear-stale-qgroups.service', 'btrfs-clear-stale-qgroups.timer',
]
MANAGED_FILES = [
    '/usr/local/sbin/btrfs-snapshot-manager',
    '/usr/local/sbin/btrfs-clear-stale-qgroups',
    '/usr/local/sbin/diaries-backup-history',
    '/usr/local/sbin/diaries-backup-status',
    '/usr/local/sbin/btrfs-extent-sharing',
    '/usr/local/sbin/btrfs-qgroup-audit',
    '/usr/local/sbin/assess-qgroup-safety',
    '/usr/local/sbin/diaries-snapshot-cleanup',
    '/usr/local/bin/btrfs-simplified-replication',
    '/usr/local/lib/diaries-backup/complete-dataset-manifest.py',
    '/etc/btrfs-snapshot-manager.json',
    '/etc/btrfs-receiver-retention.json',
    '/etc/btrfs-stale-qgroups.json',
    '/etc/sudoers.d/diaries-native-btrfs',
    '/etc/sudoers.d/diaries-agreed-parent-observer',
    '/usr/local/bin/btrfs-native-pull',
    '/usr/local/libexec/whole-backup-pull.py',
] + ['/etc/systemd/system/' + unit for unit in UNIT_NAMES]
# Static path inventory only: never recurse through the live Btrfs dataset.
STATIC_DIRECTORIES = [
    '/usr/local/libexec', '/usr/local/lib/diaries-backup',
    '/root/log/backup', '/home/richard/log/backup',
    '/media/usb', '/media/usb/@data', '/media/usb/@data/backup',
    '/media/usb/@data/backup/pluto', '/media/usb/@snapshots',
    '/media/usb/@snapshots/@data',
    '/@data/mars-received', '/@data/mars-received/@data',
    '/@data/mars-received/.replication-state',
]
# Preserve the metadata of existing state, never its mutable file content.
STATE_METADATA_PATHS = [
    '/media/usb/@data/backup/.btrfs-snapshot-writer.lock',
    '/media/usb/@snapshots/.checkpoint-holds.json',
    '/media/usb/@snapshots/.replication-protection.json',
    '/@data/mars-received/.replication-state/writer.lock',
    '/etc/btrfs-receiver-checkpoint-holds.json',
]
REQUIRED_PACKAGES = [
    'acl', 'btrfs-progs', 'cron', 'jq', 'python3', 'rsync',
    'sudo', 'systemd', 'tree', 'unzip', 'zip',
]
SCRIPT_ROOTS = ['/root/scripts/backup', '/home/richard/scripts/backup']
MAX_STATIC_FILE = 32 * 1024 * 1024


# Only ignore disposable artifacts *inside scanned backup script trees*.
# Explicitly listed managed programs, configuration and unit files are never filtered.
GENERATED_DIR_NAMES = frozenset((
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox', '.nox',
))
GENERATED_FILE_NAMES = frozenset(('.DS_Store', '.coverage'))


def is_generated_artifact(name, is_dir=False):
    if is_dir:
        return name in GENERATED_DIR_NAMES
    return (name in GENERATED_FILE_NAMES or name.startswith('.coverage.')
            or name.endswith(('.pyc', '.pyo', '.swp', '.swo', '.tmp', '.temp', '~'))
            or (name.startswith('#') and name.endswith('#')))


def sha_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def one_path(path):
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return {'present': False}
    result = {
        'present': True, 'uid': st.st_uid, 'gid': st.st_gid,
        'mode': f'{stat.S_IMODE(st.st_mode):04o}',
    }
    if stat.S_ISLNK(st.st_mode):
        result.update(type='symlink', target=os.readlink(path))
    elif stat.S_ISDIR(st.st_mode):
        result.update(type='directory')
    elif stat.S_ISREG(st.st_mode):
        result.update(type='file', size=st.st_size)
        if st.st_size > MAX_STATIC_FILE:
            raise RuntimeError(f'Unexpected large managed program file: {path}')
        result['sha256'] = sha_file(path)
    else:
        result.update(type='other')
    return result


def metadata_only(path):
    """Capture presence/type/owner/mode, without hashing mutable state contents."""
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {'present': False}
    if stat.S_ISLNK(info.st_mode):
        kind = 'symlink'
    elif stat.S_ISDIR(info.st_mode):
        kind = 'directory'
    elif stat.S_ISREG(info.st_mode):
        kind = 'file'
    else:
        kind = 'other'
    return {
        'present': True,
        'type': kind,
        'uid': info.st_uid,
        'gid': info.st_gid,
        'mode': f'{stat.S_IMODE(info.st_mode):04o}',
    }


def run(command):
    try:
        p = subprocess.run(command, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError('Metadata command failed: ' + command[0]) from exc
    return p


def package_fingerprint(package):
    """Record installed package/version without emitting package configuration."""
    p = run(['dpkg-query', '-W', '-f=${Status}\t${Version}', package])
    if p.returncode != 0:
        if p.returncode == 1 and b'no packages found matching' in p.stderr.lower():
            return {'present': False}
        raise RuntimeError('Cannot inspect package ' + package +
                           ' (exit ' + str(p.returncode) + ')')
    # A configured-but-not-installed or unknown package may have an empty
    # Version field.  Preserve the trailing tab: str.strip() would delete it.
    parts = p.stdout.decode('utf-8', 'replace').rstrip('\r\n').split('\t', 1)
    if len(parts) != 2:
        raise RuntimeError('Unexpected package metadata format: ' + package)
    status, version = parts
    return {'present': status == 'install ok installed',
            'dpkg_status': status, 'version': version}


def cron_fingerprint(user):
    p = run(['crontab', '-l', '-u', user])
    if p.returncode == 0:
        return {'present': True, 'sha256': hashlib.sha256(p.stdout).hexdigest()}
    if b'no crontab for' in p.stderr.lower():
        return {'present': False}
    raise RuntimeError(f'Cannot inspect crontab for {user} (exit {p.returncode})')


def acl_fingerprint(path):
    """Read POSIX ACL metadata without relying on an installed getfacl binary.

    Use stable kernel ACL xattr bytes and the directory's base ownership/mode.
    A missing extended ACL is normal and must be distinguished from failure to
    read the metadata. Contents are hashed and are never printed or stored.
    """
    try:
        info = os.lstat(path)
    except FileNotFoundError:
        return {'present': False}
    if not stat.S_ISDIR(info.st_mode):
        raise RuntimeError(f'Expected ACL path to be a directory: {path}')
    extended = {}
    for name in ('system.posix_acl_access', 'system.posix_acl_default'):
        try:
            data = os.getxattr(path, name, follow_symlinks=False)
        except OSError as exc:
            if exc.errno in (errno.ENODATA, getattr(errno, 'ENOATTR', errno.ENODATA)):
                extended[name] = {'present': False}
            else:
                # EOPNOTSUPP, EACCES etc must not silently appear as 'no ACL'.
                raise RuntimeError(
                    f'Cannot inspect POSIX ACL xattr {name} at {path} '
                    f'(errno {exc.errno})'
                ) from exc
        else:
            extended[name] = {
                'present': True,
                'sha256': hashlib.sha256(data).hexdigest(),
                'size': len(data),
            }
    return {
        'present': True,
        'uid': info.st_uid,
        'gid': info.st_gid,
        'mode': f'{stat.S_IMODE(info.st_mode):04o}',
        'posix_acl_xattrs': extended,
    }


def unit_state(name):
    p = run(['systemctl', 'show', name,
             '--property=LoadState,UnitFileState,ActiveState,ExecStart,User,Group,FragmentPath,DropInPaths',
             '--no-pager'])
    if p.returncode:
        raise RuntimeError(f'Cannot inspect systemd unit {name}')
    fields = {}
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
    # Service ActiveState is transient (oneshot jobs run while being sampled).
    # Timer ActiveState is part of the stable installation contract.
    if name.endswith('.service'):
        fields.pop('ActiveState', None)
    # Do not disclose potentially sensitive ExecStart command arguments.
    if 'ExecStart' in fields:
        fields['ExecStartSHA256'] = hashlib.sha256(fields.pop('ExecStart').encode()).hexdigest()
    # Calendar is non-sensitive. Ignore last/next elapse, which naturally changes.
    path = '/etc/systemd/system/' + name
    if name.endswith('.timer') and os.path.isfile(path):
        calendar = {}
        with open(path, 'r', encoding='utf-8', errors='replace') as stream:
            for line in stream:
                stripped = line.strip()
                for key in ('OnCalendar', 'Persistent', 'AccuracySec'):
                    if stripped.startswith(key + '='):
                        calendar.setdefault(key, []).append(stripped.split('=', 1)[1])
        fields['schedule'] = calendar
    return fields


def main():
    if os.geteuid() != 0:
        raise RuntimeError('Requires root for read-only metadata access (sudo -n)')
    hostname = os.uname().nodename.split('.')[0]
    if hostname not in ('mars', 'backup'):
        raise RuntimeError('Unexpected host; expected mars or backup')
    managed = {path: one_path(path) for path in MANAGED_FILES}
    for path in STATIC_DIRECTORIES:
        managed[path] = one_path(path)
    state_metadata = {path: metadata_only(path) for path in STATE_METADATA_PATHS}
    for root in SCRIPT_ROOTS:
        managed[root] = one_path(root)
        if managed[root]['present']:
            if managed[root].get('type') != 'directory':
                raise RuntimeError('Managed script root is not a directory: ' + root)
            for base, dirs, files in os.walk(root, followlinks=False):
                # Exclude disposable Python/test/editor artifacts from scanned
                # script trees, but retain all explicitly managed install paths.
                dirs[:] = sorted(d for d in dirs if not is_generated_artifact(d, is_dir=True))
                files.sort()
                if base != root:
                    managed[base] = one_path(base)
                for name in dirs:
                    p = os.path.join(base, name)
                    if os.path.islink(p):
                        managed[p] = one_path(p)
                for name in files:
                    p = os.path.join(base, name)
                    if is_generated_artifact(name):
                        continue  # Disposable runtime/editor artifact.
                    managed[p] = one_path(p)
    for unit in UNIT_NAMES:
        dropin = '/etc/systemd/system/' + unit + '.d'
        managed[dropin] = one_path(dropin)
        if os.path.isdir(dropin) and not os.path.islink(dropin):
            for name in sorted(os.listdir(dropin)):
                managed[dropin + '/' + name] = one_path(dropin + '/' + name)
    acl_path = '/media/usb/@data/backup' if hostname == 'mars' else '/@data/mars-received'
    mount_path = '/media/usb' if hostname == 'mars' else '/'
    mount = run(['findmnt', '-M', mount_path, '--noheadings', '--output', 'SOURCE,FSTYPE,OPTIONS'])
    if mount.returncode:
        raise RuntimeError('Unable to inspect required filesystem mount at ' + mount_path)
    # Cron and ACL values are represented by digests, never their contents.
    result = {
        'schema': '0045-static-installed-v2',
        'host': hostname,
        'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'managed': managed,
        'mutable_state_metadata': state_metadata,
        'packages': {name: package_fingerprint(name) for name in REQUIRED_PACKAGES},
        'systemd_units': {unit: unit_state(unit) for unit in UNIT_NAMES},
        'cron': {'root': cron_fingerprint('root'), 'richard': cron_fingerprint('richard')},
        'acl': {acl_path: acl_fingerprint(acl_path)},
        'mount': {mount_path: mount.stdout.decode('utf-8', 'replace').strip()},
    }
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print('FAIL: 0045 managed-host fingerprint: ' + str(exc), file=sys.stderr)
        sys.exit(1)
