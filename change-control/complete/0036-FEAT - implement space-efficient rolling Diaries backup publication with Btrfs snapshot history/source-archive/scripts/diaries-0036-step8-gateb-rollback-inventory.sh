#!/usr/bin/env bash
# Gate B: read-only rollback inventory. Never dumps Ansible vault, Environment=, or secret files.
set -euo pipefail
host="${1:-}"
case "$host" in pluto|mars|backup) ;; *) echo "usage: $0 {pluto|mars|backup}" >&2; exit 2;; esac
printf 'GATE_B_HOST=%s\nCAPTURE_UTC=%s\n' "$host" "$(date -u +%FT%TZ)"
printf 'HOSTNAME=%s\n' "$(hostname -f 2>/dev/null || hostname)"
printf 'OS_TIME=%s\n' "$(date --iso-8601=seconds)"
for unit in diaries-complete-backup-publish.timer diaries-complete-backup-publish.service diaries-pull.timer diaries-pull.service btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-native-push.timer btrfs-native-push.service; do
  printf '\nUNIT=%s\n' "$unit"
  systemctl show "$unit" --no-pager --property=LoadState,ActiveState,UnitFileState,FragmentPath,DropInPaths,NextElapseUSecRealtime,LastTriggerUSec 2>/dev/null || true
  file=$(systemctl show "$unit" --value --property=FragmentPath 2>/dev/null || true)
  if [[ -n "$file" && -f "$file" ]]; then sha256sum -- "$file"; fi
done
if [[ "$host" == pluto ]]; then
  parent=/home/richard/projects/diaries/data
  link="$parent/diaries-backup"
  printf '\nPUBLICATION=%s\n' "$link"
  if [[ -L "$link" ]]; then
    printf 'LINK_TARGET=%s\n' "$(readlink -- "$link")"
    printf 'RESOLVED_TARGET=%s\n' "$(readlink -f -- "$link")"
    stat -Lc 'RESOLVED_STAT=%F %U:%G %n' -- "$link"
  else printf 'ERROR=publication is not a symlink\n'; fi
  findmnt -T /mnt/nas-diaries -o TARGET,SOURCE,FSTYPE,OPTIONS || true
  for path in "$parent" "$parent/.diaries-backup-generations"; do [[ ! -e "$path" ]] || stat -c 'DIR=%F %U:%G %n' -- "$path"; done
elif [[ "$host" == mars ]]; then
  link=/media/usb/@data/backup/pluto/diaries-backup
  printf '\nPUBLICATION=%s\n' "$link"
  if [[ -L "$link" ]]; then
    printf 'LINK_TARGET=%s\n' "$(readlink -- "$link")"
    printf 'RESOLVED_TARGET=%s\n' "$(readlink -f -- "$link")"
    stat -Lc 'RESOLVED_STAT=%F %U:%G %n' -- "$link"
  else printf 'ERROR=publication is not a symlink\n'; fi
  for path in /media/usb/@data/backup/.diaries-snapshot-verified.json /media/usb/@data/backup/.btrfs-snapshot-writer.lock; do
    [[ ! -f "$path" ]] || { stat -c 'CONTROL=%F %U:%G %n' -- "$path"; sha256sum -- "$path"; }
  done
  findmnt -T /media/usb/@data -o TARGET,SOURCE,FSTYPE,OPTIONS || true
fi
if [[ "$host" == mars || "$host" == backup ]]; then
  printf '\nBTRFS_SUBVOLUMES_READ_ONLY=\n'
  if [[ "$host" == mars ]]; then mount=/media/usb; else mount=/; fi
  btrfs subvolume list -r -u -q -- "$mount" 2>&1 | tail -n 45 || true
fi
printf '\nGIT_REVISIONS=\n'
for d in /home/richard/playbooks /home/richard/projects/diaries /home/richard/projects/diaries-application/diaries; do
  if [[ -d "$d/.git" ]]; then printf '%s ' "$d"; git -C "$d" rev-parse HEAD 2>/dev/null || true; fi
done
printf '\nGATE_B_READ_ONLY_COMPLETE=1\n'
