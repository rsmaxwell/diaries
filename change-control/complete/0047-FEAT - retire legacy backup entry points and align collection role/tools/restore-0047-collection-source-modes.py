#!/usr/bin/env python3
"""0047 one-off: restore exact 0045 per-path modes in mango's Playbooks *source*.

Run from Windows Cygwin using:
  ssh mango 'cd /home/richard/playbooks && python3 - --apply' < this-file

Never changes installed files, user data, snapshot state or Git contents.
The source-mode contract is in the Playbooks role, versioned independently
because Git does not track group-writable or directory modes.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

if len(sys.argv) != 2 or sys.argv[1] not in ('--check', '--apply'):
    raise SystemExit('Usage: restore-0047-collection-source-modes.py --check|--apply')

root = Path('/home/richard/playbooks')
assert Path.cwd().resolve() == root, 'Run from /home/richard/playbooks on mango'
role = root / 'roles/backup-collection'
manifest = json.loads((role / 'source-modes.json').read_text())
assert manifest['schema'] == '0047-collection-source-modes-v1'

def git(*args):
    return subprocess.check_output(['git', '-C', str(root), *args], text=True).strip()

assert git('branch', '--show-current') == 'main', 'Expected Playbooks main branch'
assert not git('diff', '--cached', '--name-only'), 'Pre-existing staged changes; inspect first'
assert len(manifest['entries']) == 14, 'Unexpected source-mode contract'

changes = []
for item in manifest['entries']:
    rel = Path(item['path'])
    assert not rel.is_absolute() and '..' not in rel.parts and rel.parts[0] == 'files'
    source = role / rel
    # Reject symlinks in any component, including internal ancestors.
    for candidate in (source, *source.parents):
        if candidate == role.parent:
            break
        assert not candidate.is_symlink(), f'Refusing symlink in source path: {source}'
    assert source.resolve(strict=True).is_relative_to((role / 'files').resolve())
    info = source.lstat()
    assert (stat.S_ISREG(info.st_mode) if item['kind'] == 'file'
            else stat.S_ISDIR(info.st_mode)), f'Wrong type: {rel}'
    if item['kind'] == 'file':
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        assert digest == item['sha256'], f'Content diverged from 0045 baseline: {rel}'
    mode = int(item['mode'], 8)
    before = stat.S_IMODE(info.st_mode)
    if before != mode:
        changes.append((source, before, mode))
        print(f"{'APPLY' if sys.argv[1] == '--apply' else 'WOULD CHANGE'} "
              f"{rel}: {before:04o} -> {mode:04o}", flush=True)
        if sys.argv[1] == '--apply':
            os.chmod(source, mode)
            actual = stat.S_IMODE(source.lstat().st_mode)
            assert actual == mode, f'Failed to set {rel} to {mode:04o}'

if sys.argv[1] == '--apply':
    assert not git('diff', '--cached', '--name-only'), 'Unexpected index changes'
    print(f'PASS: restored {len(changes)} Playbooks source paths; '
          'all 14 match accepted 0045 source-mode contract', flush=True)
else:
    print(f'CHECK: {len(changes)} of 14 source paths need mode restoration', flush=True)
    if changes:
        raise SystemExit(1)
