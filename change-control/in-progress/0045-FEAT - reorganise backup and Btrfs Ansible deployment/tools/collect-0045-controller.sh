#!/usr/bin/env bash
# 0045 Step 1: non-secret controller source and inventory topology capture.
# Run via `ssh mango 'bash -s' < this-file`; no installation or secret dumps.
set -euo pipefail
cd /home/richard/playbooks
printf '=== Controller and repository ===\n'
hostname
pwd
git branch --show-current
git rev-parse HEAD
git status --short --branch
git submodule status || true
printf '\n=== Current Playbooks commit and active regression files ===\n'
git log -1 --format=fuller
git ls-files -- roles/btrfs-replication/tests/ roles/snapshots/tests/ roles/local-backup/tests/
printf '\n=== Relevant current entry points / wrappers ===\n'
for file in local-backup.yaml remote-backup.yaml btrfs-replication.yaml snapshots.yaml scripts/local-backup.sh scripts/remote-backup.sh scripts/snapshots.sh; do
  if test -f "$file"; then
    printf 'PRESENT %s sha256=' "$file"
    sha256sum "$file" | awk '{print $1}'
  else
    printf 'ABSENT %s\n' "$file"
  fi
done
printf '\n=== Installed role source manifest (names only) ===\n'
git ls-files -- roles/local-backup/ roles/snapshots/ roles/btrfs-replication/ roles/btrfs/
printf '\n=== Playbooks call sites (filenames only) ===\n'
git grep -l -E 'remote-backup\.yaml|local-backup\.yaml|scripts/remote-backup\.sh|scripts/local-backup\.sh|btrfs-replication\.yaml' -- '*.yaml' '*.yml' '*.sh' '*.md' || true
printf '\n=== System inventory file names (NO CONTENTS) ===\n'
sudo -n find /etc/ansible -maxdepth 5 -type f -printf '%P\n' | sort
printf '\n=== Ansible version and host/group topology (NO --vars, NO --list) ===\n'
ansible --version | head -5
ansible-inventory --graph --vault-password-file "$HOME/.vault_pass.txt"
printf '\n=== Playbook host selection ===\n'
for file in local-backup.yaml remote-backup.yaml btrfs-replication.yaml snapshots.yaml; do
  if test -f "$file"; then
    printf '\n--- %s ---\n' "$file"
    ansible-playbook --list-hosts --vault-password-file "$HOME/.vault_pass.txt" "$file"
  fi
done
printf '\n=== Allowlisted non-secret effective variables (no inventory dump) ===\n'
python3 - <<'PYVARS'
import json
import os
import subprocess
import sys

keys = (
    'btrfs_native_endpoint_role',
    'btrfs_snapshot_activation_enabled',
    'btrfs_snapshot_prune_activation_enabled',
    'btrfs_snapshot_prune_on_calendar',
    'btrfs_snapshot_prune_max_delete',
    'btrfs_native_push_schedule_enabled',
    'btrfs_native_push_on_calendar',
    'btrfs_simplified_receiver_prune_enabled',
    'btrfs_simplified_receiver_prune_on_calendar',
    'btrfs_stale_qgroups_on_calendar',
    'diaries_pull_install',
    'diaries_pull_schedule_enabled',
    'diaries_pull_on_calendar',
    'local_backup_user_cron_hour',
    'local_backup_user_cron_minute',
)
result = {}
for host in ('mars', 'backup'):
    cmd = ('ansible-inventory', '--host', host, '--vault-password-file',
           os.path.expanduser('~/.vault_pass.txt'))
    p = subprocess.run(cmd, capture_output=True, check=False)
    if p.returncode != 0:
        # Never print raw Ansible output or errors: may contain decrypted secrets.
        print('FAIL: cannot resolve allowlisted inventory variables', file=sys.stderr)
        sys.exit(1)
    try:
        variables = json.loads(p.stdout)
    except (UnicodeDecodeError, ValueError):
        print('FAIL: unexpected inventory output format', file=sys.stderr)
        sys.exit(1)
    selection = {}
    for key in keys:
        if key not in variables:
            selection[key] = {'present': False}
            continue
        value = variables[key]
        if type(value) not in (str, int, bool, float) or len(str(value)) > 120:
            selection[key] = {'present': True, 'invalid_type_or_length': True}
            continue
        selection[key] = {'present': True, 'value': value}
    result[host] = selection
print(json.dumps(result, indent=2, sort_keys=True))
PYVARS
printf '\n=== Non-secret central Btrfs schedule checksum (if present) ===\n'
if test -f /etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml; then
  sha256sum /etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml
else
  printf 'ABSENT: /etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml\n'
fi
printf '\nPASS: read-only controller capture\n'
