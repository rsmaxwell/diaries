#!/usr/bin/env bash
# Run in Windows Cygwin, from any working directory.
set -uo pipefail
feature_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) || exit 1
remote="$feature_dir/tools/verify-0041-step8-live-security-on-mango.sh"
evidence_dir="$feature_dir/evidence/Step 8"
[[ -f "$remote" ]] || { echo "FAIL: missing $remote" >&2; exit 1; }
mkdir -p "$evidence_dir" || exit 1
log="$evidence_dir/security-idempotence-$(date -u +%Y%m%d-%H%M%SZ).txt"
echo "0041 Step 8 evidence: $log"
if ( set -o pipefail; ssh -T mango 'bash -s' < "$remote" 2>&1 | tee "$log" ); then
  if grep -Fxq 'PASS: 0041 Step 8 security restrictions and idempotence verified; no Btrfs transfer performed' "$log"; then
    echo "PASS: 0041 Step 8 complete (log: $log)"
    exit 0
  fi
  echo "FAIL: remote process exited without final acceptance marker (log: $log)" >&2
  exit 1
else
  rc=$?
  echo "FAIL: 0041 Step 8 incomplete (exit $rc, log: $log)" >&2
  exit "$rc"
fi
