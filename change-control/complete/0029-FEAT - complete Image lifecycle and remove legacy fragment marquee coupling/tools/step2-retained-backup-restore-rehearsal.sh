#!/usr/bin/env bash
# Windows Cygwin Bash; run from Diaries parent repository.
# IMPORTANT: RESTORE AND MIGRATION RUN ONLY IN NEW NETWORK-ISOLATED CONTAINER.
# No live database writes; no responder or MQTT service changes.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
SOURCE='diaries-development-db'
EVIDENCE="$FEATURE/evidence/step-2-live-development-readiness"
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/retained-backup-restore-rehearsal-$STAMP.log"
BACKUP="$EVIDENCE/diaries-development-pre0029-20261125-201628.dump"
HASHFILE="$EVIDENCE/diaries-development-pre0029-20261125-201628.sha256"
PREP="$FEATURE/tools/step2-49-isolated-conversion.sql"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
CID="diaries-0029-retained-restore-$STAMP"
mkdir -p "$EVIDENCE" || exit 1
(
 set -euo pipefail
 exec > >(tee "$LOG") 2>&1
 echo '0029 RETAINED BACKUP RESTORE + TRANSITION READINESS (ISOLATED ONLY)'
 test -f .gitmodules || { echo 'FAIL: run from Diaries parent repository'; exit 1; }
 test -s "$BACKUP" && test -s "$HASHFILE" || { echo 'FAIL: retained backup or SHA-256 receipt missing'; exit 1; }
 test -s "$PREP" && test -s "$HYBRID" || { echo 'FAIL: tested conversion/hybrid SQL missing'; exit 1; }
 echo 'VERIFY: retained dump SHA-256 against original receipt'
 sha256sum -c "$HASHFILE"
 echo 'SOURCE: development DB container identity and read-only baseline'
 test "$(docker inspect -f '{{.State.Running}}' "$SOURCE")" = true || { echo 'FAIL: development DB not running'; exit 1; }
 docker exec "$SOURCE" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: wrong source DB'; exit 1; }
 docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "select 'db='||current_database()||';user='||current_user||';version='||current_setting('server_version')"
 docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "SELECT count(*) AS pageless_total, count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061)) AS reviewed_11 FROM fragment WHERE page_id IS NULL; SELECT count(*) AS original_image_fragments FROM fragment WHERE type='IMAGE';"
 echo 'SERVICE INVENTORY (read only): identify responder and MQTT before planned quiescence'
 docker ps --format 'name={{.Names}} image={{.Image}} status={{.Status}} ports={{.Ports}}' | grep -Ei 'diaries|mqtt|mosquitto|NAME' || true
 echo 'NOTE: inventory is NOT evidence of stopped responder, MQTT consistency or retained-topic resynchronization.'
 if docker ps -a --format '{{.Names}}' | grep -Fxq "$CID"; then echo 'FAIL: isolated container name already in use'; exit 1; fi
 cleanup() { docker rm -f "$CID" >/dev/null 2>&1 || true; }
 trap cleanup EXIT
 echo "START: ephemeral isolated PostgreSQL $CID (network none, no ports, no mounts)"
 docker run --rm -d --network none --name "$CID" -e POSTGRES_USER=diaries -e POSTGRES_PASSWORD=isolated-only -e POSTGRES_DB=diaries postgres:18-alpine >/dev/null
 ready=0
 for i in $(seq 1 60); do
   if docker exec "$CID" pg_isready -U diaries -d diaries >/dev/null 2>&1; then ready=1; break; fi
   sleep 1
 done
 test "$ready" -eq 1 || { echo 'FAIL: isolated container readiness timeout'; exit 1; }
 echo 'RESTORE: from RETAINED custom-format dump (not a new live pg_dump)'
 docker exec -i "$CID" pg_restore -U diaries -d diaries --no-owner --no-acl --exit-on-error < "$BACKUP"
 echo 'RESTORE_PASS'
 echo 'VERIFY: restored pre-migration baseline exactly matches observed development counts'
 docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "SELECT count(*) AS restored_pageless, count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061)) AS reviewed_11 FROM fragment WHERE page_id IS NULL; SELECT count(*) AS restored_image_fragments FROM fragment WHERE type='IMAGE';"
 baseline="$(docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*)::text||':'||count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061))::text FROM fragment WHERE page_id IS NULL")"
 test "$baseline" = '60:11' || { echo "FAIL: unexpected restored page-less baseline $baseline"; exit 1; }
 original_images="$(docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*) FROM fragment WHERE type='IMAGE'")"
 test "$original_images" = '3' || { echo "FAIL: unexpected restored IMAGE count $original_images"; exit 1; }
 echo 'RUN: existing 49-source guarded conversion (isolated DB only)'
 docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$PREP"
 echo 'RUN: unchanged production-shaped 0029 hybrid schema (isolated DB only)'
 docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$HYBRID"
 echo 'VERIFY: isolated receipts, archives, model, ownership and corrected-image cases'
 docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "SELECT (SELECT count(*) FROM migration0029_rehearsal_receipt) receipts, (SELECT count(*) FROM migration0029_legacy_image_archive) archives, (SELECT count(*) FROM fragment WHERE placement='PREAMBLE') preambles, (SELECT count(*) FROM fragment WHERE placement='DATED' AND type='IMAGE') dated_images; SELECT id, placement, type, page_id, diary_id, image_id FROM fragment WHERE id IN (598,606,611,612,613,1738,2061) ORDER BY id;"
 outcome="$(docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT (SELECT count(*) FROM migration0029_rehearsal_receipt)::text||':'||(SELECT count(*) FROM migration0029_legacy_image_archive)::text||':'||(SELECT count(*) FROM fragment WHERE placement='PREAMBLE')::text||':'||(SELECT count(*) FROM fragment WHERE placement='DATED' AND type='IMAGE')::text")"
 test "$outcome" = '49:49:9:51' || { echo "FAIL: post-migration counts $outcome"; exit 1; }
 invalid="$(docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*) FROM fragment f LEFT JOIN page p ON p.id=f.page_id WHERE (f.placement='DATED' AND (p.id IS NULL OR p.diary_id<>f.diary_id)) OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND f.page_id IS NOT NULL)")"
 test "$invalid" = '0' || { echo "FAIL: invalid ownership count $invalid"; exit 1; }
 echo 'VERIFY: live development source remained on legacy baseline (read only)'
 live="$(docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*)::text||':'||(SELECT count(*) FROM fragment WHERE type='IMAGE')::text FROM fragment WHERE page_id IS NULL")"
 test "$live" = '60:3' || { echo "FAIL: live source baseline changed during check: $live"; exit 1; }
 echo 'PASS: retained backup restorable; isolated conversion/hybrid replay and ownership checks passed.'
 echo 'PENDING: editorial approvals for all 49 mappings/captions; coordinated responder shutdown/startup; retained MQTT topic-tree verification; live migration authorization.'
 echo 'NO LIVE MIGRATION PERFORMED. Temporary isolated container removed by cleanup trap.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: $LOG"; else echo "FAIL ($RC): $LOG"; fi
exit "$RC"
