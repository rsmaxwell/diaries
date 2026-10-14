#!/usr/bin/env bash
# 0034 Step 11.1 — read-only per-host capture. No transfer, prune, restore, or deployment.
set -euo pipefail
host=$(hostname -s)
case "$host" in pluto|mars|backup|mango) ;; *) echo "Unexpected host: $host" >&2; exit 2;; esac
stamp=$(date -u +%Y%m%d-%H%M%SZ)
out="${1:-$HOME/0034-step11-1-$host-$stamp}"
mkdir -p -- "$out"
chmod 700 "$out"
run() { local label=$1; shift; { printf 'host=%s utc=%s\ncommand=' "$host" "$(date -u +%FT%TZ)"; printf '%q ' "$@"; printf '\n'; "$@"; } > "$out/$label.txt" 2>&1 || { printf 'FAILED %s rc=%s\n' "$label" "$?" >> "$out/ERRORS.txt"; }; }
run identity bash -c 'hostname -f; date -u --iso-8601=seconds; uname -a; id'
run mounts bash -c 'findmnt -t btrfs,ext4 -o TARGET,SOURCE,FSTYPE,OPTIONS; df -hT'
run timers bash -c 'systemctl list-timers --all --no-pager; systemctl is-active btrfs-snapshot-create.timer btrfs-snapshot-prune.timer || true'
run git-playbooks bash -c 'if test -d /home/richard/playbooks/.git; then git -C /home/richard/playbooks rev-parse HEAD; git -C /home/richard/playbooks status --short; else echo "no local playbooks checkout"; fi'
case "$host" in
 mars)
   run source-snapshot bash -c 'sudo -n btrfs subvolume show /media/usb/@snapshots/@data/20261013-180016Z; sudo -n btrfs subvolume show /media/usb/@snapshots/@data/20261013-171228Z'
   run snapshots bash -c 'sudo -n btrfs subvolume list -r /media/usb'
   run protection bash -c 'sudo -n btrfs-snapshot-manager hold-list; sudo -n btrfs-snapshot-manager prune --dry-run; sudo -n cat /media/usb/@snapshots/.replication-protection.json'
   run backup-inventory bash -c 'find /media/usb/@data/backup -maxdepth 4 -type d -print | head -200; test -f /media/usb/@snapshots/@data/20261013-171228Z/backup/mango/home/richard/playbooks/native-btrfs.yaml; test -f /media/usb/@snapshots/@data/20261013-171228Z/backup/mars/home/richard/scripts/backup/backup.sh; echo "checkpoint-content-tests=passed"'
   run push-installed bash -c 'command -v btrfs-native-push; sha256sum /usr/local/bin/btrfs-native-push; systemctl list-unit-files --no-pager | grep -Ei "btrfs|rsync" || true'
   ;;
 backup)
   run received-snapshots bash -c 'sudo -n btrfs subvolume show /@data/mars-received/@data/20261013-171228Z; sudo -n btrfs subvolume show /@data/mars-received/@data/20261013-180016Z; sudo -n btrfs subvolume list -r /'
   run receipts bash -c 'sudo -n cat /@data/mars-received/.replication-state/20261013-171228Z.json /@data/mars-received/.replication-state/20261013-180016Z.json'
   run restored-content bash -c 'test -f /@data/mars-received/@data/20261013-171228Z/backup/mango/home/richard/playbooks/native-btrfs.yaml; test -f /@data/mars-received/@data/20261013-171228Z/backup/mars/home/richard/scripts/backup/backup.sh; echo "received-checkpoint-content-tests=passed"'
   run receiver-installed bash -c 'test -x /usr/local/bin/btrfs-native-push-receiver; test ! -e /usr/local/bin/btrfs-native-pull; test ! -e /usr/local/libexec/whole-backup-pull.py; sha256sum /usr/local/bin/btrfs-native-push-receiver'
   ;;
 pluto)
   run production-location bash -c 'find /home/richard -maxdepth 5 -name dataset-manifest.json -o -name "*backup*" | head -150'
   run production-services bash -c 'systemctl list-timers --all --no-pager; docker ps --format "{{.Names}} {{.Image}} {{.Status}}" 2>/dev/null || true'
   ;;
 mango)
   run source-git bash -c 'git -C /home/richard/playbooks log -1 --format="%H%n%s%n%cI"; git -C /home/richard/playbooks status --porcelain=v1'
   ;;
esac
( cd "$out" && sha256sum ./*.txt > SHA256SUMS.txt )
printf 'Evidence directory: %s\n' "$out"
if [[ -s "$out/ERRORS.txt" ]]; then echo 'Some capture commands FAILED: inspect ERRORS.txt (do not mark accepted)' >&2; exit 1; fi
