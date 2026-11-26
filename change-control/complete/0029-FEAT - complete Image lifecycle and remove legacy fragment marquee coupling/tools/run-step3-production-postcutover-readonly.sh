#!/usr/bin/env bash
# Windows Cygwin, from the Diaries parent repository root. Read-only on production.
(
  set -euo pipefail
  feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
  sql="$feature/tools/step3-production-postcutover-readonly.sql"
  evidence="$feature/evidence/step-3-production-cutover"
  test -f "$sql" || { echo "FAIL: missing $sql" >&2; exit 1; }
  mkdir -p "$evidence"
  logfile="$evidence/postcutover-integrity-$(date -u +%Y%m%d-%H%M%S).log"
  exec > >(tee "$logfile") 2>&1
  echo "=== 0029 post-cutover integrity UTC $(date -u --iso-8601=seconds) ==="
  echo "Evidence: $logfile"
  echo '=== Installed Diaries application versions, health, systemd ==='
  ssh pluto '(
    set -e
    echo "systemd=$(systemctl is-active diaries-compose.service)"
    docker inspect diaries-client diaries-responder diaries-web diaries-mosquitto diaries-postgres \
      --format "{{.Name}} image={{.Config.Image}} state={{.State.Status}} health={{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}"
    echo "=== Annual topic ACL grants ==="
    grep -n "diaries/years/#" /home/richard/projects/diaries/config/mosquitto/aclfile.txt
  )'
  echo '=== Read-only production SQL checks ==='
  ssh pluto 'docker exec -i diaries-postgres sh -c '\''exec psql -X -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'\''' < "$sql"
  echo '=== Recent application/broker error summaries (review any matches) ==='
  ssh pluto 'for c in diaries-responder diaries-web diaries-mosquitto; do
    echo "--- $c ---"
    docker logs "$c" --since 10m 2>&1 | grep -Ei "ERROR|Exception|FATAL|not authorised|denied" | tail -30 || true
  done'
  echo 'PASS: structural integrity and collection completed; review error summaries and browser evidence separately'
)
result=$?
if [ "$result" -eq 0 ]; then echo 'PASS: post-cutover read-only integrity'; else echo "FAIL: post-cutover read-only integrity (exit $result)"; fi
