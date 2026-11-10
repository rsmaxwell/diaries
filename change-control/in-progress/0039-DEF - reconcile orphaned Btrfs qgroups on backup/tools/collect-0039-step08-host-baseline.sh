#!/usr/bin/env bash
# 0039-DEF Step 8. Run in the Windows Cygwin terminal from the Diaries repo root.
# Captures read-only source/receiver diagnostics directly into the feature tree;
# no snapshot, qgroup, timer or service is modified by this script.
set -euo pipefail

if [[ $# -ne 1 || ( $1 != mars && $1 != backup ) ]]; then
  echo 'Usage: bash "change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup/tools/collect-0039-step08-host-baseline.sh" mars|backup' >&2
  exit 2
fi
host=$1
if [[ $host == mars ]]; then fs=/media/usb; else fs=/; fi
feature='change-control/in-progress/0039-DEF - reconcile orphaned Btrfs qgroups on backup'
if [[ ! -d "$feature/evidence/Step 08" ]]; then
  echo "ERROR: Run from the Windows Diaries repository root (missing $feature/evidence/Step 08)" >&2
  exit 2
fi
stamp=$(date -u +'%Y%m%d-%H%M%SZ')
out="$feature/evidence/Step 08/${host}-baseline-${stamp}.txt"

echo "Capturing read-only baseline from $host into: $out" >&2
# Exit status of ssh is preserved by pipefail; an authentication or sudo error
# must not be reported as a successful baseline.
ssh -o BatchMode=yes "$host" bash -s -- "$fs" "$host" <<'REMOTE' 2>&1 | tee "$out"
set -uo pipefail
fs=$1
host=$2
fail=0
run_required() {
  printf '\n===== %s =====\n' "$*"
  "$@"
  rc=$?
  printf 'RESULT rc=%s\n' "$rc"
  if (( rc != 0 )); then fail=1; fi
}
run_optional() {
  printf '\n===== %s =====\n' "$*"
  "$@"
  rc=$?
  printf 'OPTIONAL RESULT rc=%s\n' "$rc"
}
printf '0039-DEF Step 8 read-only baseline host=%s fs=%s utc=' "$host" "$fs"
date -u +'%Y-%m-%dT%H:%M:%SZ'
run_required hostname -f
run_required uname -a
run_required btrfs version
run_required findmnt -n -o TARGET,FSTYPE,UUID --mountpoint "$fs"
run_optional systemctl is-enabled btrfs-clear-stale-qgroups.timer
run_optional systemctl is-active btrfs-clear-stale-qgroups.timer
run_optional systemctl list-timers --all btrfs-clear-stale-qgroups.timer
run_optional systemctl status --no-pager -l btrfs-clear-stale-qgroups.service
run_optional sudo -n sha256sum /usr/local/sbin/btrfs-snapshot-manager /usr/local/sbin/btrfs-clear-stale-qgroups
run_optional sudo -n python3 -c 'import json; d=json.load(open("/etc/btrfs-stale-qgroups.json")); print(d)' 
run_required sudo -n python3 -c 'import json; d=json.load(open("/etc/btrfs-snapshot-manager.json")); print({k:d.get(k) for k in ("mode","snapshot_root","lock_path","writer_lock_path","receiver_state_dir")})'
run_required sudo -n btrfs qgroup show "$fs"
run_required sudo -n btrfs subvolume list "$fs"
run_optional sudo -n btrfs qgroup --help
printf '\nSTEP08_BASELINE_STATUS=%s\n' "$([[ $fail == 0 ]] && echo PASS || echo FAIL)"
exit "$fail"
REMOTE
rc=${PIPESTATUS[0]}
if (( rc != 0 )); then
  echo "FAIL: host $host baseline returned $rc. Preserve $out and investigate missing evidence." >&2
  exit "$rc"
fi
echo "PASS: captured $out (read-only)." >&2
