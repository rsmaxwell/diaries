#!/usr/bin/env bash
# Run on mango: bash -s < this file, through Windows Cygwin ssh mango.
# Non-interactive feature-specific script; does not deploy, commit or push.
set -euo pipefail
cd /home/richard/playbooks

[[ $(git branch --show-current) == main ]] || { echo 'FAIL: not on main'; exit 1; }
[[ $(git rev-parse --short=7 HEAD) == 9a21c69 ]] || { echo 'FAIL: unexpected Playbooks revision; inspect before cleanup'; exit 1; }
[[ $(git rev-parse HEAD) == $(git rev-parse origin/main) ]] || { echo 'FAIL: Playbooks not published/synchronised'; exit 1; }
git diff --cached --quiet || { echo 'FAIL: pre-existing staged changes'; exit 1; }
git diff --quiet -- roles/local-backup || { echo 'FAIL: modified original role; manual reconciliation required'; exit 1; }

for candidate in \
  backup-collection.yaml snapshots.yaml roles/backup-collection/tasks/main.yaml \
  roles/backup-collection/defaults/main.yaml roles/backup-collection/tests/verify-backup-collection-entrypoints.py; do
  [[ -f $candidate ]] || { echo "FAIL: new source missing: $candidate"; exit 1; }
done

# Every tracked original role file must already be present in the new role tree.
while IFS= read -r candidate; do
  migrated=${candidate/roles\/local-backup\//roles\/backup-collection\/}
  [[ -f $migrated ]] || { echo "FAIL: missing role file: $migrated"; exit 1; }
done < <(git ls-files -- roles/local-backup)

for old in local-backup.yaml remote-backup.yaml scripts/local-backup.sh \
           scripts/remote-backup.sh diaries-user-backup-cron.yaml; do
  [[ -f $old && ! -L $old ]] || { echo "FAIL: unexpected old entry point: $old"; exit 1; }
done

# The old role can contain ignored Python caches; never destroy unexpected files.
# Check both directories *before* removing anything.
for dir in roles/local-backup roles/remote-backup; do
  [[ -d $dir && ! -L $dir ]] || continue
  while IFS= read -r -d '' file; do
    if [[ $file != */__pycache__/*.pyc ]]; then
      if [[ $dir == roles/local-backup ]] && git ls-files --error-unmatch "$file" >/dev/null 2>&1; then
        continue
      fi
      echo "FAIL: unexpected untracked material in old role: $file"
      exit 1
    fi
  done < <(find "$dir" -type f -print0)
done
[[ -z $(git ls-files -- roles/remote-backup) ]] || { echo 'FAIL: obsolete remote role contains tracked files'; exit 1; }

echo '=== Retire tracked legacy interfaces ==='
git rm -r -- roles/local-backup
git rm -- local-backup.yaml remote-backup.yaml scripts/local-backup.sh \
           scripts/remote-backup.sh diaries-user-backup-cron.yaml

for dir in roles/local-backup roles/remote-backup; do
  if [[ -d $dir ]]; then
    find "$dir" -type f -path '*/__pycache__/*.pyc' -delete
    find "$dir" -depth -type d -empty -delete
  fi
  [[ ! -e $dir ]] || { echo "FAIL: legacy directory still contains files: $dir"; exit 1; }
done

echo '=== Stage intended replacements ==='
git add -- README.md backup-collection.yaml snapshots.yaml \
  roles/backup-collection roles/snapshots/README-0039-DEPLOYMENT.md \
  roles/snapshots/defaults/main.yaml \
  roles/snapshots/tests/verify-snapshot-launcher-host-context.py \
  roles/snapshots/tests/verify-btrfs-snapshot-manager.py \
  roles/btrfs-replication/tasks/source-scheduling.yaml

unexpected=$(git diff --cached --name-only | grep -Ev \
 '^(README\.md|backup-collection\.yaml|snapshots\.yaml|local-backup\.yaml|remote-backup\.yaml|diaries-user-backup-cron\.yaml|scripts/(local-backup|remote-backup)\.sh|roles/(local-backup|backup-collection)/|roles/snapshots/(README-0039-DEPLOYMENT\.md|defaults/main\.yaml|tests/verify-(snapshot-launcher-host-context|btrfs-snapshot-manager)\.py)|roles/btrfs-replication/tasks/source-scheduling\.yaml)' || true)
[[ -z $unexpected ]] || { printf 'FAIL: unexpected staged files:\n%s\n' "$unexpected"; exit 1; }
git diff --cached --check

export PYTHONDONTWRITEBYTECODE=1
for test in \
  roles/backup-collection/tests/verify-backup-collection-entrypoints.py \
  roles/backup-collection/tests/verify-user-backup-cron.py \
  roles/backup-collection/tests/verify-diaries-pull.py \
  roles/backup-collection/tests/verify-0036-gatec-fixed-optin.py \
  roles/backup-collection/tests/verify-0036-fixed-destination.py \
  roles/backup-collection/tests/verify-0036-step8-cutover-configuration.py \
  roles/snapshots/tests/verify-snapshot-launcher-host-context.py \
  roles/snapshots/tests/verify-btrfs-snapshot-manager.py \
  roles/btrfs-replication/tests/verify-replication.py \
  roles/btrfs-replication/tests/verify-protection.py \
  roles/btrfs-replication/tests/verify-shared-retention.py; do
  echo "=== Regression: $test ==="
  python3 -B "$test"
done

for play in backup-collection.yaml snapshots.yaml btrfs-replication.yaml; do
  echo "=== Syntax: $play ==="
  ansible-playbook "$play" --syntax-check --vault-password-file "$HOME/.vault_pass.txt"
done

echo '=== Stage summary (review before commit) ==='
git diff --cached --stat
echo '=== Working tree ==='
git status --short --branch
echo 'PASS: 0047 source retirement and consolidated regressions; source not committed or deployed'
