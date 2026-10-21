#!/usr/bin/env bash
# Step 11 pre-execution evidence only. No snapshot mutation and no approval-file creation.
set -euo pipefail
here="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
feature="$(cd -- "$here/.." && pwd)"
out="$feature/evidence/Step 11/pre-execution"
mkdir -p "$out/mars" "$out/backup"

capture() {
  local host="$1" filename="$2" command="$3"
  echo "Capturing $host/$filename"
  if ! ssh -o BatchMode=yes "$host" "$command" >"$out/$host/$filename.txt" 2>&1; then
    echo "FAILED: $host/$filename — see $out/$host/$filename.txt" >&2
    exit 1
  fi
}

capture mars host 'hostname; date -u --iso-8601=seconds; timedatectl show -p Timezone'
capture mars manager 'sudo sha256sum /usr/local/sbin/btrfs-snapshot-manager; sudo btrfs-snapshot-manager --help'
capture mars status 'sudo btrfs-snapshot-manager status'
capture mars plan-text 'sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'
capture mars plan-json 'sudo btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data --json'
capture mars legacy-inventory 'sudo snapper --csvout --iso -c @data list'
capture mars candidate-subvolume 'sudo btrfs subvolume show /media/usb/@data/.snapshots/19605/snapshot'
capture mars candidate-readonly 'sudo btrfs property get -ts /media/usb/@data/.snapshots/19605/snapshot ro'
capture mars native-list 'sudo btrfs-snapshot-manager list'
capture mars native-dry-run 'sudo btrfs-snapshot-manager prune --dry-run'
capture mars checkpoint-holds 'sudo btrfs-snapshot-manager hold-list'
capture mars timers 'systemctl list-timers --all --no-pager'
capture mars current-jobs "ps -eo pid,stat,args | grep -E '[b]trfs (send|receive)|[s]napper|[b]trfs-snapshot-manager|[d]iaries.*(push|pull)' || true"
capture mars failures 'systemctl --failed --no-pager'
capture backup host 'hostname; date -u --iso-8601=seconds'
capture backup receiver 'sudo ls -ld /@data/mars-received /@data/mars-received/@data'
capture backup recent-receipts "sudo find /@data/mars-received/.replication-state -maxdepth 2 -type f -printf '%TY-%Tm-%TdT%TH:%TM:%TS %p\n' | sort | tail -30"
capture backup recent-subvolumes "sudo btrfs subvolume list -o /@data/mars-received/@data | tail -30"
capture backup current-jobs "ps -eo pid,stat,args | grep -E '[b]trfs (send|receive)|[d]iaries.*(push|pull)' || true"

if ! grep -Eq '^WOULD-DELETE[[:space:]]+@data[[:space:]]+@data[[:space:]]+19605[[:space:]]' "$out/mars/plan-text.txt"; then
  echo 'STOP: 19605 is not a WOULD-DELETE decision in the fresh plan.' >&2
  exit 1
fi
if ! grep -Fq 'ro=true' "$out/mars/candidate-readonly.txt"; then
  echo 'STOP: 19605 was not confirmed read-only.' >&2
  exit 1
fi
(
 cd "$out"
 find mars backup -type f -name '*.txt' -print0 | sort -z | xargs -0 sha256sum
) > "$out/SHA256SUMS.txt"
echo 'Read-only pre-execution capture complete. Pilot NOT authorised for execution by this script.'
echo "Evidence: $out"
echo 'Review exact subvolume UUID, subvolume ID, active operations, holds, pins, receiver metadata and candidate retention before go/no-go.'
