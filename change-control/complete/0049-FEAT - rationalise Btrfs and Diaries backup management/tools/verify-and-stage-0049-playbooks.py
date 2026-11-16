#!/usr/bin/env python3
"""0049 feature-only safety check / exact-file staging for Playbooks on mango.

Run from Windows Cygwin:
  ssh mango 'python3 - --inspect' < 'change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/tools/verify-and-stage-0049-playbooks.py'
To stage exact approved files after review, replace --inspect with --stage.
This helper does NOT commit, push, touch private inventory, or remove untracked files.
"""
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path('/home/richard/ansible-controller/playbooks')
BASE = '0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532'
EXPECTED = {'roles/backup-collection/tasks/source_snapshot_access.yaml': '1711d390819bf98d3720c7283bf9dad5b4eaecbf14168c68819d0f05d835c5fb', 'roles/btrfs-replication/README.md': '6767a45845e69f13cd60e1b05050f0e23b7996cf2d91b5338bff8c6923f81843', 'roles/btrfs-replication/defaults/main.yaml': '2fee4b5d502d55ff6b4090422180e410d75dae110ac46d81d96ef53de46b8a5d', 'roles/btrfs-replication/files/btrfs-replication-receiver-gate-0041.py': '9ba800110626ce870a4752709ab093d24c37df2e295ebb7bd35a8c81db46ed6e', 'roles/btrfs-replication/files/btrfs-replication-sender-cycle-0041.sh': 'edf27767c82def46cf988f41914658dbae24b83df725c18d222fdc0688fda4f9', 'roles/btrfs-replication/files/btrfs-replication.py': '7b4e4e99a2031cca6c82adc8fb3d59d59cdd66ef5aa7d6ce79a23baba6804ff2', 'roles/btrfs-replication/tasks/endpoint-setup.yaml': 'd1eea1267f2b258cf916fea0533346d29387ae34be05a0091f2edef7565a7a7c', 'roles/btrfs-replication/tasks/native.yaml': 'ae0a9c73d2dc128ab1efe1a44dcfed691e451536c2489cafd7d7dc51abb6273b', 'roles/btrfs-replication/tasks/receiver-config.yaml': 'b18c6a58cc511be14f79ac6ac82d25252822cd181c923920344db25a7fc60f5f', 'roles/btrfs-replication/tasks/receiver-retention.yaml': 'f8ed448159e129bd4bcc5bfe797a5d0aee1538c7df3c2cab1d1f6d13c382fb2f', 'roles/btrfs-replication/tasks/retire-0049-interfaces.yaml': '3fc886a7779123eb4af6251278c5557421e111006574a5e041a2caf641d6ce55', 'roles/btrfs-replication/tasks/service-identities-0041.yaml': '6938366c619fa48c9e21c8ab39fca7a1b606e82799c22250caa02ddcd094c6e1', 'roles/btrfs-replication/tasks/simplified-runtime.yaml': '5172d8a0e34cd066ef4226d736f6e8b9ddaa61dee0689c98b982267f986d7359', 'roles/btrfs-replication/tasks/source-scheduling.yaml': '71bc528d8d9fefae2888732a42ad65b02ff37c2671bdbb5a374c43a88f02b2f1', 'roles/btrfs-replication/templates/btrfs-push-0041.service.j2': '0750d67103d6838fefbbac364915bb283a00387c77e7e1ad80b7f2aeed39dc4f', 'roles/btrfs-replication/templates/btrfs-push.service.j2': '92e92307cd28b87f049863a1b1587e8af547aaec3171d0a910085dee06ad016a', 'roles/btrfs-replication/templates/btrfs-push.timer.j2': '21fd7e7ea51b459e6087af17d79a408693992f0e41b2aa8e94e2b5d1e94291e0', 'roles/btrfs-replication/templates/btrfs-receiver-manager.json.j2': '1772055db4da185b8a8de1b3b9cd14b36b7cb4e380f06062689dd40002457382', 'roles/btrfs-replication/templates/btrfs-receiver-prune.service.j2': '0848a231bd53fd01c56eda1ba5fbbc7111e5659e05123be7bbb2476fbd35bda6', 'roles/btrfs-replication/templates/btrfs-receiver-prune.timer.j2': 'de164438471ae48c1fa62985c86b545b818fe815d82e468fcc1c81481e863b0b', 'roles/btrfs-replication/tests/README.md': 'f536dc1e62a27bf074c9220e366a3c7a53a1033fe1b253dcd44da82b8cd9685c', 'roles/btrfs-replication/tests/verify-0041-restricted-identity.py': 'e61204f6a37113d65b708e8ad73f81016ee7292925432066288d3f258427cb37', 'roles/btrfs-replication/tests/verify-0049-backup-management.py': '9fec2442b449daefb08faa57a453f78cc942e63b78913b6862f0e4c00b0fb9e1', 'roles/btrfs-replication/tests/verify-replication.py': '0bdfffe6123a2768f774ff4eed38ae3e240f3d1a1e20ad191a9780f3abc7fb35', 'roles/snapshots/README.md': '36b0ccec3000b71bc86bce57a421667a4e02115fc1cc731713c180c1cd127da4', 'roles/snapshots/files/btrfs-backup-status.py': 'af73740c4dfb8b5c78c9f343ac46d3861e01fa950d07ab7ac2f51b9a1eeb8370', 'roles/snapshots/files/btrfs-snapshot-manager.py': 'e84e6c394920867793ecac52b33b4c09f518bf9223a383c3d74a52acd1fccbf0', 'roles/snapshots/files/diaries-backup-history.py': '8992d548d7820537765dd607345ccdc70afc1a43ace232ead4147dd70e7ca0c0', 'roles/snapshots/files/diaries-backup-status.py': 'feed0027b7fa9e510ef5524cd3f2dcfad9deb9417ede8016636f032a0b1b0d13', 'roles/snapshots/tests/verify-0040-simplified-receiver-retention.py': 'eab031c441a9922a5fe7d0e1a085d37243616f4dc99787278524cbd456fcba47', 'roles/snapshots/tests/verify-0040-step13-source-prune-cap.py': '7be2f99c91858c9cb20e54b0a6d4cfc096348a604fc0ff852c4c64d6bebce362', 'roles/snapshots/tests/verify-diaries-backup-status.py': '0b73b52ae345a7e6b244a676f20b406c378ec8af47f7d641ec7a2d8ae47eedfa'}

