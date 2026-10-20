#!/usr/bin/env bash
# 0037 Step 1: run *locally on mars* or on backup with read-only privileges.
# Capture output in feature evidence, not the production Playbooks source tree.
set -euo pipefail
printf 'Host: '; hostname -f
printf 'UTC: '; date -u --iso-8601=seconds
printf '\n--- filesystems ---\n'; findmnt -t btrfs -o TARGET,SOURCE,FSTYPE,OPTIONS || true
printf '\n--- btrfs filesystem show ---\n'; sudo btrfs filesystem show || true
printf '\n--- Snapper configs ---\n'; sudo snapper list-configs || true
for cfg in $(sudo snapper list-configs --columns config --csv 2>/dev/null | tail -n +2 | tr -d '"'); do
  [[ "$cfg" =~ ^[A-Za-z0-9_-]+$ ]] || continue
  printf '\n--- Snapper %s list ---\n' "$cfg"
  sudo snapper -c "$cfg" list --columns number,type,date,description || true
done
printf '\n--- units ---\n'
systemctl list-timers --all 'btrfs-snapshot-*' 'snapper-*' --no-pager || true
systemctl list-unit-files 'btrfs-snapshot-*' 'snapper-*' --no-pager || true
printf '\n--- snapshots manager status ---\n'
if command -v btrfs-snapshot-manager >/dev/null; then
  sudo btrfs-snapshot-manager list || true
  sudo btrfs-snapshot-manager prune --dry-run || true
fi
printf '\n--- protected state (metadata only) ---\n'
for f in /etc/btrfs-snapshot-manager.json; do
  if [[ -f "$f" ]]; then sudo stat -c '%n mode=%a owner=%U:%G size=%s' "$f"; fi
done
# Do not print protection/hold file bodies: they may contain identifiers.
