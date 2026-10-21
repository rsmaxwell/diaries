#!/usr/bin/env bash
# 0037-FEAT Step 10 — read-only operator acceptance evidence (no approval/deletion)
set -euo pipefail
feature="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$feature/evidence/Step 10/fresh-preflight"
mkdir -p "$out"
host="${STEP10_MARS_SSH:-mars}"
capture() {
  local name="$1" command="$2"
  echo "Capturing $name on $host"
  if ! ssh "$host" "$command" > "$out/$name.txt" 2>&1; then
    echo "FAILED: $name — inspect $out/$name.txt" >&2
    exit 1
  fi
}
capture host 'set -e; hostname; date -u +%FT%TZ; timedatectl show -p Timezone'
capture manager 'set -e; sha256sum /usr/local/sbin/btrfs-snapshot-manager; sudo -n btrfs-snapshot-manager --help'
capture plan-text 'sudo -n btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'
capture plan-json 'sudo -n btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data --json'
capture snapper-config 'set -e; sudo -n snapper -c root get-config; sudo -n snapper -c @data get-config'
capture snapper-data 'sudo -n snapper --csvout --iso -c @data list'
capture snapper-root 'sudo -n snapper --csvout --iso -c root list'
capture candidate-19605 'set -e; sudo -n btrfs subvolume show /media/usb/@data/.snapshots/19605/snapshot; sudo -n btrfs property get -ts /media/usb/@data/.snapshots/19605/snapshot ro; sudo -n stat -c "%U:%G %a %n" /media/usb/@data/.snapshots/19605/snapshot'
capture native-status 'sudo -n btrfs-snapshot-manager status'
capture native-list 'sudo -n btrfs-snapshot-manager list'
capture native-prune-dry-run 'sudo -n btrfs-snapshot-manager prune --dry-run'
capture timer-state 'set -e; systemctl is-enabled btrfs-snapshot-create.timer btrfs-snapshot-prune.timer; systemctl list-timers --all --no-pager; systemctl --no-pager --plain show -p ActiveState -p SubState btrfs-snapshot-create.service btrfs-snapshot-prune.service'
capture current-jobs 'ps -eo pid,stat,etime,args | grep -E "[b]trfs-snapshot-manager|[b]trfs (send|receive)|[s]napper.*delete|[d]iaries.*replicat" || true'
capture journal 'sudo -n journalctl -u btrfs-snapshot-create.service -u btrfs-snapshot-prune.service --since "24 hours ago" --no-pager -n 120'
(cd "$out" && sha256sum -- *.txt > SHA256SUMS.txt)
echo "PASS: Step 10 read-only capture completed at $out"
echo 'No approval was created and no deletion executed.'
