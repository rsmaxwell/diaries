#!/usr/bin/env bash
# 0041 Step 7: safe short launcher from Windows Cygwin.
# Run: bash 'change-control/in-progress/0041-FEAT - isolate native Btrfs replication with dedicated service accounts/tools/run-0041-step7-additive-from-cygwin.sh'
set -uo pipefail
feature_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) || exit 1
remote_script="$feature_dir/tools/deploy-0041-step7-additive-on-mango.sh"
evidence_dir="$feature_dir/evidence/Step 7"
[[ -f "$remote_script" ]] || { echo "FAIL: script missing: $remote_script" >&2; exit 1; }
mkdir -p "$evidence_dir" || exit 1
log="$evidence_dir/additive-provision-$(date -u +%Y%m%d-%H%M%SZ).txt"
echo "Writing 0041 evidence: $log"
echo 'Running mango non-interactive deployment script; nested SSH will not consume script input.'
if ( set -o pipefail; ssh -T mango 'bash -s' < "$remote_script" 2>&1 | tee "$log" ); then
  if grep -Fxq 'PASS: 0041 additive provisioning and dedicated-status check verified' "$log"; then
    echo "PASS: complete 0041 Step 7 additive provisioning (log: $log)"
    exit 0
  fi
  echo "FAIL: remote process returned zero without final acceptance marker (log: $log)" >&2
  exit 1
else
  rc=$?
  echo "FAIL: 0041 Step 7 incomplete (exit $rc; log: $log)" >&2
  exit "$rc"
fi
