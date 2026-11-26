#!/usr/bin/env bash
# Windows 11 Cygwin, from Diaries parent repo root. READ ONLY: does NOT migrate.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-2-live-development-readiness"
BACKUP="$EVIDENCE/diaries-development-pre0029-20261125-201628.dump"
HASHFILE="$EVIDENCE/diaries-development-pre0029-20261125-201628.sha256"
PREP="$FEATURE/tools/step2-49-isolated-conversion.sql"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/live-development-transition-gate-$STAMP.log"
mkdir -p "$EVIDENCE" || exit 1
(
 set -euo pipefail
 exec > >(tee "$LOG") 2>&1
 echo '0029 LIVE DEVELOPMENT READ-ONLY TRANSITION GATE — NO MIGRATION'
 test -f .gitmodules || { echo 'FAIL: run from parent Diaries checkout'; exit 1; }
 test -s "$BACKUP" && test -s "$HASHFILE" || { echo 'FAIL: retained backup or receipt missing'; exit 1; }
 test -s "$PREP" && test -s "$HYBRID" || { echo 'FAIL: tested SQL absent'; exit 1; }
 sha256sum -c "$HASHFILE"
 echo 'Migration SQL hashes:'; sha256sum "$PREP" "$HYBRID"
 echo 'Parent Git revision and worktree:'; git rev-parse HEAD; git status --short --untracked-files=no
 echo 'Submodules:'; git submodule status
 for sub in diaries-client diaries-responder diaries-web; do
  echo "== $sub =="; git -C "$sub" rev-parse HEAD; git -C "$sub" status --short --untracked-files=no
 done
 test "$(docker inspect -f '{{.State.Running}}' diaries-development-db)" = true || { echo 'FAIL: dev DB not running'; exit 1; }
 docker exec diaries-development-db sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: wrong DB'; exit 1; }
 docker exec diaries-development-db psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "BEGIN READ ONLY; SELECT current_database(),current_user,current_setting('server_version'); SELECT count(*) AS pageless, count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061)) AS reviewed_11 FROM fragment WHERE page_id IS NULL; SELECT count(*) AS images FROM fragment WHERE type='IMAGE'; SELECT to_regclass('public.migration0029_rehearsal_receipt') AS rehearsal_receipt; COMMIT;"
 state=$(docker exec diaries-development-db psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*)::text||':'||count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061))::text||':'||(SELECT count(*) FROM fragment WHERE type='IMAGE')::text FROM fragment WHERE page_id IS NULL")
 test "$state" = '60:11:3' || { echo "FAIL: source baseline drift: $state"; exit 1; }
 receipt=$(docker exec diaries-development-db psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT coalesce(to_regclass('public.migration0029_rehearsal_receipt')::text, '')")
 test -z "$receipt" || { echo "FAIL: unexpected migration receipt: $receipt"; exit 1; }
 echo 'Development Docker services (IDE-run responder NOT covered):'
 docker ps --format 'name={{.Names}} image={{.Image}} status={{.Status}}' | grep -Ei 'diaries|mqtt|mosquitto' || true
 echo 'PASS: read-only integrity and development baseline gate.'
 echo 'BLOCKED: editorial placement/caption approval outstanding.'
 echo 'BLOCKED: responder shutdown and MQTT reconciliation not verified.'
 echo 'BLOCKED: tested conversion SQL marked isolated rehearsal only.'
 echo 'NO DATABASE OR MQTT WRITES.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: $LOG"; else echo "FAIL ($RC): $LOG"; fi
exit "$RC"
