#!/usr/bin/env bash
# 0041 Step 12: run one read-only evidence collection from Windows Cygwin.
# Use bash as a standalone process; never affect interactive shell error options.
set -Eeuo pipefail
repo='/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
feature='change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts'
cd "$repo"
script="$feature/tools/verify-0041-step12-scheduled-on-mango.sh"
[[ -f "$script" ]] || { printf 'FAIL: missing remote verification script: %s\n' "$script" >&2; exit 1; }
output="$feature/evidence/Step 12/scheduled-replication-$(date -u +%Y%m%d-%H%M%SZ).txt"
mkdir -p "$(dirname "$output")"
printf '0041 Step 12 evidence: %s\n' "$repo/$output"
printf 'Collecting read-only scheduled-run evidence via mango. No Btrfs operation or Ansible deployment.\n'
if ssh -o BatchMode=yes mango 'bash -s' < "$script" 2>&1 | tee "$output"; then
  # With pipefail enabled, this means the remote check and local tee succeeded.
  printf 'PASS: Step 12 scheduled-cycle verification (log: %s)\n' "$repo/$output"
else
  status=$?
  printf 'FAIL: Step 12 incomplete (exit %s; log: %s)\n' "$status" "$repo/$output" >&2
  exit "$status"
fi
