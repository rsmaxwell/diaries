#!/usr/bin/env bash
# Windows Cygwin: run from Diaries parent repository root.
# Only development-infrastructure PostgreSQL; never production.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
sql="$feature/tools/step2-development-0028-reconciliation.sql"
evidence="$feature/evidence/step-2-development-preflight"
compose='compose.development-infrastructure.yaml'
env1='config/environments/development-infrastructure.env'
env2='config/environments/local.env'
for required in "$sql" "$compose" "$env1" "$env2"; do
  if [[ ! -f "$required" ]]; then printf 'FAIL: missing %s\n' "$required" >&2; exit 2; fi
done
if ! command -v docker >/dev/null 2>&1; then echo 'FAIL: Docker unavailable' >&2; exit 2; fi
mkdir -p "$evidence"
output="$evidence/reconciliation-$(date -u +%Y%m%d-%H%M%S).txt"
opts=(-f "$compose" --env-file "$env1" --env-file "$env2")
printf 'Development DB only. Checking Docker Compose configuration...\n'
docker compose "${opts[@]}" config --quiet
printf 'Collecting READ-ONLY reconciliation evidence in %s\n' "$output"
# SQL executes inside an explicit REPEATABLE READ / READ ONLY transaction.
# PostgreSQL shell uses its own POSTGRES_USER/POSTGRES_DB environment.
if docker compose "${opts[@]}" exec -T diaries-db sh -c \
  'exec psql -X -v ON_ERROR_STOP=1 -P pager=off -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < "$sql" 2>&1 | tee "$output"; then
  printf '\nPASS: query completed (read-only). Evidence: %s\n' "$output"
else
  printf '\nFAIL: query failed; inspect evidence: %s\n' "$output" >&2
  exit 1
fi
