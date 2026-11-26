#!/usr/bin/env bash
# Windows Cygwin; run from Diaries parent root. Source pluto: read-only; isolated local Docker writes.
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-production-recovery-verification"
mkdir -p "$EVIDENCE" || exit 1
STAMP=$(date -u '+%Y%m%d-%H%M%S')
LOG="$EVIDENCE/recovery-$STAMP-$$.log"
CID="diaries-0029-recovery-$STAMP-$$"
(
  set -euo pipefail
  exec > >(tee "$LOG") 2>&1
  for cmd in ssh docker git sha256sum; do command -v "$cmd" >/dev/null || { echo "FAIL missing $cmd"; exit 1; }; done
  test -f .gitmodules || { echo 'FAIL: must run from Diaries parent checkout'; exit 1; }
  echo "0029 STEP 3 RECOVERY VERIFICATION UTC=$(date -u '+%FT%TZ')"
  git rev-parse HEAD
  git submodule status
  echo 'Source: pluto published production backup (read-only).'
  # Pin a physical published generation, to avoid inadvertently switching backup generations midway.
  ROOT=$(ssh -o BatchMode=yes pluto 'readlink -f /home/richard/projects/diaries/data/diaries-backup')
  test -n "$ROOT" || { echo 'FAIL: published backup path unresolved'; exit 1; }
  echo "Pinned backup directory: $ROOT"
  # Check manifest, complete file hashes, and both database dump hashes on pluto.
  ssh -o BatchMode=yes pluto "python3 - '$ROOT'" <<'PY_REMOTE'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=json.loads((root/'dataset-manifest.json').read_text())
if manifest.get('status')!='complete' or manifest.get('backupType')!='complete-dataset':
 raise SystemExit('FAIL: published dataset not complete')
print('Backup ID:',manifest.get('backupId'))
print('Files expected:',manifest.get('counts',{}).get('durableFileCount'))
for filelist in ('verification/database.sha256','verification/files.sha256'):
 lines=(root/filelist).read_text().splitlines()
 if not lines: raise SystemExit('FAIL: empty '+filelist)
 checked=0
 for line in lines:
  digest,sep,rel=line.partition(' ')
  rel=rel.strip().lstrip('*')
  p=Path(rel)
  if len(digest)!=64 or p.is_absolute() or '..' in p.parts or not rel:
   raise SystemExit('FAIL: invalid digest/path in '+filelist)
  target=root/p
  if target.is_symlink() or not target.is_file():
   raise SystemExit('FAIL: missing or unsafe '+rel)
  with target.open('rb') as h: actual=hashlib.file_digest(h,'sha256').hexdigest()
  if actual!=digest: raise SystemExit('FAIL: hash mismatch '+rel)
  checked+=1
 print('PASS:',filelist,'verified entries=',checked)
 if filelist.endswith('files.sha256') and checked!=manifest.get('counts',{}).get('durableFileCount'):
  raise SystemExit('FAIL: Files manifest count mismatch')
print('PASS: published backup data checksums')
PY_REMOTE
  docker info >/dev/null
  cleanup() { docker rm -f "$CID" >/dev/null 2>&1 || true; }
  trap cleanup EXIT
  docker run -d --network none --name "$CID" -e POSTGRES_USER=diaries \
    -e POSTGRES_PASSWORD=rehearsal-only -e POSTGRES_DB=diaries postgres:18-alpine >/dev/null
  ready=0
  for i in $(seq 1 60); do
    if docker exec "$CID" pg_isready -U diaries -d diaries >/dev/null 2>&1; then ready=1; break; fi
    sleep 1
  done
  test "$ready" -eq 1 || { echo 'FAIL: isolated PostgreSQL not ready'; exit 1; }
  echo 'Restoring published custom dump (pluto read-only -> isolated PostgreSQL).'
  ssh -o BatchMode=yes pluto "cat '$ROOT/database/diaries.dump'" | \
    docker exec -i "$CID" pg_restore -U diaries -d diaries --no-owner --no-acl --exit-on-error
  docker exec "$CID" psql -X -v ON_ERROR_STOP=1 -U diaries -d diaries -Atc \
    'SELECT '\''RESTORED|fragments='\'' || count(*) FROM public.fragment;'
  echo 'RESTORE DATABASE: PASS'
  # Transfer published Files snapshot only into isolated container (no host filesystem writes).
  echo 'Copying published Files snapshot into disposable isolated container.'
  ssh -o BatchMode=yes pluto "tar -C '$ROOT' -cf - files" | docker exec -i "$CID" tar -C /tmp -xf -
  ssh -o BatchMode=yes pluto "cat '$ROOT/verification/files.sha256'" | \
    docker exec -i "$CID" sh -c 'cat > /tmp/files.sha256'
  docker exec "$CID" sh -c 'cd /tmp && sha256sum -c files.sha256' | \
    awk '/: OK$/ {n++; next} {print; bad=1} END {printf "Isolated Files hashes verified: %d\n",n; if(bad || n==0) exit 1}'
  echo 'RESTORE FILES: PASS'
  NOW=$(ssh -o BatchMode=yes pluto 'readlink -f /home/richard/projects/diaries/data/diaries-backup')
  if test "$NOW" != "$ROOT"; then echo 'NOTICE: published generation switched while verifying; pinned original was verified'; fi
  echo 'SUMMARY: PASS — published database restored and all Files payload hashes verified in isolated container.'
  echo 'PRODUCTION: no writes, no restarts, no destructive operations; isolated container auto-removed.'
)
rc=$?
if test "$rc" -eq 0; then echo "PASS: $LOG"; else echo "FAIL ($rc): $LOG"; fi
exit "$rc"
