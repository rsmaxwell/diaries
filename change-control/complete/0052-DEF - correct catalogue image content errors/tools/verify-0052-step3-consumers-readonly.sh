#!/usr/bin/env bash
# 0052-DEF Step 3: read-only fragment consumers and page-owned public Reader HTTP checks.
# Windows 11 Cygwin Bash: run this standalone script from the Diaries parent checkout.
# Only writes private evidence under the feature; never changes a database or MQTT topic.
(
  set -euo pipefail
  feature='change-control/in-progress/0052-DEF - correct catalogue image content errors'
  if [[ ! -f "$feature/IMPLEMENTATION-STEPS.md" ]]; then
    echo 'FAIL: run from the Windows Diaries parent checkout root' >&2
    exit 1
  fi
  for executable in docker ssh curl git; do
    command -v "$executable" >/dev/null || { echo "FAIL: missing $executable" >&2; exit 1; }
  done

  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-consumers"
  mkdir -p "$out"
  printf 'Evidence: %s\n' "$out"

  {
    echo "UTC: $stamp"
    echo 'Windows Diaries parent checkout:'
    git branch --show-current
    git rev-parse HEAD
    git status --short
    git submodule status
  } > "$out/git-identity.txt" 2>&1

  cat > "$out/consumers-readonly.sql" <<'SQL'
\set ON_ERROR_STOP on
BEGIN TRANSACTION READ ONLY;
SELECT 'image3_direct|' || coalesce(string_agg(f.id::text, ',' ORDER BY f.id), '(none)')
FROM public.fragment f WHERE f.image_id=3;
SELECT 'image18_direct|' || coalesce(string_agg(f.id::text, ',' ORDER BY f.id), '(none)')
FROM public.fragment f WHERE f.image_id=18;
SELECT 'legacy84_whitley|' || CASE WHEN EXISTS (
 SELECT 1 FROM public.fragment f
 WHERE f.id=84 AND f.type IS NULL AND f.year=1828 AND f.month=3 AND f.day=20
   AND lower(coalesce(f.text,'')) LIKE '%img2840-image-map-whitley-park%'
) THEN 'PASS' ELSE 'FAIL' END;
SELECT 'legacy598_hermitage|' || CASE WHEN EXISTS (
 SELECT 1 FROM public.fragment f
 WHERE f.id=598 AND f.type IS NULL AND f.year=1829 AND f.month=7 AND f.day=8
   AND lower(coalesce(f.text,'')) LIKE '%img2900-image-hermitage%'
) THEN 'PASS' ELSE 'FAIL' END;
SELECT 'protected606_st_isaac|' || CASE WHEN EXISTS (
 SELECT 1 FROM public.fragment f
 WHERE f.id=606 AND lower(coalesce(f.text,'')) LIKE '%img2903-image-st-isaac-church%'
) THEN 'PASS' ELSE 'FAIL' END;
SELECT 'production_2334_marquee2272|' || CASE WHEN EXISTS (
 SELECT 1 FROM public.fragment f JOIN public.marquee m ON m.fragment_id=f.id
 WHERE f.id=2334 AND f.type::text='IMAGE' AND f.image_id=3 AND f.page_id=692
   AND m.id=2272 AND m.page_id=692
) THEN 'PASS' ELSE 'NOT_PRESENT' END;
-- Metadata fingerprint: no private HTML or link bodies are output.
-- Compare with the previously accepted Step 1 private inventory if required.
SELECT 'fragment_fingerprint|' || concat_ws('|', f.id::text, f.version::text,
 coalesce(f.type::text,'NULL'), coalesce(f.image_id::text,'NULL'), coalesce(f.page_id::text,'NULL'),
 f.year::text, f.month::text, f.day::text, f.sequence::text,
 md5(coalesce(f.text,'')), md5(coalesce(f.image_link_url,'')),
 coalesce(m.id::text,'NULL'), coalesce(m.version::text,'NULL'),
 coalesce(m.x::text,'NULL'),coalesce(m.y::text,'NULL'),
 coalesce(m.width::text,'NULL'),coalesce(m.height::text,'NULL'))
FROM public.fragment f LEFT JOIN public.marquee m ON m.fragment_id=f.id
WHERE f.id IN (84, 598, 606, 2332, 2334, 2338)
ORDER BY f.id;
-- The public Reader requires page-owned fragments. Legacy Fragments 84 and 598
-- have NULL page_id and are deliberately excluded until 0028 migration.
-- Resolve a public Reader URL from the typed Whitley consumer instead.
SELECT 'reader_whitley_url|' || coalesce((
 SELECT '/diaries-web/diaries/' || p.diary_id::text || '/1828/03?fragment=2334'
 FROM public.fragment f JOIN public.page p ON p.id=f.page_id
 WHERE f.id=2334 AND f.type::text='IMAGE' AND f.image_id=3
 LIMIT 1
), 'NOT_AVAILABLE');
-- A July month route can only be tested if that month has page-owned fragments.
-- It is NOT a direct HTTP check of the legacy Hermitage Fragment 598.
SELECT 'reader_july_month_url|' || coalesce((
 SELECT '/diaries-web/diaries/' || p.diary_id::text || '/1829/07'
 FROM public.fragment f JOIN public.page p ON p.id=f.page_id
 WHERE f.year=1829 AND f.month=7 AND p.diary_id=(
   SELECT p2.diary_id FROM public.page p2 WHERE p2.id=692
 )
 ORDER BY f.id LIMIT 1
), 'NOT_AVAILABLE');
COMMIT;
SQL

  echo '=== Development fragment relationships (read-only) ==='
  docker exec -i diaries-development-db sh -c \
    'psql -X -A -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB" -f -' \
    < "$out/consumers-readonly.sql" > "$out/development-consumers.txt"

  echo '=== Production fragment relationships (read-only) ==='
  ssh pluto "docker exec -i diaries-postgres sh -c 'psql -X -A -t -v ON_ERROR_STOP=1 -U \"\$POSTGRES_USER\" -d \"\$POSTGRES_DB\" -f -'" \
    < "$out/consumers-readonly.sql" > "$out/production-consumers.txt"

  check_record() {
    local file=$1 expected=$2
    if grep -Fxq -- "$expected" "$file"; then
      printf 'PASS: %s — %s\n' "$(basename "$file")" "$expected"
    else
      printf 'FAIL: %s — expected %s\n' "$(basename "$file")" "$expected" >&2
      grep -E '^(image3_direct|image18_direct|legacy84_whitley|legacy598_hermitage|protected606_st_isaac|production_2334_marquee2272)\|' "$file" >&2 || true
      exit 1
    fi
  }
  for environment in development production; do
    file="$out/${environment}-consumers.txt"
    check_record "$file" 'image18_direct|(none)'
    check_record "$file" 'legacy84_whitley|PASS'
    check_record "$file" 'legacy598_hermitage|PASS'
    check_record "$file" 'protected606_st_isaac|PASS'
  done
  check_record "$out/development-consumers.txt" 'image3_direct|2338'
  check_record "$out/production-consumers.txt" 'image3_direct|2332,2334'
  check_record "$out/production-consumers.txt" 'production_2334_marquee2272|PASS'
  check_record "$out/development-consumers.txt" 'production_2334_marquee2272|NOT_PRESENT'

  echo '=== Production public Reader HTTP checks (not visual acceptance) ==='
  # The Reader projection excludes legacy Fragments 84 and 598 because they
  # lack page_id. Their SQL identity checks above are the correct verification.
  # Use a real page-owned consumer for the public Reader image check.
  whitley_path=$(sed -n 's/^reader_whitley_url|//p' "$out/production-consumers.txt")
  july_path=$(sed -n 's/^reader_july_month_url|//p' "$out/production-consumers.txt")
  [[ "$whitley_path" == /diaries-web/diaries/* ]] || {
    echo "FAIL: no page-owned Whitley Reader URL (got '$whitley_path')" >&2
    exit 1
  }

  check_reader_http() {
    local label=$1 path=$2 status
    local url="https://pluto.rsmaxwell.co.uk${path}"
    printf 'GET %s\n' "$url"
    status=$(curl --location --silent --show-error --max-time 40 \
      --dump-header "$out/${label}.headers" \
      --output "$out/${label}.html" \
      --write-out '%{http_code}' "$url") || {
      echo "FAIL: Reader HTTP request failed for $label" >&2
      return 1
    }
    [[ "$status" == 200 ]] || {
      echo "FAIL: Reader HTTP $status for $label" >&2
      return 1
    }
    printf 'PASS: production Reader HTTP 200 — %s\n' "$label"
  }

  check_reader_http 'reader-index' '/diaries-web'
  check_reader_http 'whitley-image3-fragment2334' "$whitley_path"
  july_status='NOT_APPLICABLE'
  if [[ "$july_path" == /diaries-web/diaries/* ]]; then
    check_reader_http 'july-1829-page-owned-month' "$july_path"
    july_status='HTTP_200_MONTH_ONLY'
  elif [[ "$july_path" == 'NOT_AVAILABLE' ]]; then
    echo 'NOT_APPLICABLE: July 1829 has no page-owned fragments in the selected diary; Reader cannot show legacy Fragment 598 before 0028 migration.'
  else
    echo "FAIL: unexpected July Reader path: $july_path" >&2
    exit 1
  fi

  cat > "$out/RESULT.txt" <<RESULT
PASS: 0052 production/development fragment-identity and direct-consumer checks.
PASS: production public Reader index and page-owned IMAGE Fragment 2334 HTTP 200.
July 1829 page-owned month HTTP check: $july_status.
Run UTC: $stamp
Reference expectations based on 2026-11-23 Step 1 inventory.
Legacy Fragments 84 and 598 have NULL page_id, so the public Reader projection
cannot resolve them directly before 0028 migration. A July month HTTP 200, if
available, is not a check that Hermitage Fragment 598 renders in the public Reader.
This script does NOT establish picture correctness or independently prove unchanged
transcription/ordering against pre-change evidence. Review fingerprint rows against
prior Step 1 private inventory if stronger criteria are required.
Public Reader visual acceptance (where applicable), protected-image visual checks,
and explicit owner closure approval remain MANUAL / NOT YET RECORDED here.
RESULT
  cat "$out/RESULT.txt"
) && echo 'PASS: Step 3 consumer and Reader HTTP checks completed' || {
  rc=$?
  echo 'FAIL: Step 3 consumer or Reader HTTP check incomplete; inspect private evidence' >&2
  exit "$rc"
}
