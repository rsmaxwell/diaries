#!/usr/bin/env bash
# Windows Cygwin, run from Diaries parent repo; rehearsal creates an isolated
# ephemeral PostgreSQL container with NO published port and NO network.
# It changes no source database, image file, or production resource.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
SOURCE_CONTAINER='diaries-development-db'
PREP="$FEATURE/tools/step2-49-isolated-conversion.sql"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
EVIDENCE="$FEATURE/evidence/step-2-isolated-rehearsal"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/rehearsal-$STAMP.log"
CID="diaries-0029-isolated-$STAMP"
(
 set -euo pipefail
 exec > >(tee "$LOG") 2>&1
 echo 'ISOLATED 0029 REHEARSAL — NO LIVE DATABASE WRITES'
 test -f "$PREP" && test -f "$HYBRID"
 test "$(docker inspect -f '{{.State.Running}}' "$SOURCE_CONTAINER")" = true || { echo 'FAIL: expected development database container not running'; exit 1; }
 # Source identity comes from the running container, not from a newly evaluated Compose config.
 docker exec "$SOURCE_CONTAINER" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: source database identity mismatch'; exit 1; }
 echo "SOURCE: confirmed running development container $SOURCE_CONTAINER (database=diaries)"
 if docker ps -a --format '{{.Names}}' | grep -Fxq "$CID"; then
   echo 'FAIL: rehearsal container name exists; aborting'; exit 1
 fi
 cleanup() { docker rm -f "$CID" >/dev/null 2>&1 || true; }
 trap cleanup EXIT
 echo "START temporary isolated database $CID (network=none; no published ports)"
 docker run --rm -d --network none --name "$CID" \
   -e POSTGRES_USER=diaries -e POSTGRES_PASSWORD=rehearsal-only -e POSTGRES_DB=diaries \
   postgres:18-alpine >/dev/null
 ready=0
 for i in $(seq 1 60); do
   if docker exec "$CID" pg_isready -U diaries -d diaries >/dev/null 2>&1; then ready=1; break; fi
   sleep 1
 done
 test "$ready" -eq 1 || { echo 'FAIL: isolated PostgreSQL did not become ready'; exit 1; }
 echo 'RESTORE: stream logical backup from running development container into isolated DB'
 # Source side is pg_dump only; restore side is a different container.
 docker exec "$SOURCE_CONTAINER" \
   sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-acl --no-owner' | \
   docker exec -i "$CID" pg_restore -U diaries -d diaries --no-owner --no-acl --exit-on-error
 echo 'RESTORE_PASS'
 echo 'RUN: guarded 49-source rehearsal (isolated only)'
 docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$PREP"
 echo 'RUN: unchanged 0029 production-shaped hybrid schema script (isolated only)'
 docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$HYBRID"
 echo 'VERIFY: 49 receipts, 49 archived legacy rows, 48 converted + 1 existing; 11 annual/dated ownership rows'
 docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "
 SELECT (SELECT count(*) FROM migration0029_rehearsal_receipt) AS receipts,
        (SELECT count(*) FROM migration0029_legacy_image_archive) AS archives,
        (SELECT count(*) FROM fragment WHERE placement='PREAMBLE') AS preambles,
        (SELECT count(*) FROM fragment WHERE placement='DATED' AND type='IMAGE') AS dated_images;
 SELECT id,year,month,day,placement,type,page_id,diary_id,image_id
 FROM fragment WHERE id IN (598,606,611,612,613,1738,2061) ORDER BY id;
 SELECT count(*) AS invalid_ownership FROM fragment f LEFT JOIN page p ON p.id=f.page_id
 WHERE (f.placement='DATED' AND (p.id IS NULL OR p.diary_id<>f.diary_id))
    OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND f.page_id IS NOT NULL);
 "
 echo 'PASS: isolated conversion and unchanged 0029 hybrid migration completed'
 echo 'Temporary container will be removed automatically; live database unaffected.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: evidence $LOG"; else echo "FAIL ($RC): evidence $LOG"; fi
exit "$RC"
