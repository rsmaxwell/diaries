#!/usr/bin/env bash
# 0045-FEAT: operator-invoked controlled apply with before/after fingerprints.
# This is an independent, non-interactive process. Never source in an interactive shell.
set -euo pipefail

if [[ "${1:-}" != '--apply' || "$#" -ne 1 ]]; then
  printf 'Usage: bash %s --apply\nNormal Ansible deployment on mars and backup; no --diff.\n' "$0" >&2
  exit 2
fi

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
feature="$root/change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment"
tools="$feature/tools"
baseline="$feature/evidence/Step 1/baseline-20261111-111819Z"
run_id="$(date -u +%Y%m%d-%H%M%SZ)"
evidence="$feature/evidence/Step 3/deployment-$run_id"
mkdir -p "$evidence"
printf '0045 Step 3 controlled apply UTC %s\nEvidence: %s\n' "$run_id" "$evidence" | tee "$evidence/summary.txt"

for host in mars backup; do
  test -s "$baseline/$host-installed-static.json" || {
    echo "FAIL: Missing accepted $host baseline" >&2; exit 1;
  }
done
for asset in collect-0045-host-state.py compare-0045-installed-state.py; do
  test -s "$tools/$asset" || { echo "FAIL: Missing tool $asset" >&2; exit 1; }
done

echo '=== Preflight: committed Playbooks and unchanged inventory choice ===' | tee -a "$evidence/summary.txt"
ssh mango 'bash -s' <<'CHECK_PLAYBOOKS' | tee "$evidence/playbooks-source-before.txt"
set -euo pipefail
cd /home/richard/playbooks
[[ "$(git branch --show-current)" == main ]]
git merge-base --is-ancestor 7dfa93fef6d975aa82f5f4cfdf54497b106e7645 HEAD
[[ "$(git rev-parse HEAD)" != 7dfa93fef6d975aa82f5f4cfdf54497b106e7645 ]]
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]]
[[ -z "$(git status --porcelain)" ]]
[[ -f backup-collection.yaml && -f scripts/backup-collection.sh ]]
if grep -q -- '--diff' scripts/backup-collection.sh; then
  # The help text may refer to --diff; reject only executable args that enable it.
  if grep -Eq 'args\+?=\(.*--diff' scripts/backup-collection.sh; then
    echo 'FAIL: launcher enables --diff' >&2; exit 1
  fi
fi
printf 'Playbooks commit: '; git rev-parse HEAD
printf 'Branch: '; git branch --show-current
printf 'PASS: source committed, clean, and published\n'
CHECK_PLAYBOOKS

# Docker apt-key was the sole predicted change during backup-collection --check.
# Its content is not in the v2 installed manifest; compare SHA-256 explicitly.
echo '=== Before: Docker signing key identity (mars) ===' | tee -a "$evidence/summary.txt"
ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' \
  | tee "$evidence/mars-docker-key-before.sha256"

echo '=== APPLY 1: backup-collection.yaml on mars ===' | tee -a "$evidence/summary.txt"
ssh mango 'cd /home/richard/playbooks && ANSIBLE_NOCOLOR=1 ansible-playbook backup-collection.yaml --limit mars --vault-password-file ~/.vault_pass.txt' \
  2>&1 | tee "$evidence/apply1-backup-collection.txt"

echo '=== APPLY 1: native btrfs-replication.yaml on mars and backup ===' | tee -a "$evidence/summary.txt"
ssh mango 'cd /home/richard/playbooks && ANSIBLE_NOCOLOR=1 ansible-playbook btrfs-replication.yaml --limit mars,backup --vault-password-file ~/.vault_pass.txt' \
  2>&1 | tee "$evidence/apply1-btrfs-replication.txt"

echo '=== After: static fingerprints ===' | tee -a "$evidence/summary.txt"
for host in mars backup; do
  ssh "$host" 'sudo -n python3 -' < "$tools/collect-0045-host-state.py" > "$evidence/$host-installed-static.json"
  python3 - "$evidence/$host-installed-static.json" "$host" <<'CHECK_MANIFEST'
import json, sys
m=json.load(open(sys.argv[1], encoding='utf-8'))
if m.get('schema') != '0045-static-installed-v2' or m.get('host') != sys.argv[2]:
    raise SystemExit('FAIL: invalid post-deployment manifest: ' + str(sys.argv[1]))
print('PASS: post-deployment manifest for ' + sys.argv[2])
CHECK_MANIFEST
  ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json status && sudo -n systemctl show btrfs-clear-stale-qgroups.service -p Result -p ExecMainStatus' \
    > "$evidence/$host-operational-readback.txt"
done

python3 "$tools/compare-0045-installed-state.py" "$baseline" "$evidence" \
  | tee "$evidence/installed-state-comparison.txt"

ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' \
  | tee "$evidence/mars-docker-key-after.sha256"
if ! cmp -s "$evidence/mars-docker-key-before.sha256" "$evidence/mars-docker-key-after.sha256"; then
  echo 'FAIL: Docker apt key changed; assess before accepting installation equivalence' | tee -a "$evidence/summary.txt" >&2
  exit 1
fi

echo 'PASS: initial apply and static installation comparison; idempotence apply still to be accepted separately' \
  | tee -a "$evidence/summary.txt"
printf 'Evidence directory: %s\n' "$evidence"
