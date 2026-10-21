#!/usr/bin/env bash
set -euo pipefail
feature="change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention"
[ -d "$feature" ] || { echo "Run from the Diaries repository root" >&2; exit 2; }
out="$feature/evidence/Step 11/operational-check"
mkdir -p "$out"
ssh mars 'hostname; date -Is; systemctl status snapper-timeline.service --no-pager || true; systemctl list-timers --all --no-pager | grep -E "snapper|btrfs-snapshot|diaries" || true; systemctl is-enabled snapper-timeline.timer snapper-cleanup.timer 2>&1 || true; systemctl is-active snapper-timeline.timer snapper-cleanup.timer 2>&1 || true; ps -eo pid,ppid,stat,etime,args | grep -E "[s]napper|[b]trfs (send|receive)|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)" || true; journalctl -u snapper-timeline.service -n 35 --no-pager || true' > "$out/mars-operational.txt" 2>&1
sha256sum "$out/mars-operational.txt" > "$out/SHA256SUMS.txt"
echo "Read-only operational evidence saved: $out"
echo "NO approval file created; NO deletion executed."
