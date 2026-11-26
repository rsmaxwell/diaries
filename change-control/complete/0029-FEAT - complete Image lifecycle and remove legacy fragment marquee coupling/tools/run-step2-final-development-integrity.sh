#!/usr/bin/env bash
# Windows Cygwin Bash: run from Diaries parent repository root.
# All SQL is read-only; only a feature-local verification log is created.
set -euo pipefail
feature='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
sql="$feature/tools/step2-final-development-integrity-readonly.sql"
evidence="$feature/evidence/step-2-final-development-integrity"
[ -f "$sql" ] || { echo "FAIL: run from the Diaries repository root, SQL not found"; exit 1; }
command -v docker >/dev/null || { echo 'FAIL: docker not found'; exit 1; }
mkdir -p "$evidence"
log="$evidence/final-development-integrity-$(date -u +%Y%m%d-%H%M%S).log"
echo "Read-only target: diaries-development-db; evidence: $log"
if (docker exec -i diaries-development-db psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries < "$sql") 2>&1 | tee "$log"; then
  echo "PASS: read-only integrity check complete; $log"
else
  echo "FAIL: integrity check; review $log" >&2
  exit 1
fi
