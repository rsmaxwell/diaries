#!/usr/bin/env python3
"""0045 read-only static installation fingerprint. Run via sudo -n python3 - on mars/backup.

Outputs no file contents, secret values or mutable Btrfs state. Hashes for managed
configuration only; does not traverse backup data or snapshot/state directories.
"""
import datetime
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
SCRIPT_ROOTS = ['/root/scripts/backup', '/home/richard/scripts/backup']
MAX_STATIC_FILE = 32 * 1024 * 1024


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


def run(command):
    try:
        p = subprocess.run(command, capture_output=True, timeout=20, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RuntimeError('Metadata command failed: ' + command[0]) from exc
    return p


def cron_fingerprint(user):
    p = run(['crontab', '-l', '-u', user])
    if p.returncode == 0:
        return {'present': True, 'sha256': hashlib.sha256(p.stdout).hexdigest()}
    if b'no crontab for' in p.stderr.lower():
        return {'present': False}
    raise RuntimeError(f'Cannot inspect crontab for {user} (exit {p.returncode})')


def acl_fingerprint(path):
    if not os.path.lexists(path):
        return {'present': False}
    p = run(['getfacl', '-c', '--absolute-names', path])
    if p.returncode != 0:
        raise RuntimeError(f'Cannot inspect ACL of {path} (exit {p.returncode})')
    return {'present': True, 'sha256': hashlib.sha256(p.stdout).hexdigest()}


def unit_state(name):
    p = run(['systemctl', 'show', name, '--property=LoadState,UnitFileState,ActiveState', '--no-pager'])
    if p.returncode:
        raise RuntimeError(f'Cannot inspect systemd unit {name}')
    fields = {}
    for line in p.stdout.decode('utf-8', 'replace').splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            fields[k] = v
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
    for root in SCRIPT_ROOTS:
        managed[root] = one_path(root)
        if managed[root]['present']:
            if managed[root].get('type') != 'directory':
                raise RuntimeError('Managed script root is not a directory: ' + root)
            for base, dirs, files in os.walk(root, followlinks=False):
                dirs.sort()
                files.sort()
                if base != root:
                    managed[base] = one_path(base)
                for name in dirs:
                    p = os.path.join(base, name)
                    if os.path.islink(p):
                        managed[p] = one_path(p)
                for name in files:
                    p = os.path.join(base, name)
                    if name.endswith('.pyc') or name == '__pycache__':
                        continue  # Disposable runtime cache, not an installed asset.
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
        'schema': '0045-static-installed-v1',
        'host': hostname,
        'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'managed': managed,
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
