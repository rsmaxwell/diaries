#!/usr/bin/env python3
"""0044 one-off Playbooks cutover-test retirement. No host operations."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess

BASELINE = 'b393602f3086a570e429dbec57d1a9ff1db7304b'
OLD = 'roles/btrfs-replication/tests/verify-simplified-cutover-readiness.py'
OLD_SHA = 'b8962ef9d36f82f0c5fd44483bfb8eda17a04332e52f918a7ecfeac8565c5b18'
EDITED_SHA = {'roles/btrfs-replication/tests/verify-simplified-protection.py': '8923b2f8b2a02bbae573c32023dad334a6663e166a1b01a0049686bd593a287b', 'roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md': 'ef98ba4d6208dac8c3dc9e7c1f0edca7e88f5cbd91fe00863e1dc81a529a7d6d'}
EDITED = set(EDITED_SHA)


def git(*args):
    return subprocess.check_output(['git', *args], text=True).strip()


def require(condition, explanation):
    if not condition:
        raise RuntimeError(explanation)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def preflight():
    root = Path.cwd().resolve()
    require(root == Path(git('rev-parse', '--show-toplevel')).resolve(),
            'Run from /home/richard/playbooks repository root')
    require(git('branch', '--show-current') == 'main', 'Expected main branch')
    require(git('rev-parse', 'HEAD') == BASELINE, 'Unexpected Playbooks HEAD')
    require(not git('diff', '--cached', '--name-only'), 'Already-staged changes present')
    require(set(git('diff', '--name-only').splitlines()) == EDITED,
            'Expected only the two updated files from the Playbooks ZIP')
    require(not git('ls-files', '--others', '--exclude-standard'),
            'Untracked files present; review before retirement')
    for name, expected in EDITED_SHA.items():
        require(sha256(root/name) == expected, f'Unexpected edited content: {name}')
    require((root/OLD).is_file() and sha256(root/OLD) == OLD_SHA,
            'Unexpected current cutover test content')
    require(git('ls-files', '--error-unmatch', OLD) == OLD,
            'Current cutover test is not tracked')
    result = subprocess.run(['git', 'grep', '-n', '-F',
                             'verify-simplified-cutover-readiness.py', '--',
                             ':(exclude)'+OLD], text=True, capture_output=True)
    require(result.returncode == 1,
            'Other tracked executable references must be updated: '+result.stdout+result.stderr)
    print('PASS: Baseline, historical test and two updated files verified', flush=True)


def test(*args, sudo=False):
    command = (['sudo','-n','env','PYTHONDONTWRITEBYTECODE=1'] if sudo
               else ['env','PYTHONDONTWRITEBYTECODE=1']) + ['python3', *args]
    print('RUN: ' + ' '.join(command), flush=True)
    subprocess.run(command, check=True)


def apply():
    preflight()
    subprocess.run(['git','rm','--',OLD], check=True)
    subprocess.run(['git','add','--',*sorted(EDITED)], check=True)
    expected = EDITED | {OLD}
    staged = set(git('diff','--cached','--name-only').splitlines())
    require(staged == expected, f'Unexpected staged paths: {staged ^ expected}')
    subprocess.run(['git','diff','--cached','--check'],check=True)
    print('=== Consolidated permanent regressions ===',flush=True)
    base = 'roles/btrfs-replication/tests/'
    test(base+'verify-simplified-replication.py', sudo=True)
    test(base+'verify-simplified-protection.py', sudo=True)
    test(base+'verify-shared-retention.py')
    print('=== Staged changes ===',flush=True)
    subprocess.run(['git','diff','--cached','--stat'],check=True)
    subprocess.run(['git','status','--short','--branch'],check=True)
    print('PASS: Cutover test retired; permanent pin protection retained; '
          'three paths staged; not committed',flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true')
    action.add_argument('--apply', action='store_true')
    arguments = parser.parse_args()
    try:
        if arguments.check:
            preflight()
        else:
            apply()
    except (RuntimeError, OSError, subprocess.CalledProcessError) as error:
        parser.exit(1, f'FAIL: {error}\n')
