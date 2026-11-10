#!/usr/bin/env python3
"""0044 one-off: retire overlapping historical regression, without deploying."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys

BASELINE = "06cf0886a863ce2d4d5e19289fc1fbf124d97554"
LEGACY = "roles/btrfs-replication/tests/verify-legacy-retirement-source.py"
LEGACY_SHA = "f47979cdef418a014dfbd540fa4cb31c8cf9441215bfcfa61d451c949afae1f9"
UPDATED_SHA = {'roles/btrfs-replication/tests/verify-simplified-cutover-readiness.py': 'b8962ef9d36f82f0c5fd44483bfb8eda17a04332e52f918a7ecfeac8565c5b18', 'roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md': '7164cef20770af0fe0dc654531feaf52c68f10a78b75d210ccb0acefa3b9cf4c'}
UPDATED = set(UPDATED_SHA)


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def require(ok, reason):
    if not ok:
        raise RuntimeError(reason)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    repo = Path.cwd().resolve()
    require(Path(git('rev-parse', '--show-toplevel')).resolve() == repo,
            'Run from Playbooks repository root')
    require(git('branch', '--show-current') == 'main', 'Expected main branch')
    require(git('rev-parse', 'HEAD') == BASELINE, 'Unexpected Playbooks HEAD; inspect before editing')
    require(not git('diff', '--cached', '--name-only'), 'Existing staged changes; refusing')
    require(set(git('diff', '--name-only').splitlines()) == UPDATED,
            'Apply the two-file Playbooks ZIP first; no other changes permitted')
    require(not git('ls-files', '--others', '--exclude-standard'), 'Untracked files present; refusing')
    for name, expected in UPDATED_SHA.items():
        require(sha256(repo / name) == expected, f'Unexpected content: {name}')
    require((repo / LEGACY).is_file(), 'Legacy test absent; perhaps already removed')
    require(sha256(repo / LEGACY) == LEGACY_SHA, 'Legacy test has unexpected changes')
    require(git('ls-files', '--error-unmatch', LEGACY) == LEGACY, 'Legacy test is not tracked')
    references = subprocess.run(['git', 'grep', '-n', '-F', 'verify-legacy-retirement-source.py', '--',
                                 ':!'+LEGACY], text=True, capture_output=True)
    require(references.returncode == 1, 'Other tracked references remain: ' + references.stdout + references.stderr)
    print('PASS: 0044 retirement preflight; expected two edits, original test intact', flush=True)


def run(*args, sudo=False):
    command = (['sudo', '-n', 'env', 'PYTHONDONTWRITEBYTECODE=1'] if sudo else []) + ['python3', *args]
    if not sudo:
        env = os.environ.copy()
        env['PYTHONDONTWRITEBYTECODE'] = '1'
    else:
        env = None
    print('RUN:', ' '.join(command), flush=True)
    subprocess.run(command, check=True, env=env)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='read-only preflight')
    parser.add_argument('--apply', action='store_true', help='remove and verify')
    args = parser.parse_args()
    require(args.check != args.apply, 'Specify exactly one of --check or --apply')
    preflight()
    if args.check:
        return
    subprocess.run(['git', 'rm', '--', LEGACY], check=True)
    subprocess.run(['git', 'add', '--', *sorted(UPDATED)], check=True)
    require(set(git('diff', '--cached', '--name-only').splitlines()) == UPDATED | {LEGACY},
            'Unexpected staged paths')
    print('=== Regressions: unchanged protocol, updated cutover, protection, retention ===', flush=True)
    base = 'roles/btrfs-replication/tests/'
    run(base+'verify-simplified-replication.py', sudo=True)
    run(base+'verify-simplified-protection.py', sudo=True)
    run(base+'verify-simplified-cutover-readiness.py')
    run(base+'verify-shared-retention.py')
    subprocess.run(['git', 'diff', '--cached', '--check'], check=True)
    require(not git('diff', '--name-only'), 'Unexpected remaining unstaged changes')
    require(not git('ls-files', '--others', '--exclude-standard'), 'Unexpected untracked files after tests')
    print('=== Staged changes ===', flush=True)
    subprocess.run(['git', 'diff', '--cached', '--stat'], check=True)
    subprocess.run(['git', 'status', '--short', '--branch'], check=True)
    print('PASS: 0044 legacy regression retired; safeguards retained; tests passed; changes staged, not committed', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError, OSError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        sys.exit(1)
