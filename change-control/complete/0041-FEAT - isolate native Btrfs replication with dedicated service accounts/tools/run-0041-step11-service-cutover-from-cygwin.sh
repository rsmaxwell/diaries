#!/usr/bin/env bash
# Windows Cygwin launcher. Remote bash runs non-interactively; ssh -T preserves stdin.
set -uo pipefail
mode="${1:-}"
if [[ $# -ne 1 || ( "$mode" != --preflight && "$mode" != --execute && "$mode" != --rollback ) ]]; then
  echo 'Usage: bash <this launcher> --preflight|--execute|--rollback' >&2
  exit 64
fi
feature_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd) || exit 1
remote_script="$feature_dir/tools/verify-0041-step11-service-cutover-on-mango.sh"
log_dir="$feature_dir/evidence/Step 11"
[[ -f "$remote_script" ]] || { echo "FAIL: missing $remote_script" >&2; exit 1; }
mkdir -p "$log_dir" || exit 1
log="$log_dir/service-${mode#--}-$(date -u +%Y%m%d-%H%M%SZ).txt"
echo "0041 Step 11 evidence: $log"
if [[ "$mode" == --execute ]]; then
  echo 'NOTICE: --execute changes the live 03:30 systemd service to run as btrfs-send. No transfer is invoked.'
elif [[ "$mode" == --rollback ]]; then
  echo 'NOTICE: --rollback restores the original root service and changes the Playbooks role default back to legacy.'
else
  echo 'Read-only preview; no production changes requested.'
fi
if ( set -o pipefail; ssh -T mango "bash -s -- $mode" < "$remote_script" 2>&1 | tee "$log" ); then
  case "$mode" in
  --execute) marker='PASS: 0041 Step 11 cutover of canonical sender service completed; next scheduled-cycle evidence outstanding' ;;
  --rollback) marker='PASS: 0041 Step 11 rollback of canonical sender service completed; dedicated credentials retained' ;;
  *) marker='PASS: 0041 Step 11 preflight completed; no production changes' ;;
  esac
  if grep -Fxq "$marker" "$log"; then
    echo "PASS: Step 11 $mode (log: $log)"
    exit 0
  fi
  echo "FAIL: remote script terminated without final acceptance marker (log: $log)" >&2
  exit 1
else
  rc=$?
  echo "FAIL: Step 11 $mode (exit $rc; log: $log)" >&2
  exit "$rc"
fi
