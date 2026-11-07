#!/usr/bin/env python3
"""Archive superseded 0040 replication prototype tests from Playbooks to Diaries.

--plan is read-only.  --apply copies and checksum-verifies every candidate into
0040-FEAT/tests/retired-step12-3/, writes an archival manifest, then removes
only the verified source copies.  Git-tracked and locally modified tests are
eligible; staged changes are rejected.  No role executables or Btrfs data are
modified.  Run on mango from the synced Diaries feature tree.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

TEST_ROOT = Path('roles/btrfs-replication/tests')
KEEP = {
    'verify-0040-step12-3-shared-retention.py',
    'verify-0040-step12-3-privileged-delete-transfer-guard.py',
    'verify-0040-step12-3-receiver-consolidation.py',
    'verify-0040-step12-3-receiver-process-lifetime.py',
    'verify-0040-step12-parent-boundary.py',
}
REQUIRED = {
    'verify-0040-simplified-replication.py',
    'verify-0040-simplified-protection.py',
    'verify-0040-step12-3-shared-retention.py',
}
EXEC_EXTENSIONS = {'.py', '.sh', '.yaml', '.yml', '.j2', '.json'}


def retirement_group(name: str) -> str | None:
    if name in KEEP or name.startswith('verify-0040-simplified-'):
        return None
    if name.endswith('.py'):
        if name.startswith('verify-0040-step12-3-') or name.startswith('verify-0040-step12-3c-'):
            return 'superseded-step12-prototype'
        if name.startswith('verify-0040-agreed-parent-'):
            return 'superseded-agreed-parent-prototype'
        if name == 'verify-0040-step12-unattended-gateway.py':
            return 'superseded-step12-gateway'
    if name.endswith('.md') and name.startswith('README-0040-STEP12-3-'):
        return 'historical-step12-guide'
    if name in {
        '0040-INCREMENT-3E-ANSIBLE-RECEIVER-OBSERVER.md',
        '0040-INCREMENT-3G-RELEASE-GUARD.md',
        '0040-real-btrfs-staging-README.txt',
    }:
        return 'historical-linked-guide'
    return None


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(['git', '-C', str(repo), *args], capture_output=True,
                          text=True, check=check)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as src:
        for chunk in iter(lambda: src.read(128 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def assert_regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f'Unsafe nonregular/symlink source or archive: {path}')


def assert_safe_dirs(path: Path) -> None:
    for d in (path, *path.parents):
        if d.is_symlink():
            raise RuntimeError(f'Symlinked directory refused: {d}')


def scan_active_references(playbooks: Path, selected: set[str]) -> None:
    """Refuse dangling executable references outside files being retired."""
    violations = []
    excluded = {'.git', '__pycache__', '.venv', 'node_modules', '.tox'}
    for directory, dirs, files in os.walk(playbooks):
        dirs[:] = [d for d in dirs if d not in excluded and not (Path(directory) / d).is_symlink()]
        for name in files:
            path = Path(directory) / name
            if path.is_symlink() or path.suffix not in EXEC_EXTENSIONS:
                continue
            rel = path.relative_to(playbooks)
            if rel.parent == TEST_ROOT and name in selected:
                continue
            try:
                content = path.read_text(encoding='utf-8', errors='replace')
            except OSError as exc:
                raise RuntimeError(f'Cannot scan {rel}: {exc}') from exc
            for target in selected:
                if target in content:
                    violations.append(f'{rel} -> {target}')
    if violations:
        raise RuntimeError('Active executable references to retired tests:\n  ' +
                           '\n  '.join(violations[:30]))


def plan(playbooks: Path, feature: Path):
    root = playbooks / TEST_ROOT
    assert_safe_dirs(root)
    if not root.is_dir():
        raise RuntimeError(f'Missing test directory: {root}')
    if Path(git(playbooks, 'rev-parse', '--show-toplevel').stdout.strip()).resolve() != playbooks:
        raise RuntimeError(f'Unexpected Playbooks Git root: {playbooks}')
    branch = git(playbooks, 'branch', '--show-current').stdout.strip()
    revision = git(playbooks, 'rev-parse', 'HEAD').stdout.strip()
    if not branch:
        raise RuntimeError('Detached HEAD: inspect Playbooks checkout before retiring tests')
    for name in REQUIRED:
        p = root / name
        assert_regular(p)
    archive = feature / 'tests' / 'retired-step12-3'
    assert_safe_dirs(archive)
    records = []
    for p in sorted(root.iterdir()):
        group = retirement_group(p.name)
        if group is None:
            continue
        assert_regular(p)
        rel = p.relative_to(playbooks).as_posix()
        staged = git(playbooks, 'diff', '--cached', '--quiet', '--', rel, check=False).returncode
        if staged not in (0, 1):
            raise RuntimeError(f'Cannot inspect staged status: {rel}')
        if staged == 1:
            raise RuntimeError(f'Staged changes require reconciliation before removal: {rel}')
        tracked = git(playbooks, 'ls-files', '--error-unmatch', '--', rel, check=False).returncode == 0
        status = git(playbooks, 'status', '--short', '--', rel).stdout.strip()
        records.append({
            'path': rel,
            'archive': (Path('playbooks') / rel).as_posix(),
            'category': group,
            'sha256': sha256(p),
            'size_bytes': p.stat().st_size,
            'git_status_at_archive': status,
            'tracked_in_git': tracked,
        })
    scan_active_references(playbooks, {Path(r['path']).name for r in records})
    meta = {'branch': branch, 'revision': revision, 'archive_dir': archive,
            'records': records}
    return meta


def apply(playbooks: Path, feature: Path, meta: dict) -> None:
    records = meta['records']
    if not records:
        print('PASS: no eligible files remain')
        return
    archive = meta['archive_dir']
    assert_safe_dirs(archive)
    archive.mkdir(parents=True, exist_ok=True)
    manifest_path = archive / 'manifest.json'
    previous = []
    if manifest_path.exists() or manifest_path.is_symlink():
        assert_regular(manifest_path)
        doc = json.loads(manifest_path.read_text())
        if doc.get('schema') != 2 or not isinstance(doc.get('files'), list):
            raise RuntimeError('Existing manifest has another schema; review before proceeding')
        previous = doc['files']
    prior = {item['path']: item for item in previous}
    # All conflicts are checked before the first removal or archival copy.
    for rec in records:
        old = prior.get(rec['path'])
        if old is not None and old['sha256'] != rec['sha256']:
            raise RuntimeError(f'Archived version conflicts with source: {rec["path"]}')
        dst = archive / rec['archive']
        assert_safe_dirs(dst.parent)
        if dst.exists() or dst.is_symlink():
            assert_regular(dst)
            if sha256(dst) != rec['sha256']:
                raise RuntimeError(f'Archival bytes differ: {dst}')
    # Copy everything, then verify everything. No test is removed before this.
    for rec in records:
        src = playbooks / rec['path']
        if sha256(src) != rec['sha256']:
            raise RuntimeError(f'Source changed after plan: {src}')
        dst = archive / rec['archive']
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            shutil.copy2(src, dst)
    for rec in records:
        if sha256(archive / rec['archive']) != rec['sha256']:
            raise RuntimeError(f'Archive verification failed: {rec["archive"]}')
    merged = {**prior, **{item['path']: item for item in records}}
    doc = {
        'schema': 2,
        'purpose': '0040-FEAT historical superseded replication test preservation',
        'archived_utc': datetime.now(timezone.utc).isoformat(),
        'playbooks_branch': meta['branch'],
        'playbooks_head_revision': meta['revision'],
        'files': [merged[k] for k in sorted(merged)],
    }
    temp = manifest_path.with_suffix('.json.tmp')
    with temp.open('x', encoding='utf-8') as f:
        json.dump(doc, f, indent=2, sort_keys=True)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    temp.replace(manifest_path)
    for rec in records:
        src = playbooks / rec['path']
        # Immediately before unlink, recheck source identity.
        assert_regular(src)
        if sha256(src) != rec['sha256']:
            raise RuntimeError(f'Source changed during archival: {src}')
        src.unlink()
    print('PASS: archive verified and source copies retired:', len(records))
    print('ARCHIVE MANIFEST:', manifest_path)
    print('Keep the archive in Diaries 0040-FEAT; sync to Windows authoritative checkout.')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--playbooks', type=Path, default=Path('/home/richard/playbooks'))
    options = parser.add_mutually_exclusive_group()
    options.add_argument('--plan', action='store_true', help='read-only candidate inventory (default)')
    options.add_argument('--apply', action='store_true', help='archive exact bytes, verify then remove')
    parser.add_argument('--expect-count', type=int, help='required with --apply; must equal the reviewed plan count')
    args = parser.parse_args()
    playbooks = args.playbooks.expanduser().resolve(strict=True)
    feature = Path(__file__).resolve().parent.parent
    meta = plan(playbooks, feature)
    records = meta['records']
    print('PLAYBOOKS BRANCH:', meta['branch'])
    print('PLAYBOOKS REVISION:', meta['revision'])
    print('CANDIDATES:', len(records))
    print('GROUPS:', dict(Counter(r['category'] for r in records)))
    print('GIT STATUS:', dict(Counter('tracked' if r['tracked_in_git'] else 'untracked' for r in records)))
    print('ARCHIVE ROOT:', meta['archive_dir'])
    for rec in records:
        print(f"CANDIDATE {rec['path']} sha256={rec['sha256']} status={rec['git_status_at_archive']!r}")
    if args.apply:
        if args.expect_count is None or args.expect_count < 1:
            raise RuntimeError('--apply requires --expect-count N from the reviewed plan')
        if args.expect_count != len(records):
            raise RuntimeError(f'Candidate count changed: expected {args.expect_count}, found {len(records)}')
        apply(playbooks, feature, meta)
    else:
        print('PLAN ONLY: no files changed')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (RuntimeError, OSError, ValueError, subprocess.CalledProcessError, KeyError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
