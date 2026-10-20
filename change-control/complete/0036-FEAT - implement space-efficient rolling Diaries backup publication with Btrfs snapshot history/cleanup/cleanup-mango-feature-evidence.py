#!/usr/bin/env python3
"""Safely remove mango's 0034/0036 evidence ONLY if identical to a verified archive.

Default is a dry run. --apply requires an interactive typed confirmation.
No network access, no sudo, and no changes to mars/backup.
"""
import argparse
import hashlib
import os
from pathlib import Path, PurePosixPath
import stat
import sys
import tarfile

LABEL = 'closed-0034-0036-evidence-20261018'
CHECKPOINT = '20261018-165453Z'


def error(message):
    raise RuntimeError(message)


def sha256(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def allowed(name):
    return (name.startswith('0034-step11-1-mango-') or
            name == '0036-gateb-evidence' or
            name.startswith('0036-gate-d-evidence') or
            name.startswith('0036-gate-e-'))


def clean_path(name):
    if name.startswith('/') or '\\' in name:
        error(f'Unsafe archive path: {name}')
    parts = PurePosixPath(name).parts
    if not parts or any(part in ('..', '.') for part in parts):
        error(f'Unsafe archive path: {name}')
    if not allowed(parts[0]):
        error(f'Unexpected top-level archive path: {name}')
    return parts


def archive_inventory(tf):
    items = {}
    roots = set()
    for member in tf:
        parts = clean_path(member.name.rstrip('/'))
        rel = '/'.join(parts)
        if rel in items:
            error(f'Duplicate archive entry: {rel}')
        if not (member.isfile() or member.isdir()):
            error(f'Refusing archive links/special entry: {rel}')
        items[rel] = member
        roots.add(parts[0])
    if not items:
        error('Empty archive')
    if len(roots) < 2 or not any(r.startswith('0034-') for r in roots) or not any(r.startswith('0036-') for r in roots):
        error('Expected both 0034 and 0036 archive entries')
    return items, sorted(roots)


def inspect_sources(home, tf, items, roots):
    actual = {}
    for root_name in roots:
        root = home / root_name
        if not root.exists() and not root.is_symlink():
            error(f'Missing original: {root}')
        if root.is_symlink():
            error(f'Refusing symlink: {root}')
        if root.is_file():
            actual[root_name] = root
            continue
        if not root.is_dir():
            error(f'Unexpected source type: {root}')
        for base, dirs, files in os.walk(root, followlinks=False):
            base_path = Path(base)
            for entry in [base_path] + [base_path / d for d in dirs] + [base_path / f for f in files]:
                if entry.is_symlink():
                    error(f'Refusing symlink in source: {entry}')
                if not (entry.is_file() or entry.is_dir()):
                    error(f'Refusing special filesystem entry: {entry}')
                actual[entry.relative_to(home).as_posix()] = entry

    if set(actual) != set(items):
        unexpected = sorted(set(actual) - set(items))
        missing = sorted(set(items) - set(actual))
        error(f'Source differs from archive manifest. Unexpected: {unexpected[:12]}; Missing: {missing[:12]}')

    checked_files = 0
    for rel, member in items.items():
        original = actual[rel]
        if member.isdir():
            if not original.is_dir():
                error(f'Expected directory: {original}')
        else:
            if not original.is_file() or original.stat().st_size != member.size:
                error(f'File missing/changed size: {original}')
            archived_stream = tf.extractfile(member)
            if archived_stream is None:
                error(f'Cannot read archived content: {rel}')
            archive_hash = hashlib.sha256()
            with archived_stream:
                for block in iter(lambda: archived_stream.read(1024 * 1024), b''):
                    archive_hash.update(block)
            if sha256(original) != archive_hash.hexdigest():
                error(f'Content changed since archiving: {original}')
            checked_files += 1
    return checked_files


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--apply', action='store_true', help='Delete verified originals after interactive confirmation')
    ap.add_argument('--home', type=Path, default=Path.home(), help='Source home directory (default: current user home)')
    args = ap.parse_args()
    home = args.home.expanduser().resolve()
    if args.apply and not sys.stdin.isatty():
        error('--apply requires an interactive terminal')
    if os.geteuid() == 0:
        error('Do not run as root')
    if home != Path.home().resolve():
        error('Refusing non-current home directory')
    archive_dir = home / 'feature-evidence-archive'
    archive = archive_dir / (LABEL + '.tar.gz')
    checksum_file = archive_dir / (LABEL + '.sha256')
    if not archive.is_file() or not checksum_file.is_file():
        error('Archive and checksum must both exist on mango')
    lines = checksum_file.read_text().strip().splitlines()
    if len(lines) != 1:
        error('Unexpected checksum-file format')
    parts = lines[0].split()
    if len(parts) != 2 or parts[1].lstrip('*') != archive.name or len(parts[0]) != 64:
        error('Unexpected checksum-file entry')
    verified_digest = sha256(archive)
    if verified_digest != parts[0].lower():
        error('Archive SHA-256 mismatch')
    with tarfile.open(archive, 'r:gz') as tf:
        items, roots = archive_inventory(tf)
        checked_files = inspect_sources(home, tf, items, roots)
    print(f'Archive SHA-256: {verified_digest}')
    print(f'Protected snapshot: {CHECKPOINT} (previously verified on backup)')
    print(f'Files content-matched: {checked_files}; archive entries: {len(items)}')
    print('Exactly matching top-level entries selected for cleanup:')
    for r in roots:
        print('  ' + r)
    if not args.apply:
        print('\nDRY RUN PASS: no files deleted. Run again with --apply only after reviewing the list.')
        return
    phrase = f'DELETE {len(roots)} VERIFIED ENTRIES'
    entered = input(f'\nTo permanently delete these originals from mango, type "{phrase}": ').strip()
    if entered != phrase:
        error('Confirmation mismatch; nothing deleted')
    # All files validated immediately before confirmation. Check again to limit race with accidental edits.
    with tarfile.open(archive, 'r:gz') as tf:
        items, roots = archive_inventory(tf)
        inspect_sources(home, tf, items, roots)
    # Delete only archive-enumerated files, deepest first, then empty directories.
    files = sorted((rel for rel, m in items.items() if m.isfile()), key=lambda x: (-x.count('/'), x))
    dirs = sorted((rel for rel, m in items.items() if m.isdir()), key=lambda x: (-x.count('/'), x))
    for rel in files:
        (home / rel).unlink()
    for rel in dirs:
        (home / rel).rmdir()  # refuses unexpected new entries
    print(f'CLEANUP COMPLETE: removed {len(roots)} archived source entries.')
    print('Archive, checksum, mars snapshot, and off-site received snapshot are untouched.')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, tarfile.TarError) as exc:
        print('ABORT: ' + str(exc), file=sys.stderr)
        sys.exit(1)
