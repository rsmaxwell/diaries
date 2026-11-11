#!/usr/bin/env bash
# Read-only reconciliation of the already-applied 0045 Step 3 deployment.
# Run as a standalone process from Windows Cygwin; does not execute Ansible.
set -euo pipefail

root="$(git -C "$(dirname "$0")" rev-parse --show-toplevel)"
feature="$root/change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment"
baseline="$feature/evidence/Step 1/baseline-20261111-111819Z"
run="$feature/evidence/Step 3/deployment-20261111-130143Z"
log="$run/postapply-runtime-reconciliation-$(date -u +%Y%m%d-%H%M%SZ).txt"

for name in mars backup; do
  test -s "$baseline/$name-installed-static.json" || { echo "Missing baseline for $name" >&2; exit 1; }
  test -s "$run/$name-installed-static.json" || { echo "Missing deployed manifest for $name" >&2; exit 1; }
done
test -s "$run/mars-docker-key-before.sha256" || { echo 'Missing Docker key before-hash' >&2; exit 1; }

{
  printf '%s\n' '=== Step 3: reconciled v2 static installation comparison ==='
  PYTHONDONTWRITEBYTECODE=1 python3 -B "$feature/tools/compare-0045-installed-state.py" "$baseline" "$run"

  printf '%s\n' '=== Step 3: verify loaded services are current (mars) ==='
  ssh mars 'bash -s' <<'REMOTE'
set -euo pipefail
for unit in \
  btrfs-clear-stale-qgroups.service \
  btrfs-native-push.service \
  btrfs-snapshot-create.service \
  btrfs-snapshot-prune.service \
  diaries-pull.service
do
  values="$(sudo -n systemctl show "$unit" --property=LoadState,NeedDaemonReload --no-pager)"
  printf '%s\n' "$values" | grep -Fxq 'LoadState=loaded' || { echo "FAIL: $unit is not loaded" >&2; exit 1; }
  printf '%s\n' "$values" | grep -Fxq 'NeedDaemonReload=no' || { echo "FAIL: $unit needs systemd daemon-reload" >&2; exit 1; }
  printf 'PASS: %s loaded and up to date\n' "$unit"
done
REMOTE

  printf '%s\n' '=== Step 3: Docker apt signing key remained unchanged ==='
  ssh mars 'sudo -n sha256sum /etc/apt/keyrings/docker.asc' > "$run/mars-docker-key-after.sha256"
  cmp -s "$run/mars-docker-key-before.sha256" "$run/mars-docker-key-after.sha256" || {
    echo 'FAIL: Docker signing key differs from pre-deployment state' >&2; exit 1;
  }
  echo 'PASS: Docker signing key unchanged'
  echo 'PASS: read-only reconciliation complete; Step 3 still requires acceptance review'
} 2>&1 | tee "$log"
