#!/usr/bin/env python3
"""0042: guarded Playbooks-only source retirement. Never contacts backup hosts.

Run from mango:/home/richard/playbooks AFTER both ZIPs have been reviewed.
Archives exact bytes in the Diaries feature evidence directory before git rm.
"""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tarfile
from datetime import datetime, timezone

FEATURE = Path(__file__).resolve().parents[1]
MANIFEST = Path(__file__).with_name('obsolete-playbooks-paths.json')
ROOT = Path('/home/richard/playbooks')


def command(*args, cwd=ROOT):
    result = subprocess.run(args, cwd=cwd, text=True, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)
    if result.returncode:
        raise RuntimeError(f'{args}: rc={result.returncode}: {result.stderr.strip()}')
    return result.stdout


def verify(root, expected):
    if not (root / '.git').exists():
        # A worktree .git may be a file; explicit git plumbing checks below.
        assert (root / '.git').is_file(), f'Not a Git checkout: {root}'
    assert command('git', 'rev-parse', '--show-toplevel', cwd=root).strip() == str(root), 'Repository root mismatch'
    assert command('git', 'branch', '--show-current', cwd=root).strip() == 'main', 'Expected Playbooks main branch'
    native=(root/'roles/btrfs-replication/tasks/native.yaml').read_text()
    service=(root/'roles/btrfs-replication/templates/btrfs-native-push.service.j2').read_text()
    assert '/usr/local/bin/btrfs-simplified-replication sender cycle' in service
    assert '/usr/local/bin/btrfs-native-push --latest' not in service
    assert 'import_tasks: qgroup-maintenance.yaml' in native, '0039 implementation missing'
    assert 'btrfs-native-endpoint.py' not in native and 'btrfs-native-push.py' not in native
    out=[]
    for entry in expected:
        path=entry['path']
        assert path.startswith('roles/') and '..' not in Path(path).parts, path
        full=root/path
        info=full.lstat()
        assert stat.S_ISREG(info.st_mode) and not full.is_symlink(), f'Unsafe candidate: {path}'
        digest=hashlib.sha256(full.read_bytes()).hexdigest()
        assert digest == entry['sha256'], f'Changed candidate (refuse): {path}'
        assert command('git', 'ls-files', '--error-unmatch', '--', path, cwd=root).strip() == path, f'Untracked: {path}'
        assert not command('git', 'status', '--porcelain', '--', path, cwd=root).strip(), f'Local edits/staged: {path}'
        out.append({'path':path,'sha256':digest,'mode':stat.S_IMODE(info.st_mode),'size':info.st_size})
    assert len({a['path'] for a in out})==len(out), 'Duplicate paths'
    return out


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', action='store_true')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--expect-count', type=int)
    parser.add_argument('--confirm', default='')
    parser.add_argument('--repo', type=Path, default=ROOT)
    args=parser.parse_args()
    assert args.plan != args.apply, 'Choose exactly one of --plan or --apply'
    root=args.repo.resolve()
    expected=json.loads(MANIFEST.read_text())['files']
    recorded=verify(root, expected)
    print(f'PASS: {len(recorded)} exact, tracked, unmodified source files verified', flush=True)
    print('git_head='+command('git','rev-parse','HEAD',cwd=root).strip(),flush=True)
    if args.plan:
        for entry in recorded:print(entry['path'])
        return 0
    assert args.expect_count == len(recorded), 'Unexpected candidate count; refusing'
    assert args.confirm == 'RETIRE-0042-PLAYBOOKS-ONLY', 'Explicit confirmation token missing'
    evidence=FEATURE/'evidence'/'Step 1'
    evidence.mkdir(parents=True,exist_ok=True)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    archive=evidence/f'0042-retired-playbooks-{stamp}.tar.gz'
    receipt=evidence/f'0042-source-retirement-{stamp}.json'
    assert not archive.exists() and not receipt.exists(), 'Evidence name already exists'
    with tarfile.open(archive,'x:gz') as out:
        for entry in recorded:
            full=root/entry['path']
            out.add(full,arcname=entry['path'],recursive=False)
    # Read back and verify all content before any removal.
    with tarfile.open(archive,'r:gz') as saved:
        names=saved.getnames()
        assert names == [x['path'] for x in recorded], 'Archive member mismatch'
        for entry in recorded:
            data=saved.extractfile(entry['path']).read()
            assert hashlib.sha256(data).hexdigest()==entry['sha256'],f'Archive mismatch: {entry["path"]}'
    receipt_data={
        'timestamp':stamp,'result':'ARCHIVE_VERIFIED_REMOVAL_PENDING',
        'source_revision':command('git','rev-parse','HEAD',cwd=root).strip(),
        'candidate_count':len(recorded),'archive':str(archive),
        'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'files':recorded,
    }
    receipt.write_text(json.dumps(receipt_data,indent=2)+'\n')
    print('ARCHIVE_VERIFIED',archive,flush=True)
    # Git source-only deletion. No SSH, systemctl, snapshot, Btrfs or host changes.
    try:
        completed=command('git','rm','--',*[r['path'] for r in recorded],cwd=root)
    except Exception as exc:
        receipt_data['result']='GIT_RM_FAILED_REVIEW_REQUIRED'
        receipt_data['error']=str(exc)
        receipt.write_text(json.dumps(receipt_data,indent=2)+'\n')
        raise
    receipt_data['result']='SOURCE_REMOVED_STAGED'
    receipt_data['git_rm_output']=completed
    receipt.write_text(json.dumps(receipt_data,indent=2)+'\n')
    print('PASS: archived and git-rm staged',len(recorded),'source files')
    print('receipt:',receipt)
    print('IMPORTANT: synchronise evidence back to Windows Diaries repository before closure')
    return 0

if __name__ == '__main__':
    try:sys.exit(main())
    except Exception as exc:
        print('FAIL:',exc,file=sys.stderr)
        sys.exit(1)
