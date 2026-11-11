#!/usr/bin/env python3
"""Compare 0045 static installed manifests without exposing protected file contents.

Usage: python3 compare-0045-installed-state.py BEFORE_DIR AFTER_DIR
The two directories must contain {mars,backup}-installed-static.json from the
same 0045 collector. Report keys/paths only; no secret values are printed.
This is one acceptance input, not a substitute for the full Step 3 review.
"""
import json
from pathlib import Path
import sys


GENERATED_DIR_NAMES = frozenset((
    '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.tox', '.nox',
))
GENERATED_FILE_NAMES = frozenset(('.DS_Store', '.coverage'))
SCRIPT_ROOTS = ('/root/scripts/backup/', '/home/richard/scripts/backup/')


def is_temporary_managed_key(path):
    """Narrow exclusion: discovered artifacts beneath script trees only.

    Never exclude explicitly managed paths elsewhere in the filesystem.
    """
    for root in SCRIPT_ROOTS:
        if not path.startswith(root):
            continue
        components = path[len(root):].split('/')
        if any(part in GENERATED_DIR_NAMES for part in components):
            return True
        name = components[-1]
        return (name in GENERATED_FILE_NAMES or name.startswith('.coverage.')
                or name.endswith(('.pyc', '.pyo', '.swp', '.swo', '.tmp', '.temp', '~'))
                or (name.startswith('#') and name.endswith('#')))
    return False


def read(path, host):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if obj['schema'] != '0045-static-installed-v2' or obj['host'] != host:
        raise ValueError('Schema or host mismatch: ' + str(path))
    return obj



def proven_runtime_execstart_digest_only(unit, before, after, before_managed, after_managed):
    """Permit *only* a volatile systemd ExecStart execution-record difference.

    systemctl show ExecStart mixes stable commands with pid/start_time/stop_time/
    code/status from previous runs. The installed unit file, every scanned
    drop-in and all other loaded-unit properties must match precisely. This
    does NOT ignore an actual service definition, security or timer difference.
    """
    if not unit.endswith('.service') or not isinstance(before, dict) or not isinstance(after, dict):
        return False
    key = 'ExecStartSHA256'
    if not (isinstance(before.get(key), str) and isinstance(after.get(key), str)):
        return False
    if len(before[key]) != 64 or len(after[key]) != 64 or before[key] == after[key]:
        return False
    if not all(ch in '0123456789abcdef' for ch in before[key] + after[key]):
        return False
    b, a = dict(before), dict(after)
    b.pop(key)
    a.pop(key)
    if b != a or b.get('LoadState') != 'loaded':
        return False
    path = '/etc/systemd/system/' + unit
    if b.get('FragmentPath') != path:
        return False
    installed_before = before_managed.get(path)
    installed_after = after_managed.get(path)
    if (not isinstance(installed_before, dict)
            or installed_before.get('type') != 'file'
            or not installed_before.get('sha256')
            or installed_before != installed_after):
        return False
    dropin_root = path + '.d'
    # The collector includes metadata for the .d directory and every file in it.
    covered_paths = (set(before_managed) | set(after_managed))
    for candidate in covered_paths:
        if candidate == dropin_root or candidate.startswith(dropin_root + '/'):
            if before_managed.get(candidate) != after_managed.get(candidate):
                return False
    # Every systemd-loaded drop-in must be present in the captured managed set.
    dropins = b.get('DropInPaths', '').split()
    if any(not (item.startswith(dropin_root + '/') and item in before_managed
                and item in after_managed) for item in dropins):
        return False
    return True

def main():
    if len(sys.argv) != 3:
        print('Usage: compare-0045-installed-state.py BEFORE_DIR AFTER_DIR', file=sys.stderr)
        return 2
    before, after = map(Path, sys.argv[1:])
    failed = False
    for host in ('mars', 'backup'):
        old = read(before / f'{host}-installed-static.json', host)
        new = read(after / f'{host}-installed-static.json', host)
        differences = []
        for section in ('managed', 'mutable_state_metadata', 'packages', 'systemd_units', 'cron', 'acl', 'mount'):
            old_items = old[section]
            new_items = new[section]
            for key in sorted(set(old_items) | set(new_items)):
                if section == 'managed' and is_temporary_managed_key(key):
                    continue  # Python/test/editor artifacts are not installed assets.
                before_item = old_items.get(key)
                after_item = new_items.get(key)
                if before_item != after_item:
                    if (section == 'systemd_units' and proven_runtime_execstart_digest_only(
                            key, before_item, after_item, old['managed'], new['managed'])):
                        print('RECONCILED:', host, 'systemd_units:' + key,
                              '(ExecStart execution-history digest only; '
                              'installed unit, drop-ins and loaded properties unchanged)')
                        continue
                    differences.append(f'{section}:{key}')
        if differences:
            failed = True
            print(f'FAIL: {host} {len(differences)} static installation differences')
            for key in differences:
                print('  DIFFERENCE:', key)
        else:
            print(f'PASS: {host} static installation fingerprint identical')
    if failed:
        return 1
    print('PASS: Both hosts static fingerprints identical; review runtime and source-to-destination coverage separately')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('FAIL: cannot compare 0045 manifests:', str(exc), file=sys.stderr)
        sys.exit(2)
