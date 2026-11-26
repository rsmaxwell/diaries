#!/usr/bin/env bash
# 0029-FEAT, Windows Cygwin from the Diaries parent repo root. Read-only.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
script="$feature/tools/step2-49-review-manifest.sql"
evidence="$feature/evidence/step-2-development-preflight"
compose='compose.development-infrastructure.yaml'
env1='config/environments/development-infrastructure.env'
env2='config/environments/local.env'
for f in "$script" "$compose" "$env1" "$env2"; do [[ -f "$f" ]] || { echo "FAIL missing $f" >&2; exit 2; }; done
mkdir -p "$evidence"
stamp=$(date -u +%Y%m%d-%H%M%S)
output="$evidence/0029-49-review-manifest-$stamp.csv"
errors="$evidence/0029-49-review-manifest-$stamp.stderr.txt"
opts=(-f "$compose" --env-file "$env1" --env-file "$env2")
docker compose "${opts[@]}" config --quiet
if docker compose "${opts[@]}" exec -T diaries-db sh -c   'exec psql -X -q -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"'   < "$script" > "$output" 2> "$errors"; then
  # Check CSV shape before reporting success; no alterations to source rows.
  python - "$output" <<'PYCSV'
import csv,sys
from collections import Counter
p=sys.argv[1]
with open(p,encoding='utf-8-sig',newline='') as f:
    rows=list(csv.DictReader(f))
counts=Counter(r['source_fragment_id'] for r in rows)
issues=[(r['source_fragment_id'],r['review_status']) for r in rows if r['image_candidate_count']!='1']
print(f'RESULT: {len(rows)} image occurrences across {len(counts)} source Fragments')
print('Review status:',dict(Counter(r['review_status'] for r in rows)))
if len(counts)!=49 or len(rows)!=49 or issues:
    print('FAIL: unexpected source/cardinality or catalogue matches:',issues)
    sys.exit(1)
print('PASS: exactly 49 uniquely matched candidate records (NOT content-equivalence approval)')
PYCSV
  echo "Evidence: $output"
else
  echo "FAIL: read-only manifest extraction; stderr $errors" >&2
  cat "$errors" >&2
  exit 1
fi
