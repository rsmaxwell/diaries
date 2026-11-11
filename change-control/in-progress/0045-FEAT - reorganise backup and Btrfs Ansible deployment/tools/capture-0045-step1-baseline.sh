#!/usr/bin/env bash
# 0045 Step 1 - run from the authoritative Windows Cygwin Diaries checkout.
# Does not run Ansible apply, mutate hosts, prune, or access Vault plaintext.
set -euo pipefail
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
feature='change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment'
tools="$feature/tools"
test -f "$tools/collect-0045-controller.sh"
test -f "$tools/collect-0045-host-state.py"
test "$(git branch --show-current)" = main
# Verify closure and that the new planned feature is present.
test -d 'change-control/complete/0039-DEF - reconcile orphaned Btrfs qgroups on backup'
test -d 'change-control/complete/0043-FEAT - centralise Btrfs maintenance schedules'
test -d 'change-control/in-progress/0046-FEAT - move non-sensitive Ansible inventory into Playbooks Git'
run_id="$(date -u +%Y%m%d-%H%M%SZ)"
evidence="$feature/evidence/Step 1/baseline-$run_id"
mkdir -p "$evidence"
printf '0045 Step 1 baseline capture started UTC %s\n' "$run_id" | tee "$evidence/capture-summary.txt"

{
  printf '=== Windows Diaries parent ===\n'
  git branch --show-current
  git rev-parse HEAD
  git status --short --branch
  git submodule status
  printf '\n=== Relevant closure and planning documents ===\n'
  for f in \
    'change-control/complete/0039-DEF - reconcile orphaned Btrfs qgroups on backup/README.md' \
    'change-control/complete/0043-FEAT - centralise Btrfs maintenance schedules/README.md' \
    "$feature/README.md"; do
    sha256sum "$f"
  done
} > "$evidence/diaries-source.txt"
printf 'PASS: Windows Diaries revision and submodules recorded\n' | tee -a "$evidence/capture-summary.txt"

printf '=== Capture mango source/inventory topology ===\n'
ssh mango 'bash -s' < "$tools/collect-0045-controller.sh" > "$evidence/mango-source-and-inventory.txt"
printf 'PASS: mango read-only source/inventory topology recorded\n' | tee -a "$evidence/capture-summary.txt"

for host in mars backup; do
  printf '=== Capture %s static installed manifest ===\n' "$host"
  ssh "$host" 'sudo -n python3 -' < "$tools/collect-0045-host-state.py" \
    > "$evidence/$host-installed-static.json"
  # Extract only read-only health and service results. The snapshot-manager
  # status is mutable operational evidence, not compared as an installed file.
  ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json status && sudo -n systemctl show btrfs-clear-stale-qgroups.service -p Result -p ExecMainStatus' \
    > "$evidence/$host-operational-readback.txt"
  grep -Fq '"schema": "0045-static-installed-v1"' "$evidence/$host-installed-static.json"
  grep -Fq "\"host\": \"$host\"" "$evidence/$host-installed-static.json"
  printf 'PASS: %s installed manifest and health recorded\n' "$host" | tee -a "$evidence/capture-summary.txt"
done
printf 'FINISHED: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$evidence/capture-summary.txt"
printf '\nEvidence directory: %s\n' "$evidence"
