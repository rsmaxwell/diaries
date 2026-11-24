#!/usr/bin/env python3
"""0028: read/copy only the approved rehearsal's original page scans.

The caller supplies a CSV exported from the isolated, already migrated DB.
All source files are read-only; staged copies and hashes are private evidence.
No network or SQL access; no writes outside the newly created destination.
"""
import argparse
import csv
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import sys

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp', '.tif', '.tiff'}
REQUIRED_HEADERS = ('diary_name', 'page_name', 'extension', 'page_id')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def safe_segment(segment, label):
    require(isinstance(segment, str) and segment != '', f'Empty {label}')
    require(segment not in ('.', '..') and '/' not in segment and '\\' not in segment,
            f'Unsafe {label}: {segment!r}')
    require(':' not in segment and not segment.startswith('.') and not segment.endswith((' ', '.')),
            f'Unsafe {label}: {segment!r}')
    require(not any(ord(c) < 32 or ord(c) == 127 for c in segment),
            f'Control character in {label}')
    return segment


def source_rows(path):
    with open(path, newline='', encoding='utf-8-sig') as fh:
        reader = csv.DictReader(fh)
        require(tuple(reader.fieldnames or ()) == REQUIRED_HEADERS,
                f'Unexpected page-list headings: {reader.fieldnames}')
        rows = []
        seen = set()
        for row in reader:
            diary = safe_segment(row['diary_name'], 'diary name')
            page = safe_segment(row['page_name'], 'page name')
            ext = row['extension']
            require(isinstance(ext, str) and ext.strip() == ext and ext,
                    'Blank or malformed page extension')
            ext = ext if ext.startswith('.') else '.' + ext
            require(ext.lower() in ALLOWED_EXTENSIONS,
                    f'Unsupported page scan extension: {ext}')
            page_id = int(row['page_id'])
            require(page_id > 0, 'Nonpositive Page ID')
            relative = Path(diary) / (page + ext)
            require((page_id, str(relative)) not in seen, 'Duplicate page record')
            seen.add((page_id, str(relative)))
            rows.append({'diary_name': diary, 'page_name': page,
                         'page_id': page_id, 'extension': ext,
                         'relative_path': relative.as_posix()})
    require(rows, 'No page scans to stage')
    require(len({r['page_id'] for r in rows}) == len(rows), 'Page ID reused with different path')
    require(len({r['relative_path'] for r in rows}) == len(rows), 'Page filename shared by distinct Page IDs')
    return rows


def file_sha(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def is_within(path, root):
    """Python 3.8-compatible containment of already canonicalised Paths.

    Both callers resolve the paths before calling this; a sibling whose
    name shares the source prefix is not treated as a descendant.
    """
    return path == root or root in path.parents


def ensure_regular_nonsymlink(path, source_root):
    require(not path.is_symlink(), f'Refusing source symlink {path}')
    resolved = path.resolve(strict=True)
    require(is_within(resolved, source_root), f'Source escaped root: {path}')
    require(path.is_file() and stat.S_ISREG(path.stat().st_mode), f'Not a regular source file: {path}')
    require(path.stat().st_size > 0, f'Empty source file: {path}')


def stage(rows, source_root, destination):
    source_root = source_root.resolve(strict=True)
    require(source_root.is_dir(), 'Original diary scan source root is not a directory')
    require(destination.exists() and destination.is_dir() and not any(destination.iterdir()),
            'Destination must be an existing EMPTY private staging directory')
    dest_real = destination.resolve()
    require(not is_within(dest_real, source_root) and not is_within(source_root, dest_real),
            'Source and destination must be distinct directories')
    # Fail before any copy if the NAS source is incomplete or contains an unsafe link.
    for row in rows:
        ensure_regular_nonsymlink(source_root / Path(row['relative_path']), source_root)
    files_root = destination / 'diaries'
    files_root.mkdir()
    results = []
    for row in rows:
        relative = Path(row['relative_path'])
        original = source_root / relative
        ensure_regular_nonsymlink(original, source_root)
        target = files_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        require(not target.exists(), f'Staged target unexpectedly exists: {target}')
        h = hashlib.sha256()
        with original.open('rb') as reader, target.open('xb') as writer:
            for chunk in iter(lambda: reader.read(1024 * 1024), b''):
                h.update(chunk)
                writer.write(chunk)
        digest = h.hexdigest()
        require(file_sha(original) == digest, f'Original changed during staging: {relative}')
        require(file_sha(target) == digest, f'Copied scan differs: {relative}')
        target.chmod(0o444)
        results.append({**row, 'bytes': target.stat().st_size, 'sha256': digest})
    result = {'status': 'PASS', 'original_page_count': len(rows),
              'source_unchanged': True, 'copies_independently_verified': True,
              'media_root': 'diaries', 'page_scans': results}
    (destination / 'STAGING-RESULT.PRIVATE.json').write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    with (destination / 'SHA256SUMS.txt').open('w', encoding='utf-8') as f:
        for item in results:
            f.write(f'{item["sha256"]}  diaries/{item["relative_path"]}\n')
    print(f'PASS: staged {len(rows)} independent, checksum-verified page scans; originals unchanged')
    return result


def check_existing(rows, destination):
    path = destination / 'STAGING-RESULT.PRIVATE.json'
    require(path.is_file(), 'Missing original scan staging result')
    result = json.loads(path.read_text(encoding='utf-8'))
    require(result.get('status') == 'PASS' and result.get('original_page_count') == len(rows),
            'Staging result mismatch')
    by_path = {r['relative_path']: r for r in result['page_scans']}
    require(set(by_path) == {r['relative_path'] for r in rows}, 'Original scan staging inventory drift')
    for row in rows:
        recorded = by_path[row['relative_path']]
        require(recorded['page_id'] == row['page_id'], 'Page ID drift')
        f = destination / 'diaries' / row['relative_path']
        require(f.is_file() and not f.is_symlink(), f'Staged page missing: {f}')
        require(file_sha(f) == recorded['sha256'], f'Staged page checksum drift: {f}')
    print(f'PASS: {len(rows)} existing staged page scans verified without copying again')
    return result


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--csv', required=True, type=Path)
    p.add_argument('--source', type=Path)
    p.add_argument('--destination', required=True, type=Path)
    p.add_argument('--check-existing', action='store_true')
    args = p.parse_args(argv)
    rows = source_rows(args.csv)
    if args.check_existing:
        check_existing(rows, args.destination)
    else:
        require(args.source is not None, '--source required for staging')
        stage(rows, args.source, args.destination)


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(f'FAIL: 0028 scan staging: {exc}', file=sys.stderr)
        sys.exit(1)
