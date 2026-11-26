#!/usr/bin/env bash
# Run in a NON-INTERACTIVE bash process; safe to call as `bash script` from Cygwin.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
evidence="$feature/evidence/step-2-development-preflight"
map="$feature/reports/0029-49-placement-provisional-20261125.csv"
source="$evidence/0029-49-source-context-20261125-193610.csv"
pages="$evidence/0029-49-page-context-20261125-193610.csv"
verifier="$feature/tools/step2-49-verify-rehearsal-readonly.py"
compose='compose.development-infrastructure.yaml'
env1='config/environments/development-infrastructure.env'
env2='config/environments/local.env'
for f in "$map" "$source" "$pages" "$verifier" "$compose" "$env1" "$env2"; do
  [[ -f "$f" ]] || { echo "FAIL: missing $f" >&2; exit 2; }
done
mkdir -p "$evidence"
stamp=$(date -u +%Y%m%d-%H%M%S)
sql="$evidence/0029-49-live-precheck-$stamp.sql"
result="$evidence/0029-49-live-precheck-$stamp.csv"
errors="$evidence/0029-49-live-precheck-$stamp.stderr.txt"
python "$verifier" generate --mapping "$map" --source "$source" --pages "$pages" > "$sql"
opts=(-f "$compose" --env-file "$env1" --env-file "$env2")
docker compose "${opts[@]}" config --quiet
if ! docker compose "${opts[@]}" exec -T diaries-db sh -c 'exec psql -X -q -t -v ON_ERROR_STOP=1 -U "$POSTGRES_USER" -d "$POSTGRES_DB"' < "$sql" > "$result" 2> "$errors"; then
 echo 'FAIL: read-only database check failed:' >&2; cat "$errors" >&2; exit 1
fi
python "$verifier" check --mapping "$map" --source "$source" --pages "$pages" --result "$result"
echo "Evidence: $result"
echo 'No database modification. No migration or content-equivalence approval.'
