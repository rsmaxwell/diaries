#!/usr/bin/env bash
set -euo pipefail

# Run from the Windows Diaries repository root. Read-only; does not disable quotas.
feature="change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention"
evidence="$feature/evidence/Step 12/performance"
mkdir -p "$evidence"
ssh -o BatchMode=yes mars 'sudo -n bash -s' > "$evidence/snapper-performance.txt" 2>&1 <<'REMOTE'
set -u
printf 'host=%s\n' "$(hostname)"
date -u '+date_utc=%Y-%m-%dT%H:%M:%SZ'
snapper --version
printf '\nOriginal inventory command, bounded to 60 seconds (read-only):\n'
start=$(date +%s)
timeout 60s snapper --no-dbus --csvout --iso -c @data list > /dev/null
rc=$?
end=$(date +%s)
printf 'original_exit=%s elapsed_seconds=%s\n' "$rc" "$((end-start))"
printf '\nWorkaround inventory command, bounded to 60 seconds (read-only):\n'
start=$(date +%s)
timeout 60s snapper --no-dbus --csvout --iso -c @data list --disable-used-space > /dev/null
rc=$?
end=$(date +%s)
printf 'workaround_exit=%s elapsed_seconds=%s\n' "$rc" "$((end-start))"
printf '\nQuota rescan status:\n'
btrfs quota rescan -s /media/usb
printf '\nDevice stats:\n'
btrfs device stats /media/usb
REMOTE
cat "$evidence/snapper-performance.txt"
if grep -q 'original_exit=0 ' "$evidence/snapper-performance.txt" && grep -q 'workaround_exit=0 ' "$evidence/snapper-performance.txt"; then
  echo 'PASS: both read-only inventory commands completed'
else
  echo 'NOTICE: an inventory command failed or timed out; preserve output, do not rerun cleanup'
fi
printf 'Evidence: %s\n' "$evidence/snapper-performance.txt"
