#!/usr/bin/env bash
# Step 10 Cygwin launcher: --preflight is read-only; --execute is one live transfer.
set -uo pipefail
mode="${1:-}"
if [[ $# -ne 1 || ( "$mode" != --preflight && "$mode" != --execute ) ]]; then
  echo 'Usage: bash <this-launcher> --preflight|--execute' >&2
  exit 64
fi
feature_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) || exit 1
remote_script="$feature_dir/tools/verify-0041-step10-dedicated-cycle-on-mango.sh"
log_dir="$feature_dir/evidence/Step 10"
[[ -f "$remote_script" ]] || { echo "FAIL: script missing: $remote_script" >&2; exit 1; }
mkdir -p "$log_dir" || exit 1
log="$log_dir/step10-${mode#--}-$(date -u +%Y%m%d-%H%M%SZ).txt"
echo "0041 Step 10 evidence: $log"
if [[ $mode == --execute ]]; then
  echo 'NOTICE: --execute authorises ONE production Btrfs incremental replication via dedicated identities.'
  echo 'The existing production 03:30 timer remains unchanged; snapshot receive and agreed-parent advancement are expected.'
else
  echo 'Read-only preflight; no Btrfs transfer requested.'
fi
if ( set -o pipefail; ssh -T mango "bash -s -- $mode" < "$remote_script" 2>&1 | tee "$log" ); then
  if [[ $mode == --execute ]]; then
    marker='PASS: 0041 Step 10 dedicated production incremental cycle complete'
  else
    marker='PASS: 0041 Step 10 preflight-only complete; no transfer or state changes'
  fi
  if grep -Fxq "$marker" "$log"; then
    echo "PASS: Step 10 $mode (log: $log)"
    exit 0
  fi
  echo "FAIL: premature remote termination; final acceptance marker absent (log: $log)" >&2
  exit 1
else
  rc=$?
  echo "FAIL: Step 10 $mode incomplete (exit $rc; log: $log)" >&2
  exit "$rc"
fi
