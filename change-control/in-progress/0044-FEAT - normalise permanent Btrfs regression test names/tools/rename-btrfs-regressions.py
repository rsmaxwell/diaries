#!/usr/bin/env python3
"""0044-FEAT: safely rename permanent btrfs-replication regressions.

Operate on a verified, clean /home/richard/playbooks checkout. No host actions,
no snapshot operations, no commit or push. Historical feature prose is preserved.
"""
from __future__ import annotations

import argparse
import ast
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = '6d7f397048b8ed47c94f973a98096fc6e806e4e8'
DIRECTORY = Path('roles/btrfs-replication/tests')
RENAMES = {
    'verify-0040-simplified-replication.py': 'verify-simplified-replication.py',
    'verify-0040-simplified-protection.py': 'verify-simplified-protection.py',
    'verify-0040-simplified-cutover-readiness.py': 'verify-simplified-cutover-readiness.py',
    'verify-0040-step12-3-shared-retention.py': 'verify-shared-retention.py',
    'verify-0040-legacy-retirement-source.py': 'verify-legacy-retirement-source.py',
}
DOCS = (
    Path('roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md'),
    Path('roles/snapshots/tests/README-0040-SIMPLIFIED-RECEIVER-RETENTION.md'),
)


def git(repo: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[bytes]:
    result = subprocess.run(['git', '-C', str(repo), *args], capture_output=True)
    if check and result.returncode:
        detail = result.stderr.decode('utf-8', 'replace').strip()
        raise RuntimeError(f"git {' '.join(args)} failed: {detail}")
    return result


def verify(repo: Path, expected_head: str) -> dict[Path, bytes]:
    if not repo.is_dir():
        raise RuntimeError(f'Playbooks checkout missing: {repo}')
    branch = git(repo, 'branch', '--show-current').stdout.decode().strip()
    head = git(repo, 'rev-parse', 'HEAD').stdout.decode().strip()
    print(f'branch={branch} head={head}')
    if branch != 'main' or head != expected_head:
        raise RuntimeError(f'Expected branch main at {expected_head}')
    if git(repo, 'status', '--porcelain', '--untracked-files=normal').stdout:
        raise RuntimeError('Playbooks has existing changes; preserve/reconcile them before renaming')
    for old, new in RENAMES.items():
        src, dest = repo / DIRECTORY / old, repo / DIRECTORY / new
        if not src.is_file() or dest.exists():
            raise RuntimeError(f'Unexpected rename state: {src} -> {dest}')
        tracked = git(repo, 'ls-files', '--error-unmatch', '--', str(DIRECTORY / old), check=False)
        if tracked.returncode:
            raise RuntimeError(f'Old test is not Git-tracked: {old}')
        ast.parse(src.read_text(encoding='utf-8'), filename=str(src))
    documents = {}
    for doc in DOCS:
        if not (repo / doc).is_file():
            raise RuntimeError(f'Expected documentation missing: {doc}')
        documents[doc] = (repo / doc).read_bytes()
    if not any(any(old.encode() in content for old in RENAMES) for content in documents.values()):
        raise RuntimeError('Expected old filename references were not found in documentation')

    # Do not rename before checking whether any other tracked file references the
    # old script names. Historical docs outside Playbooks are intentionally untouched.
    for old in RENAMES:
        result = git(repo, 'grep', '-l', '-z', '-F', '-e', old, '--', check=False)
        if result.returncode not in (0, 1):
            raise RuntimeError(f'git grep failed for {old}: {result.stderr.decode(errors="replace")}')
        matches = {Path(x.decode('utf-8', 'surrogateescape')) for x in result.stdout.split(b'\0') if x}
        unexpected = matches - set(DOCS)
        if unexpected:
            raise RuntimeError(f'Unexpected references to {old}: {sorted(map(str, unexpected))}')
    return documents


def apply(repo: Path, documents: dict[Path, bytes]) -> None:
    for old, new in RENAMES.items():
        git(repo, 'mv', '--', str(DIRECTORY / old), str(DIRECTORY / new))
        print(f'RENAMED: {old} -> {new}')
    for doc, data in documents.items():
        updated = data
        for old, new in RENAMES.items():
            updated = updated.replace(old.encode(), new.encode())
        if updated != data:
            (repo / doc).write_bytes(updated)
            git(repo, 'add', '--', str(doc))
            print(f'UPDATED: {doc}')
    for new in RENAMES.values():
        target = repo / DIRECTORY / new
        ast.parse(target.read_text(encoding='utf-8'), filename=str(target))
    for old in RENAMES:
        result = git(repo, 'grep', '-l', '-F', '-e', old, '--', check=False)
        if result.returncode == 0:
            raise RuntimeError(f'Old filename still referenced: {old}\n{result.stdout.decode(errors="replace")}')
        if result.returncode != 1:
            raise RuntimeError(f'git grep failed after rename: {old}')
    git(repo, 'diff', '--cached', '--check')
    git(repo, 'diff', '--check')
    print(git(repo, 'diff', '--cached', '--stat').stdout.decode(), end='')
    print(git(repo, 'status', '--short').stdout.decode(), end='')
    print('PASS: five tests renamed, references updated, source parses, changes staged (not committed)')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=Path('/home/richard/playbooks'))
    parser.add_argument('--expected-head', default=EXPECTED_HEAD)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--check', action='store_true', help='read-only preflight')
    mode.add_argument('--apply', action='store_true', help='git mv, update references, stage changes')
    opts = parser.parse_args()
    try:
        repo = opts.repo.resolve()
        docs = verify(repo, opts.expected_head)
        if opts.check:
            for old, new in RENAMES.items():
                print(f'READY: {DIRECTORY / old} -> {DIRECTORY / new}')
            print('PASS: rename preflight; no files changed')
        else:
            apply(repo, docs)
        return 0
    except (RuntimeError, SyntaxError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
