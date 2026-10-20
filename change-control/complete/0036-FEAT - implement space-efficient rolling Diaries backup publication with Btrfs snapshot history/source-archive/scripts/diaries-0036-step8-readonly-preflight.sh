#!/usr/bin/env bash
# Non-mutating Step 8 operator inventory. Usage: script [pluto|mars|backup]
set -euo pipefail
host="${1:-}"
case "$host" in pluto|mars|backup) ;; *) echo 'Usage: $0 {pluto|mars|backup}' >&2; exit 2;; esac
echo "=== Step 8 READ-ONLY: $host ==="
echo 'Host:'; hostname -f || hostname
echo 'Systemd timers (read-only):'; systemctl list-timers --all --no-pager 2>/dev/null | grep -Ei 'diaries|snapshot|btrfs' || true
echo 'Relevant unit status (read-only):'
for svc in diaries-complete-backup-publish.timer diaries-pull.timer; do
 systemctl is-enabled "$svc" 2>/dev/null || true
 systemctl is-active "$svc" 2>/dev/null || true
done
if [[ "$host" == pluto ]]; then
  echo 'Host NAS mount:'; findmnt /mnt/nas-diaries -o TARGET,SOURCE,FSTYPE,OPTIONS || true
  echo 'Publication (stat, no traversal):'; stat -c '%F %n -> %N' /home/richard/projects/diaries/data/diaries-backup 2>/dev/null || true
  echo 'Publication parent:'; ls -ld /home/richard/projects/diaries/data 2>/dev/null || true
fi
if [[ "$host" == mars || "$host" == backup ]]; then
  echo 'Btrfs mounts:'; findmnt -t btrfs -o TARGET,SOURCE,FSTYPE,OPTIONS || true
  echo 'Working dataset / marker / lock (no mutation):'
  for path in /media/usb/@data/backup/pluto/diaries-backup /media/usb/@data/backup/.diaries-snapshot-verified.json /media/usb/@data/backup/.btrfs-snapshot-writer.lock; do
    stat -c '%F %n -> %N' "$path" 2>/dev/null || true
  done
fi
echo 'READ-ONLY preflight complete; no approval to change services or paths.'
