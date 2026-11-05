#!/usr/bin/env python3
"""Safely archive and retire obsolete 0040 Step 12 prototype verification scripts.

Run from the Diaries parent repository checkout on mango, *not* from the
Playbooks repo; all evidence and archives remain in the Diaries feature tree.
Does not touch runtime files, Ansible tasks, timers or Btrfs snapshots.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime, timezone


ROLE_TESTS = Path('roles/btrfs-replication/tests')


def retired_name(name: str) -> bool:
    # New simplified replacement tests must use verify-0040-simplified-*
    # and must never be included in the historical prototype retirement.
    if name.startswith('verify-0040-simplified-'):
        return False
    return (
        (name.startswith('verify-0040-step12-3') and name.endswith('.py'))
        or (name.startswith('verify-0040-agreed-parent-') and name.endswith('.py'))
        or name in {
            'verify-0040-step12-parent-boundary.py',
            'verify-0040-step12-unattended-gateway.py',
        }
        or (name.startswith('README-0040-STEP12-3') and name.endswith('.md'))
        or (name.startswith('0040-STEP12-3') and name.endswith('.md'))
    )


def git(repo: Path, *argv: str) -> str:
    p = subprocess.run(
        ['git', '-C', str(repo), *argv], check=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
    )
    return p.stdout.strip()


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(128 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def ensure_regular(path: Path) -> None:
    if path.is_symlink() or not path.is_file():
        raise RuntimeError(f'Refusing non-regular or symlink path: {path}')


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--playbooks', type=Path, default=Path('/home/richard/playbooks'))
    choice = ap.add_mutually_exclusive_group()
    choice.add_argument('--plan', action='store_true', help='default: list exact candidates only')
    choice.add_argument('--apply', action='store_true', help='archive all candidates, verify, then delete only archived tests')
    args = ap.parse_args()
    playbooks = args.playbooks.expanduser().resolve(strict=True)
    test_dir = playbooks / ROLE_TESTS
    feature_dir = Path(__file__).resolve().parent.parent
    archive_dir = feature_dir / 'tests' / 'retired-step12-3'
    if not test_dir.is_dir() or test_dir.is_symlink():
        raise RuntimeError(f'Missing/unsafe Playbooks tests directory: {test_dir}')
    if (playbooks / '.git').is_symlink():
        raise RuntimeError('Refusing symlinked Playbooks .git')
    top = Path(git(playbooks, 'rev-parse', '--show-toplevel')).resolve()
    if top != playbooks:
        raise RuntimeError(f'Playbooks mismatch: expected {playbooks}; Git reports {top}')
    branch = git(playbooks, 'branch', '--show-current') or '(detached)'
    revision = git(playbooks, 'rev-parse', 'HEAD')
    candidates = sorted(p for p in test_dir.iterdir() if retired_name(p.name))
    for p in candidates:
        ensure_regular(p)
    print('PLAYBOOKS:', playbooks)
    print('BRANCH:', branch)
    print('REVISION:', revision)
    print('MATCHING TEST/DOC FILES:', len(candidates))
    print('ARCHIVE:', archive_dir)
    if not candidates:
        print('No matching prototype verification scripts to retire. PASS (no changes).')
        return 0

    # A runnable active script or Ansible task referencing a test by name must
    # be reconciled before the test is removed. Historical markdown is excluded.
    live = [playbooks/'btrfs-replication.yaml', playbooks/'site.yaml']
    for folder in [playbooks/'roles/btrfs-replication/tasks',
                   playbooks/'roles/btrfs-replication/files',
                   playbooks/'.github/workflows']:
        if folder.is_dir():
            live.extend(p for p in folder.rglob('*')
                        if p.is_file() and not p.is_symlink() and p.suffix in {'.py', '.yaml', '.yml', '.sh'})
    names = {p.name for p in candidates}
    refs = []
    for p in live:
        if p.is_file():
            data = p.read_text('utf8', errors='replace')
            for name in names:
                if name in data:
                    refs.append((str(p.relative_to(playbooks)), name))
    if refs:
        print('ERROR: active code refers to prototype tests:', file=sys.stderr)
        for path, name in refs[:40]:
            print(f'  {path} references {name}', file=sys.stderr)
        return 2

    items = []
    for p in candidates:
        rel = p.relative_to(playbooks).as_posix()
        status = git(playbooks, 'status', '--short', '--', rel)
        item = {'source': rel, 'archive': p.name, 'sha256': digest(p), 'git_status': status}
        items.append(item)
        print(f"  {rel}  sha256={item['sha256'][:12]}  status={status or 'clean'}")
    if not args.apply:
        print('PLAN ONLY: no files archived or removed. Use --apply after reviewing paths.')
        return 0

    archive_dir.mkdir(parents=True, exist_ok=True)
    if archive_dir.is_symlink():
        raise RuntimeError('Archive directory is a symlink; refusing')
    manifest_path = archive_dir/'manifest.json'
    prior = {}
    if manifest_path.exists():
        ensure_regular(manifest_path)
        manifest = json.loads(manifest_path.read_text('utf8'))
        prior = {rec['archive']: rec for rec in manifest.get('files', [])}
    # Preflight archive conflicts *before* deleting anything.
    for item in items:
        dest = archive_dir / item['archive']
        if dest.exists() or dest.is_symlink():
            ensure_regular(dest)
            if digest(dest) != item['sha256']:
                raise RuntimeError(f'Existing archival copy differs, refusing deletion: {dest}')
        if item['archive'] in prior and prior[item['archive']]['sha256'] != item['sha256']:
            raise RuntimeError(f'Manifest already contains different source: {item["archive"]}')
    # Archive all first, then independently checksum every byte before removal.
    for item, src in zip(items, candidates):
        dest = archive_dir / item['archive']
        if not dest.exists():
            shutil.copy2(src, dest)
    for item in items:
        if digest(archive_dir/item['archive']) != item['sha256']:
            raise RuntimeError(f'Archive verification failed: {item["archive"]}')
    merged = {**prior, **{i['archive']: i for i in items}}
    doc = {
        'purpose':'0040-FEAT historical Step 12.3 prototype verification retirement',
        'created_or_updated_utc': datetime.now(timezone.utc).isoformat(),
        'source_host':'mango (operator execution)',
        'playbooks_branch': branch,
        'playbooks_revision_at_archive': revision,
        'files': [merged[k] for k in sorted(merged)],
    }
    tmp = archive_dir/'manifest.json.tmp'
    tmp.write_text(json.dumps(doc, indent=2, sort_keys=True)+'\n', encoding='utf8')
    tmp.replace(manifest_path)
    for p in candidates:
        p.unlink()
    print(f'PASS: archived and removed {len(candidates)} obsolete prototype tests; manifest: {manifest_path}')
    print('Review Playbooks git status and commit the Diaries archive via normal source-control workflow.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
