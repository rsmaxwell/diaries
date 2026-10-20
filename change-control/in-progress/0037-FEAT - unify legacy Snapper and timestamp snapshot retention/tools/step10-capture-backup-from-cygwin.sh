#!/usr/bin/env bash
# 0037-FEAT Step 10 — backup receiver read-only evidence (no deletion/approval).
set -euo pipefail
feature="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$feature/evidence/Step 10/receiver-preflight"
mkdir -p "$out"
host="${STEP10_BACKUP_SSH:-backup}"
capture() {
  local name="$1" command="$2"
  printf 'Capturing %s on %s\n' "$name" "$host"
  if ! ssh "$host" "$command" >"$out/$name.txt" 2>&1; then
    printf 'FAILED: %s (see %s)\n' "$name" "$out/$name.txt" >&2
    exit 1
  fi
}
capture host 'set -e; hostname; date -u +%FT%TZ; timedatectl show -p Timezone; findmnt -t btrfs -o TARGET,SOURCE,FSTYPE,OPTIONS'
capture receiver-path 'set -e; sudo -n test -d /@data/mars-received/@data; sudo -n ls -ld /@data/mars-received /@data/mars-received/@data /@data/mars-received/.replication-state; sudo -n stat -c "%U:%G %a %n" /@data/mars-received /@data/mars-received/@data /@data/mars-received/.replication-state'
capture received-subvolumes 'set -e; sudo -n btrfs subvolume list / | grep -F "path @data/mars-received/@data/"'
capture latest-received 'set -e; latest=$(sudo -n find /@data/mars-received/@data -mindepth 1 -maxdepth 1 -type d -name "????????-??????Z" -printf "%f\n" | LC_ALL=C sort | tail -n 1); test -n "$latest"; printf "LATEST_RECEIVED=%s\n" "$latest"; sudo -n btrfs subvolume show "/@data/mars-received/@data/$latest"; sudo -n btrfs property get -ts "/@data/mars-received/@data/$latest" ro'
capture btrfs-health 'set -e; sudo -n btrfs filesystem usage -b /; sudo -n btrfs device stats /'
capture timers 'set -e; systemctl list-timers --all --no-pager; systemctl --failed --no-pager --plain'
capture replication-processes 'ps -eo pid,stat,etime,args | grep -E "[b]trfs (send|receive)|[d]iaries.*(replicat|push)|[m]ars.*(replicat|push)" || true'
capture replication-metadata-listing 'set -e; sudo -n find /@data/mars-received/.replication-state -maxdepth 2 -type f -printf "%TY-%Tm-%TdT%TH:%TM:%TS %s %p\n" | LC_ALL=C sort'
(cd "$out" && sha256sum -- *.txt > SHA256SUMS.txt)
printf 'PASS: receiver read-only capture completed -> %s\n' "$out"
printf 'No approval, deletion, pruning or replication action performed.\n'
