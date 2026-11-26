#!/usr/bin/env bash
# Windows 11 Cygwin Bash — invoke from Diaries parent repository.
# Reads the active DEVELOPMENT database through pg_dump only. Never alters it.
# All schema writes occur in a temporary, --network none PostgreSQL container.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
SOURCE='diaries-development-db'
FORWARD="$FEATURE/tools/step3-retire-marquee-page-id.sql"
BACKWARD="$FEATURE/tools/step3-restore-marquee-page-id.sql"
EVIDENCE="$FEATURE/evidence/step-3-isolated-marquee-page-retirement"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
CID="diaries-0029-step3-${STAMP}-$$"
LOG="$EVIDENCE/rehearsal-${STAMP}-$$.log"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  echo '0029 STEP 3 — ISOLATED MARQUEE PAGE RETIREMENT, ROLLBACK, REAPPLY'
  echo "UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  test -f .gitmodules && test -f "$FORWARD" && test -f "$BACKWARD" || { echo 'FAIL: invoke from Diaries root with Step 3 SQL files'; exit 1; }
  echo 'Repository provenance:'
  git rev-parse HEAD
  git submodule status
  sha256sum "$FORWARD" "$BACKWARD"
  docker info >/dev/null
  test "$(docker inspect -f '{{.State.Running}}' "$SOURCE")" = true || { echo 'FAIL: development database not running'; exit 1; }
  docker exec "$SOURCE" sh -c 'test "$POSTGRES_DB" = diaries && test "$POSTGRES_USER" = diaries' || { echo 'FAIL: unexpected development database identity'; exit 1; }
  echo 'PASS: source identity confirmed. Source is accessed only via pg_dump.'
  if docker ps -a --format '{{.Names}}' | grep -Fxq "$CID"; then echo 'FAIL: isolated container name already present'; exit 1; fi
  cleanup() { docker rm -f "$CID" >/dev/null 2>&1 || true; }
  trap cleanup EXIT
  docker run --rm -d --network none --name "$CID" \
    -e POSTGRES_USER=diaries -e POSTGRES_PASSWORD=isolated-only -e POSTGRES_DB=diaries \
    postgres:18-alpine >/dev/null
  ready=0
  for i in $(seq 1 60); do
    if docker exec "$CID" pg_isready -U diaries -d diaries >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  test "$ready" -eq 1 || { echo 'FAIL: isolated PostgreSQL failed readiness'; exit 1; }
  echo 'RESTORE: direct pg_dump stream from development; no source mutation, no dump stored outside feature.'
  docker exec "$SOURCE" sh -c 'exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl' | \
    docker exec -i "$CID" pg_restore -U diaries -d diaries --no-owner --no-acl --exit-on-error
  echo 'RESTORE: PASS'
  sql() { docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries "$@"; }
  scalar() { sql -Atc "$1" | tr -d '\r'; }
  check_column() {
    local expected="$1" actual
    actual=$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='marquee' AND column_name='page_id'")
    test "$actual" = "$expected" || { echo "FAIL: expected marquee.page_id count=$expected, found=$actual"; return 1; }
  }
  check_owners() {
    local invalid
    invalid=$(scalar "SELECT count(*) FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.page_id IS NULL OR f.placement IS DISTINCT FROM 'DATED'")
    test "$invalid" = 0 || { echo "FAIL: $invalid invalid Marquee Fragment owners"; return 1; }
  }
  check_mismatch() {
    local mismatch
    mismatch=$(scalar "SELECT count(*) FROM public.marquee m JOIN public.fragment f ON f.id=m.fragment_id WHERE m.page_id IS DISTINCT FROM f.page_id")
    test "$mismatch" = 0 || { echo "FAIL: $mismatch Marquee/Fragment Page mismatches"; return 1; }
  }
  echo 'PREFLIGHT: ensure this is a completed Step 2 hybrid schema with retirement still pending.'
  test "$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='fragment' AND column_name='placement'")" = 1 || { echo 'FAIL: hybrid Fragment placement missing'; exit 1; }
  check_column 1
  check_owners
  check_mismatch
  original=$(scalar 'SELECT count(*) FROM public.marquee')
  echo "Marquee row count: $original"
  echo 'FORWARD 1: guarded removal in isolated database.'
  sql -f /dev/stdin < "$FORWARD"
  check_column 0
  check_owners
  test "$(scalar 'SELECT count(*) FROM public.marquee')" = "$original"
  echo 'FORWARD 1: PASS'
  echo 'ROLLBACK: reconstruct column from Fragment Page in isolated database.'
  sql -f /dev/stdin < "$BACKWARD"
  check_column 1
  check_owners
  check_mismatch
  test "$(scalar 'SELECT count(*) FROM public.marquee')" = "$original"
  echo 'ROLLBACK: PASS'
  echo 'FORWARD 2: reproducibility after rollback.'
  sql -f /dev/stdin < "$FORWARD"
  check_column 0
  check_owners
  test "$(scalar 'SELECT count(*) FROM public.marquee')" = "$original"
  echo 'FORWARD 2: PASS'
  echo 'SUMMARY: PASS — restore, ownership, retirement, rollback, reapplication; source development DB unchanged.'
  echo 'The isolated PostgreSQL container is removed automatically.'
)
RC=$?
if test "$RC" -eq 0; then echo "PASS: evidence $LOG"; else echo "FAIL ($RC): evidence $LOG"; fi
exit "$RC"
