#!/usr/bin/env bash
# Windows 11 Cygwin Bash; from Diaries parent repository root.
# Production: only SSH docker exec pg_dump (read-only). All writes: network-isolated local container.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-production-isolated-rehearsal"
PREFLIGHT="$FEATURE/tools/step3-production-preflight-readonly.sql"
HYBRID="$FEATURE/tools/step2-hybrid-schema-and-data.sql"
HYBRID_BACK="$FEATURE/tools/step2-hybrid-schema-rollback.sql"
MARQUEE="$FEATURE/tools/step3-retire-marquee-page-id.sql"
MARQUEE_BACK="$FEATURE/tools/step3-restore-marquee-page-id.sql"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u +%Y%m%d-%H%M%S)
CID="diaries-0029-prod-rehearsal-${STAMP}-$$"
LOG="$EVIDENCE/production-rehearsal-${STAMP}-$$.log"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  echo '0029 STEP 3 — PRODUCTION DATABASE ISOLATED MIGRATION / ROLLBACK / REAPPLY'
  echo "UTC: $(date -u '+%Y-%m-%dT%H:%M:%SZ')"
  test -f .gitmodules || { echo 'FAIL: execute from the Windows Diaries parent repository root'; exit 1; }
  for sqlfile in "$PREFLIGHT" "$HYBRID" "$HYBRID_BACK" "$MARQUEE" "$MARQUEE_BACK"; do
    test -f "$sqlfile" || { echo "FAIL: missing SQL $sqlfile"; exit 1; }
  done
  for cmd in docker ssh git sha256sum; do command -v "$cmd" >/dev/null || { echo "FAIL: missing $cmd"; exit 1; }; done
  echo 'Repository provenance (uncommitted changes preserved):'
  git rev-parse HEAD
  git submodule status
  echo 'SQL input checksums:'
  sha256sum "$PREFLIGHT" "$HYBRID" "$HYBRID_BACK" "$MARQUEE" "$MARQUEE_BACK"
  docker info >/dev/null
  test -z "$(docker ps -aq --filter "name=^/${CID}$")" || { echo 'FAIL: isolated container name collision'; exit 1; }
  # Create the isolated destination before contacting the production source.
  cleanup() { docker rm -f "$CID" >/dev/null 2>&1 || true; }
  trap cleanup EXIT
  docker run -d --network none --name "$CID" \
    -e POSTGRES_USER=diaries -e POSTGRES_PASSWORD=isolated-only \
    -e POSTGRES_DB=diaries postgres:18-alpine >/dev/null
  ready=0
  for i in $(seq 1 60); do
    if docker exec "$CID" pg_isready -U diaries -d diaries >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  test "$ready" -eq 1 || { echo 'FAIL: isolated PostgreSQL did not become ready'; exit 1; }
  echo 'SOURCE: pluto/diaries-postgres; SSH executes ONLY pg_dump; no files/services modified on pluto.'
  echo 'RESTORE: stream production custom-format dump into local PostgreSQL with --network none.'
  # Producer and consumer both fail the pipeline on error (pipefail); no dump stored outside feature.
  ssh -o BatchMode=yes pluto \
    'docker exec diaries-postgres sh -c '\''exec pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Fc --no-owner --no-acl'\''' | \
    docker exec -i "$CID" pg_restore -U diaries -d diaries --no-owner --no-acl --exit-on-error
  echo 'RESTORE: PASS'
  sql() { docker exec -i "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries "$@"; }
  scalar() { sql -Atc "$1" | tr -d '\r'; }
  check_col() {
    local tab="$1" col="$2" expect="$3" actual
    actual=$(scalar "SELECT count(*) FROM information_schema.columns WHERE table_schema='public' AND table_name='${tab}' AND column_name='${col}'")
    test "$actual" = "$expect" || { echo "FAIL: ${tab}.${col} column expected=${expect} actual=${actual}"; return 1; }
  }
  count=$(scalar 'SELECT count(*) FROM public.fragment')
  marquee_count=$(scalar 'SELECT count(*) FROM public.marquee')
  echo "BASELINE: fragments=${count} marquees=${marquee_count}"
  echo 'PRE-MIGRATION GATE: the approved, production-specific 11-row baseline.'
  baseline=$(sql -At -F '|' -f /dev/stdin < "$PREFLIGHT")
  printf '%s\n' "$baseline"
  grep -q '^GATE=PASS|' <<< "$baseline" || { echo 'FAIL: live production-shaped baseline does not match reviewed data'; exit 1; }
  check_col fragment placement 0
  check_col marquee page_id 1
  check_counts() {
    test "$(scalar 'SELECT count(*) FROM public.fragment')" = "$count" || { echo 'FAIL: Fragment row count changed'; return 1; }
    test "$(scalar 'SELECT count(*) FROM public.marquee')" = "$marquee_count" || { echo 'FAIL: Marquee row count changed'; return 1; }
  }
  check_hybrid() {
    check_col fragment placement 1
    check_col fragment diary_id 1
    test "$(scalar "SELECT count(*) FROM public.fragment WHERE placement='PREAMBLE'")" = 9 || { echo 'FAIL: expected 9 PREAMBLE Fragments'; return 1; }
    test "$(scalar "SELECT count(*) FROM public.fragment WHERE placement='DATED'")" = "$((count-9))" || { echo 'FAIL: DATED count mismatch'; return 1; }
    test "$(scalar "SELECT count(*) FROM public.fragment WHERE id IN (1738,2061) AND placement='DATED' AND page_id IS NOT NULL")" = 2 || { echo 'FAIL: dated exceptional Fragments not assigned'; return 1; }
    test "$(scalar "SELECT count(*) FROM public.fragment WHERE type NOT IN ('TEXT','IMAGE') OR placement IS NULL OR diary_id IS NULL")" = 0 || { echo 'FAIL: incomplete Fragment conversion'; return 1; }
    test "$(scalar "SELECT count(*) FROM public.marquee m LEFT JOIN public.fragment f ON f.id=m.fragment_id WHERE f.id IS NULL OR f.page_id IS NULL OR f.placement IS DISTINCT FROM 'DATED'")" = 0 || { echo 'FAIL: invalid Marquee owner'; return 1; }
    check_counts
  }
  check_marquee_mismatch() {
    test "$(scalar 'SELECT count(*) FROM public.marquee m JOIN public.fragment f ON f.id=m.fragment_id WHERE m.page_id IS DISTINCT FROM f.page_id')" = 0 || { echo 'FAIL: Marquee Page mismatches'; return 1; }
  }
  echo 'FORWARD 1: hybrid Fragment conversion (guarded SQL).'
  sql -f /dev/stdin < "$HYBRID"
  check_hybrid
  check_col marquee page_id 1
  check_marquee_mismatch
  echo 'FORWARD 1: PASS'
  echo 'FORWARD 2: retire redundant Marquee page_id.'
  sql -f /dev/stdin < "$MARQUEE"
  check_hybrid
  check_col marquee page_id 0
  echo 'FORWARD 2: PASS'
  echo 'ROLLBACK 2: reconstruct Marquee page_id from its owning Fragment.'
  sql -f /dev/stdin < "$MARQUEE_BACK"
  check_hybrid
  check_col marquee page_id 1
  check_marquee_mismatch
  echo 'ROLLBACK 2: PASS'
  echo 'ROLLBACK 1: restore pre-hybrid Fragment schema/data (no application edits occurred).'
  sql -f /dev/stdin < "$HYBRID_BACK"
  check_col fragment placement 0
  check_col fragment diary_id 0
  check_col marquee page_id 1
  check_counts
  check_marquee_mismatch
  rollback_gate=$(sql -At -F '|' -f /dev/stdin < "$PREFLIGHT")
  printf '%s\n' "$rollback_gate"
  grep -q '^GATE=PASS|' <<< "$rollback_gate" || { echo 'FAIL: rolled-back baseline differs from original production-shaped dataset'; exit 1; }
  echo 'ROLLBACK 1: PASS'
  echo 'REAPPLY: both forward SQL stages on restored baseline.'
  sql -f /dev/stdin < "$HYBRID"
  check_hybrid
  sql -f /dev/stdin < "$MARQUEE"
  check_hybrid
  check_col marquee page_id 0
  echo 'REAPPLY: PASS'
  echo 'SUMMARY: PASS — production copy restored, both migrations, both rollbacks, baseline recovery, reapplication.'
  echo 'PRODUCTION: read-only pg_dump only; pluto database, MQTT, containers and Files unchanged.'
  echo 'CLEANUP: isolated PostgreSQL container removed on exit.'
)
rc=$?
if test "$rc" -eq 0; then echo "PASS: evidence $LOG"; else echo "FAIL ($rc): evidence $LOG"; fi
exit "$rc"
