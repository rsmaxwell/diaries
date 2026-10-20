#!/usr/bin/env bash
# Read-only 0036 Gate C freshness and layout check. Refuses unexpected production layout.
set -euo pipefail
host="${1:?Usage: bash gate-c-precheck.sh pluto|mars}"
case "$host" in
 pluto) publication=/home/richard/projects/diaries/data/diaries-backup; timer=diaries-complete-backup-publish.timer ;;
 mars) publication=/media/usb/@data/backup/pluto/diaries-backup; timer=diaries-pull.timer ;;
 *) echo 'Only pluto/mars accepted' >&2; exit 2;;
esac
[[ -L "$publication" ]] || { echo "STOP: publication no longer symlink: $publication" >&2;exit 2; }
target="$(readlink -- "$publication")"
[[ "$target" == .diaries-backup-generations/* ]] || { echo "STOP: unexpected link target: $target" >&2;exit 2; }
[[ -d "$publication" && ! -L "$(dirname "$publication")" ]] || { echo 'STOP: missing generation or unsafe parent' >&2;exit 2; }
unit_state="$(systemctl is-active "$timer" 2>/dev/null || true)"
printf 'HOST=%s\nPUBLICATION=%s\nLINK_TARGET=%s\nRESOLVED=%s\nTIMER=%s\nTIMER_ACTIVE=%s\n' "$host" "$publication" "$target" "$(readlink -f -- "$publication")" "$timer" "$unit_state"
if [[ "$host" == mars ]]; then
 findmnt -T /media/usb/@data -n -o FSTYPE | grep -qx btrfs || { echo 'STOP: mars working tree not Btrfs' >&2;exit 2; }
 for f in /media/usb/@data/backup/.btrfs-snapshot-writer.lock /media/usb/@data/backup/.diaries-snapshot-verified.json;do
  [[ -f "$f" && ! -L "$f" ]] || { echo "STOP: missing marker or lock: $f" >&2;exit 2; }
 done
fi
printf 'GATE_C_READ_ONLY_PREFLIGHT_PASS=1\n'
