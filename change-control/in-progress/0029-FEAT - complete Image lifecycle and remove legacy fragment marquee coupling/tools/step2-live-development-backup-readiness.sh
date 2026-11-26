#!/usr/bin/env bash
# Windows 11 Cygwin Bash; invoke from the Diaries parent repository.
# Read-only against the running DEVELOPMENT database. Writes backup/evidence to the feature folder only.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
SOURCE='diaries-development-db'
EVIDENCE="$FEATURE/evidence/step-2-live-development-readiness"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/readiness-$STAMP.log"
DUMP="$EVIDENCE/diaries-development-pre0029-$STAMP.dump"
RECEIPT="$EVIDENCE/readiness-$STAMP.receipt.txt"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  echo '0029 LIVE-DEVELOPMENT READINESS — BACKUP AND READ-ONLY VALIDATION; NO MIGRATION'
  test -f .gitmodules || { echo 'FAIL: not in Diaries parent repository'; exit 1; }
  echo 'Parent Git:'
  git status --short --branch || true
  git rev-parse HEAD || true
  echo 'Submodule Git:'
  git submodule status || true
  echo 'Expected source container:' "$SOURCE"
  test "$(docker inspect -f '{{.State.Running}}' "$SOURCE")" = true || { echo 'FAIL: expected development DB container not running'; exit 1; }
  docker exec "$SOURCE" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: development database identity mismatch'; exit 1; }
  docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "select 'db='||current_database()||';user='||current_user||';postgres='||current_setting('server_version')"
  echo 'Pre-migration baseline (read only):'
  docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -c "SELECT count(*) AS pageless_total, count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061)) AS reviewed_11 FROM fragment WHERE page_id IS NULL; SELECT count(*) AS image_fragments FROM fragment WHERE type='IMAGE'; SELECT to_regclass('public.migration0029_rehearsal_receipt') AS unexpected_rehearsal_receipt;"
  echo 'Capturing pg_dump custom-format logical backup into feature evidence.'
  # pg_dump reads the running DB only. No Compose dependency or database mutation.
  docker exec "$SOURCE" sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' > "$DUMP"
  test -s "$DUMP" || { echo 'FAIL: pg_dump empty'; exit 1; }
  echo 'Verifying that the generated archive has a valid pg_restore table of contents.'
  docker exec -i "$SOURCE" pg_restore --list < "$DUMP" > "$EVIDENCE/diaries-development-pre0029-$STAMP.toc"
  test -s "$EVIDENCE/diaries-development-pre0029-$STAMP.toc"
  if command -v sha256sum >/dev/null 2>&1; then sha256sum "$DUMP" > "$EVIDENCE/diaries-development-pre0029-$STAMP.sha256"; else echo 'FAIL: sha256sum missing'; exit 1; fi
  {
    echo 'Development database backup readiness receipt — NOT migration approval'
    date -u '+Captured UTC: %Y-%m-%dT%H:%M:%SZ'
    echo "Database container: $SOURCE"
    echo "Dump: $DUMP"
    echo "Archive bytes: $(wc -c < "$DUMP")"
    cat "$EVIDENCE/diaries-development-pre0029-$STAMP.sha256"
    echo 'Archive TOC: verified with pg_restore --list'
    echo 'Restore test: NOT performed by this command (earlier isolated rehearsal restored a separate dump).'
    echo 'Live responder and MQTT quiescence: NOT verified.'
    echo 'Editorial placement approvals: PENDING.'
    echo 'Live development migration: NOT EXECUTED.'
  } > "$RECEIPT"
  cat "$RECEIPT"
  echo 'PASS: development backup captured; archive format validated; migration NOT executed.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: readiness log $LOG"; else echo "FAIL ($RC): readiness log $LOG"; fi
exit "$RC"
