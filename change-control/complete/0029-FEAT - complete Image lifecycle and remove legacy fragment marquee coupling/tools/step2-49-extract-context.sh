#!/usr/bin/env bash
# Windows Cygwin, execute from Diaries parent checkout. Read-only, noninteractive process.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
evidence="$feature/evidence/step-2-development-preflight"
compose='compose.development-infrastructure.yaml'
env1='config/environments/development-infrastructure.env'
env2='config/environments/local.env'
for f in "$compose" "$env1" "$env2" "$feature/tools/step2-49-source-context.sql" "$feature/tools/step2-49-page-context.sql"; do
  [[ -f "$f" ]] || { echo "FAIL: missing $f" >&2; exit 2; }
done
mkdir -p "$evidence"
stamp=$(date -u +%Y%m%d-%H%M%S)
opts=(-f "$compose" --env-file "$env1" --env-file "$env2")
docker compose "${opts[@]}" config --quiet
for section in source page; do
  file="$feature/tools/step2-49-${section}-context.sql"
  out="$evidence/0029-49-${section}-context-$stamp.csv"
  errors="$evidence/0029-49-${section}-context-$stamp.stderr.txt"
  echo "Collecting read-only $section context: $out"
  if ! docker compose "${opts[@]}" exec -T diaries-db sh -c     'exec psql -X -q -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'     < "$file" > "$out" 2> "$errors"; then
      echo "FAIL: $section extraction failed; diagnostics:" >&2
      cat "$errors" >&2
      exit 1
  fi
done
python - "$evidence/0029-49-source-context-$stamp.csv" "$evidence/0029-49-page-context-$stamp.csv" <<'PYCSV'
import csv,sys,collections
src=list(csv.DictReader(open(sys.argv[1],encoding='utf-8-sig',newline='')))
pages=list(csv.DictReader(open(sys.argv[2],encoding='utf-8-sig',newline='')))
if len(src)!=49 or len(set(x['source_fragment_id'] for x in src))!=49:
    sys.exit(f'FAIL: expected 49 source records, found {len(src)}')
drift=[r['source_fragment_id'] for r in src if r['source_unchanged']!='t']
print(f'Source records: {len(src)}, manifest drift: {len(drift)}')
if drift: print('DRIFT IDs:',','.join(drift))
print(f'Page candidate rows: {len(pages)}; sources with multiple candidates: {sum(1 for r in src if ";" in r["candidate_page_ids"])}')
missing=[r['source_fragment_id'] for r in pages if not r['matched_page_id']]
if missing: print('WARNING: missing candidate Page IDs for sources:',','.join(missing))
print('Original HTML and candidate Page context are evidence ONLY. No migration approval inferred.')
if drift or missing: sys.exit('FAIL: data drift or missing Page; review before proceeding')
print('PASS: 49 source HTML snapshots and candidate Page-context rows captured; database unchanged.')
PYCSV
