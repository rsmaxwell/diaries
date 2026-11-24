#!/usr/bin/env bash
# Windows PC Cygwin; strictly read-only pluto SSH/Docker/Systemd inventory.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  script="$feature/tools/0028_step3_runtime_inventory.py"
  test -f "$script" && test -f "$feature/IMPLEMENTATION-STEPS.md" || {
    echo 'FAIL: run from Windows Diaries parent root after applying ZIP' >&2; exit 2;
  }
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-release-runtime"
  test ! -e "$out" || { echo 'FAIL: evidence already exists' >&2; exit 2; }
  mkdir -p "$out"
  echo '=== pluto: inspect current Compose/systemd release contract (READ-ONLY) ==='
  if ! ssh pluto 'python3 -' < "$script" > "$out/pluto-release-runtime.json" 2> "$out/pluto-release-runtime.err"; then
    echo "FAIL: pluto read-only survey, error: $out/pluto-release-runtime.err" >&2; exit 2;
  fi
  python3 - "$out/pluto-release-runtime.json" <<'PYCODE'
import json,sys
v=json.load(open(sys.argv[1],encoding='utf-8'))
assert v['mode']=='READ_ONLY_RELEASE_CONTRACT'
assert v['writerIsolationVerified'] is False
assert v['productionApplyAuthorised'] is False
print('PASS: live identities and service/backup supervision recorded')
print('PostgreSQL published host port:',v['publishedPostgresHostPort'])
print('Responder image:',v['containers']['diaries-responder']['image'])
print('Original service states are recorded, but writer isolation is NOT proved')
PYCODE
  echo "Private receipt: $out"
  echo 'PRODUCTION APPLY NOT AUTHORISED'
)