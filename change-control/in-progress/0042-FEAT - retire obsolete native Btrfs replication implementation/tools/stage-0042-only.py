#!/usr/bin/env python3
"""0042-FEAT: stage only source retirement, keeping 0039 qgroup edits unstaged.

Pure, self-contained feature-local helper. It does not write the working tree,
commit, push, execute Ansible, change timers, or modify host files.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

EXPECTED_HEAD = 'e0da797310ab452ddc61e7368c50a444fe881e41'
FILES_SHA256 = {'roles/btrfs-replication/README.md': '0b120d850032c147d4689ed886216dae1b71c1174826b8619a5c3e6e7d38738f', 'roles/btrfs-replication/defaults/main.yaml': 'bf0ad275065047053ac4642caf388f548664c493697c2002a3c210b4deaa1219', 'roles/btrfs-replication/tasks/native.yaml': 'c51c93c219c8319017dc93799aabf4a53f5de24e2f1028e2c02c58697d4bd8f4', 'roles/btrfs-replication/templates/btrfs-native-push.service.j2': '1b022132b11b20acf9635e6ff439501bb63d0f56e9cf7a962b47b2fd546546e2', 'roles/btrfs-replication/tests/README-0040-SIMPLIFIED.md': 'b7a179ff908f8e465e871ebc7ba40a21ffe1c1c21823f562bb36dfc697d3c269', 'roles/btrfs-replication/tests/verify-0040-legacy-retirement-source.py': 'f47979cdef418a014dfbd540fa4cb31c8cf9441215bfcfa61d451c949afae1f9', 'roles/btrfs-replication/tests/verify-0040-simplified-cutover-readiness.py': '8f78490f41829b085e6668fe15ec0a630846f68e8337008bf40d1b8229c6c576', 'roles/btrfs-replication/tests/verify-0040-simplified-protection.py': 'd62e93be2c398a5618a11b6b99e2f4f511c92a5525b716cb8aa2d3844dc194f4'}
SHARED_HEAD_SHA256 = {'roles/btrfs-replication/defaults/main.yaml': '162c9fb924c7e1c62479dfb7fc2e819f77242dbb41f05e98411c6fa1497b6237', 'roles/btrfs-replication/tasks/native.yaml': 'ebf289047a45e24ba6dec799908055b2375e8d82388c0e7ea896a2dab9a599f7'}
SHARED_0039_SUFFIXES = {'roles/btrfs-replication/defaults/main.yaml': '\n# 0039-DEF: one housekeeping executable for mars and backup. Merely installing\n# it never activates the scheduled cleanup. Both gates must be reviewed for\n# each host after the read-only Step 8 baseline and Step 9 source regression.\nbtrfs_stale_qgroup_maintenance_install_enabled: false\nbtrfs_stale_qgroup_maintenance_enabled: false\nbtrfs_stale_qgroup_on_calendar: "*-*-* 05:30:00 UTC"\nbtrfs_stale_qgroup_max_stale: 2000\n# The installed /etc/btrfs-stale-qgroups.json is rendered separately on\n# each endpoint; the executable and systemd service implementation are shared.\nbtrfs_stale_qgroup_filesystem_path: "{{ \'/media/usb\' if btrfs_native_endpoint_role == \'source\' else \'/\' }}"\nbtrfs_stale_qgroup_manager_config_path: /etc/btrfs-snapshot-manager.json\nbtrfs_stale_qgroup_writer_lock_path: "{{ \'/media/usb/@data/backup/.btrfs-snapshot-writer.lock\' if btrfs_native_endpoint_role == \'source\' else \'/@data/mars-received/.replication-state/writer.lock\' }}"\n', 'roles/btrfs-replication/tasks/native.yaml': '\n# 0039-DEF: shared, explicitly gated housekeeping for both source and receiver.\n- name: Native Btrfs | Configure qgroup maintenance without activating by default\n  ansible.builtin.import_tasks: qgroup-maintenance.yaml\n  tags: [qgroup-maintenance]\n'}
SHARED = tuple(SHARED_0039_SUFFIXES)
EXCLUSIVE = tuple(sorted(set(FILES_SHA256) - set(SHARED)))


def git(*args, data=None):
    result = subprocess.run(['git', *args], input=data, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, check=False)
    if result.returncode != 0:
        raise RuntimeError('git '+ ' '.join(args) + ' failed (rc=' + str(result.returncode) + '): ' + result.stderr.decode(errors='replace'))
    return result.stdout


def sha(data):
    return hashlib.sha256(data).hexdigest()


def check():
    repo = Path(git('rev-parse', '--show-toplevel').decode().strip()).resolve()
    if repo != Path('/home/richard/playbooks').resolve():
        raise RuntimeError('unexpected Playbooks root: ' + str(repo))
    if git('rev-parse', 'HEAD').decode().strip() != EXPECTED_HEAD:
        raise RuntimeError('Git HEAD changed; no staging attempted')
    if git('symbolic-ref', '--short', 'HEAD').decode().strip() != 'main':
        raise RuntimeError('not on main branch')

    manifest = Path(__file__).with_name('obsolete-playbooks-paths.json')
    entries = json.loads(manifest.read_text())['files']
    retired = {e['path'] for e in entries}
    if len(retired) != 215:
        raise RuntimeError('manifest not exactly 215 unique paths')
    staged = set(filter(None,git('diff', '--cached', '--name-only', '-z').decode().split('\0')))
    deleted = set(filter(None,git('diff','--cached','--name-only','--diff-filter=D','-z').decode().split('\0')))
    if staged != retired or deleted != retired:
        raise RuntimeError('staged changes are not precisely the 215 expected deletions')
    if git('diff', '--cached', '--check'):
        raise RuntimeError('staged diff check failed')

    for path, expected in FILES_SHA256.items():
        p = repo / path
        if not p.is_file() or p.is_symlink() or sha(p.read_bytes()) != expected:
            raise RuntimeError('working file differs from reviewed 0042 ZIP: ' + path)
        idx = git('show', ':' + path)
        head = git('show', 'HEAD:' + path)
        if idx != head:
            raise RuntimeError('already staged non-retirement changes: ' + path)
        if path in SHARED and sha(head) != SHARED_HEAD_SHA256[path]:
            raise RuntimeError('shared file baseline not reviewed: ' + path)

    staged_shared = {}
    for path, suffix in SHARED_0039_SUFFIXES.items():
        work = (repo/path).read_bytes()
        suffix = suffix.encode('utf-8')
        if not work.endswith(suffix):
            raise RuntimeError('0039-only trailing block missing: ' + path)
        staged_shared[path] = work[:-len(suffix)]
        if not staged_shared[path]:
            raise RuntimeError('shared staged content empty: ' + path)
    return repo, retired, staged_shared


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--plan',action='store_true')
    mode.add_argument('--stage',action='store_true')
    args=parser.parse_args()
    repo, retired, shared_index = check()
    print('PASS: exact 215 archived deletions staged; reviewed working files unchanged')
    print('0042-only modified paths:', len(FILES_SHA256))
    print('0039-only shared changes held back:', ', '.join(SHARED))
    if args.plan:
        print('PLAN: no changes staged')
        return
    for path in EXCLUSIVE:
        git('add', '--', path)
    for path in SHARED:
        blob=git('hash-object', '-w', '--stdin', data=shared_index[path]).decode().strip()
        git('update-index','--cacheinfo','100644,'+blob+','+path)
        if git('show', ':'+path) != shared_index[path]:
            raise RuntimeError('indexed shared bytes not verified: ' + path)
        if (repo/path).read_bytes() != shared_index[path]+SHARED_0039_SUFFIXES[path].encode():
            raise RuntimeError('0039 working bytes changed while staging: ' + path)
    names=set(filter(None,git('diff','--cached','--name-only','-z').decode().split('\0')))
    if names != retired | set(FILES_SHA256):
        raise RuntimeError('unexpected source staged after completion')
    git('diff','--cached','--check')
    print('PASS: 0042 index contains 215 deletions plus %d 0042-only updates' % len(FILES_SHA256))
    print('PASS: 0039 qgroup additions remain unstaged in two shared files')
    print('No commit made; review git diff --cached --stat then commit.')

if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, ValueError, KeyError) as e:
        print('REFUSED: '+str(e), file=sys.stderr)
        sys.exit(1)
