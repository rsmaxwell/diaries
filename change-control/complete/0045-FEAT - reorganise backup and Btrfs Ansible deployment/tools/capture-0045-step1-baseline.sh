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
  manifest="$evidence/$host-installed-static.json"
  if ! ssh "$host" 'sudo -n python3 -' < "$tools/collect-0045-host-state.py" \
      > "$manifest"; then
    printf 'FAIL: %s host collector returned a nonzero status; inspect stderr and %s\n' "$host" "$manifest" >&2
    exit 1
  fi
  # Confirm the schema emitted by the current collector; a simple grep can
  # silently fail when its expected schema is older than the collector.
  if ! python3 - "$manifest" "$host" <<'VERIFY_MANIFEST'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
host = sys.argv[2]
try:
    data = json.loads(path.read_text(encoding='utf-8'))
    expected_sections = (
        'managed', 'mutable_state_metadata', 'packages',
        'systemd_units', 'cron', 'acl', 'mount',
    )
    problems = []
    if data.get('schema') != '0045-static-installed-v2':
        problems.append('expected schema 0045-static-installed-v2; got ' + repr(data.get('schema')))
    if data.get('host') != host:
        problems.append('expected host ' + host + '; got ' + repr(data.get('host')))
    for section in expected_sections:
        if not isinstance(data.get(section), dict):
            problems.append('missing or invalid section ' + section)
    if not data.get('managed'):
        problems.append('managed-file section is empty')
    if problems:
        raise ValueError('; '.join(problems))
except (OSError, ValueError, TypeError, AttributeError) as exc:
    print(f'FAIL: {host} installed manifest validation: {exc}', file=sys.stderr)
    sys.exit(1)
print(f'PASS: {host} installed manifest schema and sections verified')
VERIFY_MANIFEST
  then
    printf 'FAIL: %s installed manifest invalid: %s\n' "$host" "$manifest" >&2
    exit 1
  fi
  # Extract only read-only health and service results. The snapshot-manager
  # status is mutable operational evidence, not compared as an installed file.
  if ! ssh "$host" 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json status && sudo -n systemctl show btrfs-clear-stale-qgroups.service -p Result -p ExecMainStatus' \
      > "$evidence/$host-operational-readback.txt"; then
    printf 'FAIL: %s read-only health capture failed\n' "$host" >&2
    exit 1
  fi
  printf 'PASS: %s installed manifest and health recorded\n' "$host" | tee -a "$evidence/capture-summary.txt"
done
printf 'FINISHED: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$evidence/capture-summary.txt"
printf '\nEvidence directory: %s\n' "$evidence"
