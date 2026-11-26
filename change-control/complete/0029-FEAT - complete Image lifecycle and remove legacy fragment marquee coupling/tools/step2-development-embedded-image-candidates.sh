#!/usr/bin/env bash
# Windows Cygwin, at Diaries parent repository root. DEVELOPMENT database only.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
sql="$feature/tools/step2-development-embedded-image-candidates.sql"
evidence="$feature/evidence/step-2-development-preflight"
compose='compose.development-infrastructure.yaml'
env1='config/environments/development-infrastructure.env'
env2='config/environments/local.env'
for required in "$sql" "$compose" "$env1" "$env2"; do
  if [[ ! -f "$required" ]]; then echo "FAIL: missing $required" >&2; exit 2; fi
done
if ! command -v docker >/dev/null 2>&1; then echo 'FAIL: Docker not found' >&2; exit 2; fi
mkdir -p "$evidence"
output="$evidence/embedded-image-candidates-$(date -u +%Y%m%d-%H%M%S).txt"
opts=(-f "$compose" --env-file "$env1" --env-file "$env2")
echo 'Development Compose validation; READ ONLY SQL follows.'
docker compose "${opts[@]}" config --quiet
if docker compose "${opts[@]}" exec -T diaries-db sh -c \
  'exec psql -X -v ON_ERROR_STOP=1 -P pager=off -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < "$sql" 2>&1 | tee "$output"; then
  echo "PASS: read-only candidate scan. Evidence: $output"
else
  echo "FAIL: read-only candidate scan. Evidence: $output" >&2
  exit 1
fi
