#!/usr/bin/env bash
# 0028-FEAT: read-only production recovery and writer-channel discovery.
# Run from the Diaries parent root on Windows PC (Cygwin).
# Never stops services, changes backups, runs a restore or changes Git.
set -euo pipefail
umask 077
feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
if [[ ! -f "$feature/IMPLEMENTATION-STEPS.md" || ! -f "$feature/README.md" ]]; then
  echo 'FAIL: start this script from the Diaries parent repository root' >&2
  exit 2
fi
if ! command -v ssh >/dev/null || ! command -v python3 >/dev/null; then
  echo 'FAIL: ssh and python3 are required in Cygwin' >&2
  exit 2
fi
stamp=$(date -u +%Y%m%dT%H%M%SZ)
out="$feature/evidence/Step 3/private/${stamp}-recovery-writer-inventory"
mkdir -p "$out"
printf 'Read-only evidence: %s\n' "$out"
results="$out/PROBE-STATUS.tsv"
printf 'host\tprobe\texit_status\n' > "$results"
probe() {
  local host=$1 probe_name=$2 body=$3 code=0
  echo "=== ${host}: ${probe_name} (read-only) ==="
  if printf '%s\n' "$body" | ssh -o BatchMode=yes -o ConnectTimeout=15 -o RequestTTY=no "$host" 'bash -s' > "$out/${host}-${probe_name}.log" 2>&1; then
    echo "PASS: ${host} ${probe_name} collected"
  else
    code=$?
    echo "UNAVAILABLE: ${host} ${probe_name} (SSH/remote exit ${code}); see private log"
  fi
  printf '%s\t%s\t%s\n' "$host" "$probe_name" "$code" >> "$results"
}
read -r -d '' PLUTO <<'REMOTE' || true
# No secrets are printed; no writes or service changes.
printf '%s\n' '=== HOST AND TIME ==='
hostname; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf '%s\n' '=== DEPLOYED SERVICES: IMAGE, DIGEST, STATE, HEALTH, BOUND PORTS ==='
for name in diaries-db diaries-mqtt diaries-responder diaries-client diaries-web; do
  echo "SERVICE: $name"
  docker inspect --format 'NAME={{.Name}} IMAGE_TAG={{.Config.Image}} IMAGE_ID={{.Image}} STATUS={{.State.Status}} HEALTH={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}} PORTS={{json .HostConfig.PortBindings}}' "$name" || echo "UNAVAILABLE: $name"
done
printf '%s\n' '=== COMPOSE CONFIGURATION AND INSTALLED TOOL PRESENCE ==='
project="$HOME/projects/diaries"
if [[ -f "$project/compose.yaml" && -f "$project/.env" ]]; then
  echo 'PASS: production Compose and .env present (values intentionally NOT printed)'
  ( cd "$project" && docker compose --file compose.yaml --env-file .env config --services ) || echo 'UNAVAILABLE: Compose services'
else
  echo "UNAVAILABLE: production Compose under $project"
fi
for tool in backup-dataset.sh restore-dataset.sh; do
  if [[ -f "$project/scripts/$tool" ]]; then echo "PRESENT: $tool"; else echo "MISSING: $tool"; fi
done
printf '%s\n' '=== CURRENT PUBLISHED COMPLETE DATASET (metadata only) ==='
pub="$project/data/diaries-backup"
if [[ -f "$project/.env" ]]; then
  configured=$(grep -m 1 '^DIARIES_COMPLETE_BACKUP_PUBLISHED_ROOT=' "$project/.env" || true)
  if [[ -n "$configured" ]]; then pub="${configured#*=}"; fi
fi
if [[ -L "$pub" ]]; then
  echo 'PRESENT: published dataset symlink'; readlink "$pub" || true
elif [[ -e "$pub" ]]; then
  echo 'PRESENT: published dataset path (not symlink)'
else
  echo "UNAVAILABLE: published dataset path ($pub)"
fi
printf '%s\n' '=== PRODUCTION BACKUP TIMER STATE ==='
systemctl show diaries-complete-backup-publish.timer --no-pager --property=LoadState,ActiveState,UnitFileState,LastTriggerUSec,NextElapseUSecRealtime || true
systemctl show diaries-complete-backup-publish.service --no-pager --property=LoadState,ActiveState,Result,ExecMainStatus || true
printf '%s\n' '=== DATABASE CONNECTION SUMMARY, NO QUERIES/PASSWORDS ==='
if docker inspect diaries-db >/dev/null 2>&1; then
  docker exec diaries-db sh -c 'exec psql -X -q -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -At -c "SELECT state, count(*) FROM pg_stat_activity WHERE datname = current_database() GROUP BY state ORDER BY state NULLS LAST"' || echo 'UNAVAILABLE: DB connection-state query'
fi
printf '%s\n' '=== END PLUTO READ-ONLY PROBE ==='
REMOTE
read -r -d '' BACKUPS <<'REMOTE' || true
printf '%s\n' '=== HOST AND TIME ==='
hostname; date -u '+%Y-%m-%dT%H:%M:%SZ'
printf '%s\n' '=== DIARIES BACKUP STATUS ==='
if [[ -x /usr/local/sbin/diaries-backup-status ]]; then
  # Both hosts keep /etc/btrfs-snapshot-manager.json privileged. sudo -n is
  # read-only here; never weaken configuration permissions to make status work.
  sudo -n /usr/local/sbin/diaries-backup-status --json
  rc=$?
  echo "DIARIES_BACKUP_STATUS_EXIT=$rc"
else
  echo 'UNAVAILABLE: diaries-backup-status not installed'
  echo 'DIARIES_BACKUP_STATUS_EXIT=127'
fi
printf '%s\n' '=== BTRFS BACKUP STATUS COMMAND AVAILABILITY ==='
if command -v btrfs-backup-status >/dev/null 2>&1; then
 echo 'PRESENT: btrfs-backup-status (not invoked; no full scan)'
else
 echo 'UNAVAILABLE: btrfs-backup-status'
fi
printf '%s\n' '=== RELEVANT SYSTEMD TIMERS ==='
systemctl list-timers --all --no-pager --no-legend 2>/dev/null | grep -E 'diaries|btrfs|snapshot|prune|native' || echo 'No relevant timers detected or timer output unavailable'
printf '%s\n' '=== END BACKUP HOST READ-ONLY PROBE ==='
REMOTE
probe pluto runtime-and-backup-metadata "$PLUTO"
probe mars retained-backup-status "$BACKUPS"
probe backup retained-backup-status "$BACKUPS"
summary_tool="$feature/tools/step3_recovery_readiness_summary.py"
python3 "$summary_tool" "$results" "$out/READINESS-RESULT.json"