def git(*args):
    return subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True)

def abort(reason):
    print('0049 GIT PRECHECK: FAIL — ' + reason, file=sys.stderr)
    sys.exit(2)

def main():
    if sys.argv[1:] not in (['--inspect'], ['--stage']):
        abort('usage: --inspect (read-only) or --stage (stage only these 32 files)')
    action = sys.argv[1]
    top = git('rev-parse', '--show-toplevel')
    if top.returncode or Path(top.stdout.strip()).resolve() != ROOT.resolve():
        abort('Playbooks checkout missing or wrong git root: ' + (top.stderr.strip() or top.stdout.strip()))
    branch = git('branch', '--show-current')
    revision = git('rev-parse', 'HEAD')
    if branch.returncode or revision.returncode:
        abort('Cannot determine Playbooks branch/HEAD')
    print('PLAYBOOKS BRANCH:', branch.stdout.strip())
    print('PLAYBOOKS BASE HEAD:', revision.stdout.strip())
    if branch.stdout.strip() != 'main' or revision.stdout.strip() != BASE:
        abort('Branch or HEAD differs from 0049 baseline; reconcile before staging')
    status = git('status', '--short')
    print('CURRENT STATUS:')
    print(status.stdout or '(clean)')
    if status.returncode:
        abort(status.stderr.strip() or 'git status failed')
    cached = git('diff', '--cached', '--quiet')
    if cached.returncode != 0:
        abort('There are already staged changes; preserve/review those before proceeding')
    diffs = git('diff', '--check')
    if diffs.returncode:
        abort('git diff --check failed:\n' + diffs.stdout + diffs.stderr)
    failed = []
    for relative, expected in EXPECTED.items():
        p = ROOT / relative
        if not p.is_file() or p.is_symlink():
            failed.append(relative + ': missing or symlink')
            continue
        received = hashlib.sha256(p.read_bytes()).hexdigest()
        if received != expected:
            failed.append(relative + ': SHA256 mismatch (found ' + received + ')')
    if failed:
        for row in failed:
            print(row, file=sys.stderr)
        abort(f'{len(failed)} approved source files differ; no staging performed')
    print('0049 SOURCE HASHES: PASS (' + str(len(EXPECTED)) + ' approved files)')
    if action == '--inspect':
        print('0049 INSPECTION: PASS — no files staged or committed')
        return
    stage = git('add', '--', *EXPECTED.keys())
    if stage.returncode:
        abort('git add failed: ' + stage.stderr.strip())
    names = git('diff', '--cached', '--name-only')
    if names.returncode:
        abort('Cannot enumerate staged paths: ' + names.stderr.strip())
    staged = set(names.stdout.splitlines())
    if staged != set(EXPECTED):
        abort('staged source paths differ from 32-file manifest: missing=' + repr(sorted(set(EXPECTED)-staged)) +
              ' extra=' + repr(sorted(staged-set(EXPECTED))))
    checks = git('diff', '--cached', '--check')
    if checks.returncode:
        abort('Staged diff whitespace check failed:\n' + checks.stdout + checks.stderr)
    stat = git('diff', '--cached', '--stat')
    print('STAGED 0049 SOURCE DIFF:')
    print(stat.stdout)
    print('0049 STAGE: PASS — 32 approved files staged; no commit or push performed')

if __name__ == '__main__':
    main()
