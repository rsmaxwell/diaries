#!/usr/bin/env bash
# 0037-FEAT Step 8. Read-only evidence capture; execute from Cygwin.
set -euo pipefail
feature="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
evidence="$feature/evidence/Step 08"
mkdir -p "$evidence"
# Every invocation is separately SSH executed; files are created only on Windows.
capture() {
  local name="$1" cmd="$2"
  printf 'Capturing %s on mars...\n' "$name"
  if ssh -o BatchMode=yes mars "$cmd" > "$evidence/$name.txt" 2>&1; then
    printf 'PASS %s (%s lines)\n' "$name" "$(wc -l < "$evidence/$name.txt")"
  else
    local code=$?
    printf 'FAIL %s (exit %s): inspect %s\n' "$name" "$code" "$evidence/$name.txt" >&2
    return "$code"
  fi
}
capture host-time 'hostname; date -u "+%Y-%m-%dT%H:%M:%SZ"; timedatectl show -p Timezone; findmnt -T /media/usb -o TARGET,SOURCE,FSTYPE,OPTIONS'
capture snapper-config-root 'sudo -n snapper -c root get-config'
capture snapper-config-data 'sudo -n snapper -c @data get-config'
capture snapper-csv-root 'sudo -n snapper --csvout --iso -c root list'
capture snapper-csv-data 'sudo -n snapper --csvout --iso -c @data list'
capture native-list 'sudo -n btrfs-snapshot-manager list'
capture native-status 'sudo -n btrfs-snapshot-manager status'
capture legacy-plan-text 'sudo -n btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'
capture legacy-plan-json 'sudo -n btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data --json'
capture timers 'systemctl list-timers --all --no-pager --plain; systemctl is-enabled btrfs-snapshot-create.timer btrfs-snapshot-prune.timer snapper-timeline.timer snapper-cleanup.timer 2>&1 || true'
printf 'Step 8 READ-ONLY captures completed. No deletion/prune/creation commands executed.\n'
