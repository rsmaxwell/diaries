#!/usr/bin/env bash
# 0029 Step 3 - read-only source and published-backup checks.
# Run from the Windows Cygwin Diaries parent checkout.
set -o pipefail
FEATURE='change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling'
EVIDENCE="$FEATURE/evidence/step-3-release-source-and-recovery"
mkdir -p "$EVIDENCE" || exit 1
STAMP="$(date -u +%Y%m%d-%H%M%S)"
LOG="$EVIDENCE/audit-$STAMP.log"
{
  echo "0029 STEP 3 RELEASE SOURCE / PUBLISHED BACKUP READ-ONLY AUDIT UTC=$(date -u +%FT%TZ)"
  echo '== Windows source worktree (uncommitted work preserved) =='
  git status --short --branch
  git rev-parse HEAD
  git submodule status
  for sub in diaries-client diaries-responder diaries-web; do
    echo "--- $sub ---"
    git -C "$sub" status --short --branch
    git -C "$sub" rev-parse HEAD
    git -C "$sub" diff --check || exit 1
  done
  git diff --check || exit 1
  echo 'PASS: source provenance and whitespace checks'
  echo '== Published production backup verification (metadata/dump only; no restore) =='
  ssh pluto 'bash -s' <<'REMOTE'
set -o pipefail
ROOT=/home/richard/projects/diaries/data/diaries-backup
if [ ! -d "$ROOT" ]; then echo "FAIL: published root is not a directory: $ROOT"; exit 1; fi
python3 - "$ROOT" <<'PY_REMOTE'
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]);manifest=root/'dataset-manifest.json'
if not manifest.is_file(): raise SystemExit('FAIL: missing dataset-manifest.json')
data=json.loads(manifest.read_text())
print('backupId:',data.get('backupId'))
print('status:',data.get('status'))
print('logicalDataset:',data.get('logicalDataset'))
print('createdCompletedAt:',data.get('createdCompletedAt'))
print('durableFileCount:',data.get('counts',{}).get('durableFileCount'))
print('filesTotalBytes:',data.get('files',{}).get('snapshot',{}).get('totalBytes'))
if data.get('status')!='complete' or data.get('backupType')!='complete-dataset': raise SystemExit('FAIL: manifest is not a completed dataset')
for rel in ('database/diaries.dump','database/diaries.sql','verification/database.sha256','verification/files.sha256','verification/inventory.json'):
 p=root/rel
 if not p.is_file() or p.is_symlink() or not p.stat().st_size: raise SystemExit('FAIL: missing/empty/unsafe '+rel)
 print('PRESENT:',rel,'bytes=',p.stat().st_size)
# Source format: each database.sha256 record includes hash and dataset-relative filename.
for line in (root/'verification/database.sha256').read_text().splitlines():
 if not line.strip(): continue
 pieces=line.split(maxsplit=1)
 if len(pieces)!=2: raise SystemExit('FAIL: invalid database.sha256 entry')
 expected,rel=pieces
 rel=rel.lstrip('*')
 p=Path(rel)
 if p.is_absolute() or '..' in p.parts: raise SystemExit('FAIL: unsafe checksum path')
 target=root/p
 if not target.is_file(): raise SystemExit('FAIL: checksum target missing: '+rel)
 digest=hashlib.file_digest(target.open('rb'),'sha256').hexdigest()
 if digest!=expected: raise SystemExit('FAIL: database digest mismatch: '+rel)
 print('PASS: sha256',rel)
print('PASS: published manifest metadata and database dump checksums')
print('NOT VERIFIED: every Files payload hash, database restore, or filesystem restore')
PY_REMOTE
rc=$?
if [ "$rc" -ne 0 ]; then exit "$rc"; fi
# Structural, read-only inspection of the published pg_dump custom archive.
if docker exec -i diaries-postgres pg_restore --list < "$ROOT/database/diaries.dump" >/dev/null; then
  echo 'PASS: pg_restore --list recognises published custom dump'
else
  echo 'FAIL: pg_restore --list could not read published dump'
  exit 1
fi
REMOTE
  rc=$?
  if [ "$rc" -ne 0 ]; then echo 'FAIL: published backup check'; exit "$rc"; fi
  echo 'PASS: release-source and backup metadata/dump checks'
  echo 'NOT YET COMPLETE: full Files hash verification and disposable database/Files recovery verification; immutable Git release commits; new image builds'
} 2>&1 | tee "$LOG"
rc=${PIPESTATUS[0]}
echo "Evidence: $LOG"
if [ "$rc" -eq 0 ]; then echo 'RESULT: PASS for checks run (not production deployment authorisation)'; else echo "RESULT: FAIL ($rc)"; fi
exit "$rc"
