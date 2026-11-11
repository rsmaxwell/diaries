#!/usr/bin/env bash
# 0045-FEAT read-only caller audit. Run on mango (Diaries checkout synced there).
# Review findings before retiring old operator entry points; no host changes.
set -euo pipefail
cd /home/richard/playbooks
printf '=== Git baseline ===\n'
git branch --show-current
git rev-parse HEAD
git status --short
printf '=== Tracked source callers (exclude historical verification/docs) ===\n'
git grep -n -E \
  'local-backup\.yaml|remote-backup\.yaml|scripts/(local-backup|remote-backup)\.sh' \
  -- ':!verification/**' ':!roles/*/tests/**' ':!0045-OPERATOR-RETIREMENTS.txt' || true
printf '=== Local cron and systemd references on mango ===\n'
for root in /etc/cron.d /etc/cron.daily /etc/cron.hourly /etc/cron.weekly /etc/systemd/system; do
  if test -d "$root"; then
    sudo grep -REIn --exclude='*.wants' \
      'local-backup\.yaml|remote-backup\.yaml|local-backup\.sh|remote-backup\.sh' "$root" || true
  fi
done
printf '=== Jenkins job/script references (when accessible) ===\n'
for root in /var/lib/jenkins/jobs /srv/jenkins/jobs; do
  if test -d "$root"; then
    sudo grep -REIn \
      'local-backup\.yaml|remote-backup\.yaml|local-backup\.sh|remote-backup\.sh' "$root" || true
  fi
done
printf 'NOTE: Jobs stored on other hosts, externally managed schedules and user crontabs may also need operator inspection.\n'
