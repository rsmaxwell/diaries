#!/usr/bin/env bash
# 0029 Step 3: coordinated DEVELOPMENT database schema retirement.
# Windows 11 Cygwin Bash from Diaries parent repo root.
# Default mode --plan is read-only. --execute requires manual IDE shutdown attestation.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-live-development-marquee-retirement"
FORWARD="$FEATURE/tools/step3-retire-marquee-page-id.sql"
BACKWARD="$FEATURE/tools/step3-restore-marquee-page-id.sql"
SOURCE='diaries-development-db'
MODE="${1:---plan}"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
LOG="$EVIDENCE/development-retirement-${STAMP}-$$.log"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  echo "0029 STEP 3 — LIVE DEVELOPMENT MARQUEE RETIREMENT mode=$MODE"
  echo "UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  case "$MODE" in --plan|--execute) ;; *) echo 'FAIL: allowed modes --plan / --execute'; exit 1 ;; esac
  test -f .gitmodules && test -s "$FORWARD" && test -s "$BACKWARD" || { echo 'FAIL: run from Diaries root; missing SQL'; exit 1; }
  echo 'Git provenance:'
  git rev-parse HEAD
  git submodule status
  echo 'SQL SHA-256:'
  sha256sum "$FORWARD" "$BACKWARD"
  # These are the SQL binaries whose SHA values were recorded in the successful isolated rehearsal.
  actual_forward=$(sha256sum "$FORWARD" | awk '{print $1}')
  actual_backward=$(sha256sum "$BACKWARD" | awk '{print $1}')
  test "$actual_forward" = '758a41e5ecdddd895827865b35edd362edb4dd56d12a51f845fc515a9b735931' || { echo 'FAIL: forward SQL differs from rehearsed version'; exit 1; }
  test "$actual_backward" = 'b629dcfe85f6525f5c3a0a7b3c8308b7f88432e23e1b22d5833b7bf2feba244a' || { echo 'FAIL: rollback SQL differs from rehearsed version'; exit 1; }
  docker info >/dev/null
  test "$(docker inspect -f '{{.State.Running}}' "$SOURCE")" = true || { echo 'FAIL: development PostgreSQL not running'; exit 1; }
  docker exec "$SOURCE" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: development database identity mismatch'; exit 1; }
  if docker ps --format '{{.Names}}' | grep -Eq '^diaries-(responder|web|client)(-|$)'; then
    echo 'FAIL: Docker application container detected; stop development application writers first'; exit 1
  fi
  scalar() { docker exec "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc "$1" | tr -d '\r'; }
  echo 'Database read-only preflight:'
  test "$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id'")" = 1 || { echo 'FAIL: marquee.page_id already absent'; exit 1; }
  test "$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement'")" = 1 || { echo 'FAIL: Step 2 hybrid schema missing'; exit 1; }
  invalid=$(scalar "SELECT count(*) FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.page_id IS NULL OR f.placement IS DISTINCT FROM 'DATED'")
  mismatch=$(scalar 'SELECT count(*) FROM public.marquee m JOIN public.fragment f ON f.id=m.fragment_id WHERE m.page_id IS DISTINCT FROM f.page_id')
  rows=$(scalar 'SELECT count(*) FROM public.marquee')
  echo "Marquees=$rows invalidOwners=$invalid pageMismatches=$mismatch"
  test "$invalid" = 0 && test "$mismatch" = 0 || { echo 'FAIL: ownership mismatch; migration prohibited'; exit 1; }
  if test "$MODE" = --plan; then
    echo 'PLAN PASS — no database writes or backups performed.'
    echo 'For --execute: close development Editor/Reader sessions and STOP the IDE responder; retain the active development DB; set explicit shutdown attestation.'
    exit 0
  fi
  test "${DIARIES_0029_RESPONDER_STOPPED:-}" = 'YES_IDE_AND_DOCKER_STOPPED' || { echo 'BLOCKED: set DIARIES_0029_RESPONDER_STOPPED=YES_IDE_AND_DOCKER_STOPPED after stopping IDE responder'; exit 1; }
  test "${DIARIES_0029_STEP3_APPROVED:-}" = 'YES_DEVELOPMENT_MARQUEE_RETIREMENT' || { echo 'BLOCKED: explicit development cutover approval not recorded'; exit 1; }
  echo 'OPERATOR ATTESTATION: development IDE responder stopped, application writers inactive, development schema migration approved.'
  backup="$EVIDENCE/diaries-development-before-marquee-retirement-${STAMP}-$$.dump"
  echo "BACKUP (custom archive): $backup"
  docker exec "$SOURCE" sh -c 'exec pg_dump -Fc --no-owner --no-acl -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > "$backup"
  test -s "$backup" || { echo 'FAIL: backup missing or empty'; exit 1; }
  docker exec -i "$SOURCE" pg_restore --list < "$backup" > "$backup.toc"
  test -s "$backup.toc" || { echo 'FAIL: backup TOC invalid'; exit 1; }
  sha256sum "$backup" > "$backup.sha256"
  sha256sum -c "$backup.sha256"
  echo 'PASS: fresh development recovery dump preserved under feature evidence.'
  echo 'APPLY: guarded retirement SQL to development DB. DO NOT RESTART OLD RESPONDER.'
  docker exec -i "$SOURCE" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$FORWARD" || { echo 'FAIL: SQL execution; keep responder stopped and inspect DB state. Backup retained.'; exit 1; }
  test "$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id'")" = 0 || { echo 'FAIL: page_id still present; keep responder stopped'; exit 1; }
  after=$(scalar 'SELECT count(*) FROM public.marquee')
  bad=$(scalar "SELECT count(*) FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.page_id IS NULL OR f.placement IS DISTINCT FROM 'DATED'")
  test "$after" = "$rows" && test "$bad" = 0 || { echo "FAIL: postflight rows=$after invalidOwners=$bad; keep responder stopped"; exit 1; }
  echo "DATABASE PASS: marquee.page_id retired; $after Marquees retained; owner checks pass."
  echo 'NEXT: manually start UPDATED development responder (not old version), check startup MQTT synchronisation, Editor and Reader.'
  echo 'ROLLBACK: only after stopping responder again, run separate guarded rollback SQL; inspect schema then restart matching old responder as appropriate.'
  echo "RECOVERY BACKUP: $backup"
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: log $LOG"; else echo "FAIL ($RC): log $LOG"; fi
exit "$RC"
