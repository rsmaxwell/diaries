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
                if old_items.get(key) != new_items.get(key):
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
