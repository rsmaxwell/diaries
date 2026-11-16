#!/usr/bin/env bash
# 0049-FEAT live acceptance read-back; source and receiver; no state mutations.
# Run from mango, after the feature directory is synchronised from the Windows repo.
set -u
fail=0
run() {
  printf '\n>>> %s\n' "$*"
  "$@"
  rc=$?
  printf 'EXIT=%s\n' "$rc"
  if [ "$rc" -ne 0 ]; then fail=1; fi
}
readback() {
  local host="$1" old_timer="$2" new_timer="$3" service="$4" parent="$5"
  printf '\n===== HOST %s =====\n' "$host"
  run ssh -o BatchMode=yes "$host" "systemctl show '$old_timer' '$new_timer' -p Id -p LoadState -p ActiveState -p UnitFileState -p NextElapseUSecRealtime --no-pager"
  run ssh -o BatchMode=yes "$host" "systemctl cat '$service' --no-pager"
  run ssh -o BatchMode=yes "$host" "sudo -n stat -c '%a %U:%G %n' '$parent'"
  run ssh -o BatchMode=yes "$host" "sudo -n sha256sum '$parent'"
  run ssh -o BatchMode=yes "$host" 'sudo -n btrfs-backup-status --local-only --json'
  run ssh -o BatchMode=yes "$host" 'sudo -n btrfs-snapshot-manager list'
  run ssh -o BatchMode=yes "$host" 'sudo -n btrfs-snapshot-manager prune --dry-run'
  # This checks timer exclusivity explicitly; it cannot start either service.
  run ssh -o BatchMode=yes "$host" "bash -c 'if systemctl -q is-active \"$old_timer\" && systemctl -q is-active \"$new_timer\"; then echo FAIL-DUPLICATE-TIMERS; exit 1; fi; if ! systemctl -q is-active \"$new_timer\"; then echo FAIL-NEW-TIMER-INACTIVE; exit 1; fi; echo PASS-EXACTLY-ONE-CURRENT-TIMER'"
}
readback mars btrfs-native-push.timer btrfs-push.timer btrfs-push.service /media/usb/@snapshots/.simple-agreed-parent.json
readback backup btrfs-receiver-simple-prune.timer btrfs-receiver-prune.timer btrfs-receiver-prune.service /@data/mars-received/.replication-state/.simple-agreed-parent.json
printf '\nOVERALL LIVE READ-BACK EXIT=%s\n' "$fail"
exit "$fail"
