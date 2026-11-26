#!/usr/bin/env bash
# 0029-FEAT LIVE DEVELOPMENT CUTOVER. Default is planning/verification ONLY.
# Windows Cygwin Bash, execute from parent Diaries repo root.
# This script NEVER touches production. Execution requires explicit approval
# and verified manual IDE responder shutdown. Do not run --execute until approved.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-2-live-development-cutover"
BACKUP_BASE="$FEATURE/evidence/step-2-live-development-readiness/diaries-development-pre0029-20261125-201628"
PREP="$FEATURE/tools/step2-49-live-development-conversion.sql"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
SOURCE='diaries-development-db'
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/cutover-${STAMP}.log"
MODE="${1:---plan}"
(
 set -euo pipefail
 exec > >(tee "$LOG") 2>&1
 echo "0029 live development cutover mode=$MODE; target fixed: $SOURCE"
 test -f .gitmodules && test -s "$PREP" && test -s "$HYBRID" || { echo 'FAIL: parent repository or migration files missing'; exit 1; }
 test -s "$BACKUP_BASE.dump" && test -s "$BACKUP_BASE.sha256" || { echo 'FAIL: retained restore-tested backup missing'; exit 1; }
 sha256sum -c "$BACKUP_BASE.sha256"
 echo 'Validating precise SQL binaries from successful isolated rehearsal:'
 echo 'c01bcd5450287eec00c9eccf1657ebc676847814e1307dfa6ccc8f1a5c22cb39' " $PREP" | sha256sum -c --status || { echo 'FAIL: conversion SQL drift'; exit 1; }
 echo '563cb107ac8fa518610c2f3a9a4e6b65575cf4acfc89a889bfd2ec288e3080ef' " $HYBRID" | sha256sum -c --status || { echo 'FAIL: hybrid SQL drift'; exit 1; }
 echo 'SQL fingerprint PASS'
 # Ensure the live-development SQL differs from rehearsal SQL only by comments/blank lines.
 python3 - "$PREP" "$FEATURE/tools/step2-49-isolated-conversion.sql" <<'PYCOMPARE'
import sys
def statements(path):
    return '\n'.join(line.strip() for line in open(path, encoding='utf-8') if line.strip() and not line.lstrip().startswith('--'))
if statements(sys.argv[1]) != statements(sys.argv[2]):
    raise SystemExit('FAIL: live conversion differs in executable SQL from isolated rehearsal')
print('Executable SQL equivalence PASS')
PYCOMPARE
 echo 'Parent revision:'; git rev-parse HEAD
 echo 'Submodule revisions:'; git submodule status
 for sub in diaries-client diaries-responder diaries-web; do
   echo "Status $sub:"; git -C "$sub" status --short --untracked-files=no
 done
 test "$(docker inspect -f '{{.State.Running}}' "$SOURCE")" = true || { echo 'FAIL: expected database container not running'; exit 1; }
 docker exec "$SOURCE" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: wrong database identity'; exit 1; }
 echo 'Validating unchanged legacy baseline:'
 baseline=$(docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT count(*)::text||':'||count(*) FILTER (WHERE id IN (1,2,3,387,806,1177,1563,1564,1738,1926,2061))::text||':'||(SELECT count(*) FROM fragment WHERE type='IMAGE')::text FROM fragment WHERE page_id IS NULL")
 test "$baseline" = '60:11:3' || { echo "FAIL: baseline drift: $baseline"; exit 1; }
 receipt=$(docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT coalesce(to_regclass('public.migration0029_rehearsal_receipt')::text, '')")
 test -z "$receipt" || { echo "FAIL: previous migration receipt: $receipt"; exit 1; }
 echo 'Legacy DB baseline PASS (60:11:3)'
 echo 'Responder status: IDE process is not observable reliably from Docker. Manual shutdown attestation required.'
 if docker ps --format '{{.Names}}' | grep -Ei 'diaries.*responder'; then echo 'FAIL: responder Docker container running'; exit 1; fi
 if test "$MODE" = '--plan'; then
   echo 'PLAN PASS. NO DATABASE WRITES. Editorial approval and responder shutdown NOT confirmed.'
   echo 'Do not use --execute until the user explicitly accepts the mapping and cutover.'
   exit 0
 fi
 test "$MODE" = '--execute' || { echo 'FAIL: use --plan (default) or --execute'; exit 1; }
 test "${DIARIES_0029_APPROVED:-}" = 'YES_49_MAPPING_AND_CAPTIONS' || { echo 'BLOCKED: editorial approval not recorded'; exit 1; }
 test "${DIARIES_0029_RESPONDER_STOPPED:-}" = 'YES_IDE_AND_DOCKER_STOPPED' || { echo 'BLOCKED: IDE responder shutdown not attested'; exit 1; }
 echo 'Approval and responder shutdown attested by operator. Ensure all development editors/clients are inactive. New backup before any write.'
 BACKUP="$EVIDENCE/diaries-development-before-cutover-$STAMP.dump"
 # pg_dump is READ-ONLY to development DB. Custom archive is kept for recovery.
 docker exec "$SOURCE" sh -c 'exec pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$BACKUP"
 test -s "$BACKUP" || { echo 'FAIL: backup empty'; exit 1; }
 docker exec -i "$SOURCE" pg_restore --list < "$BACKUP" > "$BACKUP.toc"
 test -s "$BACKUP.toc" || { echo 'FAIL: backup TOC invalid'; exit 1; }
 sha256sum "$BACKUP" > "$BACKUP.sha256"
 echo "PRE-CUTOVER RECOVERY BACKUP: $BACKUP"
 sha256sum -c "$BACKUP.sha256"
 echo 'STOP GATE: no new development writes from IDE/clients must occur during these transactions.'
 echo 'RUN approved development conversion SQL (identical statements to isolated-tested version) against fixed DEVELOPMENT target'
 docker exec -i "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$PREP"
 echo 'RUN original unchanged hybrid SQL against fixed DEVELOPMENT target'
 docker exec -i "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$HYBRID"
 echo 'POSTFLIGHT: checking exact migrated state'
 post=$(docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "SELECT (SELECT count(*) FROM migration0029_rehearsal_receipt)::text||':'||(SELECT count(*) FROM migration0029_legacy_image_archive)::text||':'||(SELECT count(*) FROM fragment WHERE placement='PREAMBLE')::text||':'||(SELECT count(*) FROM fragment WHERE placement='DATED' AND type='IMAGE')::text||':'||(SELECT count(*) FROM fragment f LEFT JOIN page p ON p.id=f.page_id WHERE (f.placement='DATED' AND (p.id IS NULL OR p.diary_id<>f.diary_id)) OR (f.placement IN ('PREAMBLE','POSTAMBLE') AND f.page_id IS NOT NULL))::text")
 test "$post" = '49:49:9:51:0' || { echo "FAIL: migration postflight $post; KEEP RESPONDER STOPPED; restore retained backup per runbook"; exit 1; }
 echo "DATABASE POSTFLIGHT PASS: $post"
 echo 'CAUTION: now manually start ONLY the updated development responder, inspect MQTT startup reconciliation logs and verify editor/reader.'
 echo "PASS: database migration completed; MQTT and UI gates still OPEN. Log: $LOG"
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: $LOG"; else echo "FAIL ($RC): $LOG"; fi
exit "$RC"
