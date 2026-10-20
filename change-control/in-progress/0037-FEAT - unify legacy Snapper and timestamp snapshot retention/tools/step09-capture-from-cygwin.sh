#!/usr/bin/env bash
# Step 9 read-only state capture: Cygwin -> SSH mars; evidence stays in Diaries.
set -euo pipefail
phase="${1:-}"
if [[ "$phase" != pre && "$phase" != post ]]; then echo "Usage: bash tools/step09-capture-from-cygwin.sh pre|post" >&2; exit 2; fi
root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
out="$root/evidence/Step 09/$phase"
mkdir -p "$out"
ssh_target="${STEP09_MARS_SSH:-mars}"
capture() { local name="$1" cmd="$2"; echo "Capturing $phase/$name"; ssh "$ssh_target" "$cmd" > "$out/$name.txt" 2>&1 || { echo "FAIL $name — see $out/$name.txt" >&2; exit 1; }; }
capture host 'hostname; date -u +%FT%TZ; timedatectl show -p Timezone'
capture manager-sha 'sha256sum /usr/local/sbin/btrfs-snapshot-manager; stat -c "%U:%G %a %n" /usr/local/sbin/btrfs-snapshot-manager'
capture manager-help 'sudo -n btrfs-snapshot-manager --help'
capture unit-definitions 'systemctl cat btrfs-snapshot-create.service btrfs-snapshot-prune.service btrfs-snapshot-create.timer btrfs-snapshot-prune.timer'
capture timers 'systemctl is-enabled btrfs-snapshot-create.timer btrfs-snapshot-prune.timer; systemctl list-timers --all --no-pager | grep -E "btrfs-snapshot|snapper" || true'
capture native-status 'sudo -n btrfs-snapshot-manager status'
capture native-list 'sudo -n btrfs-snapshot-manager list'
capture legacy-plan 'sudo -n btrfs-snapshot-manager legacy-plan --legacy-map root=root --legacy-map @data=@data'
capture native-prune-dry-run 'sudo -n btrfs-snapshot-manager prune --dry-run'
capture snapper-root 'sudo -n snapper --csvout --iso -c root list'
capture snapper-data 'sudo -n snapper --csvout --iso -c @data list'
capture manager-journal 'sudo -n journalctl -u btrfs-snapshot-create.service -u btrfs-snapshot-prune.service --since "12 hours ago" --no-pager -n 80'
(cd "$out" && sha256sum -- *.txt > SHA256SUMS.txt)
echo "PASS Step 9 $phase capture -> $out"
