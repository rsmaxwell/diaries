#!/usr/bin/env bash
# Run from Windows PC Cygwin at the Diaries parent checkout root.
# READ-ONLY except new ignored feature evidence; no network, DB or Docker access.
# Never treats current checkout or frozen manifest as production authorisation.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  manifest="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
  test -f "$feature/IMPLEMENTATION-STEPS.md" || { echo 'FAIL: run from Windows Diaries parent repo root' >&2; exit 1; }
  test -f "$feature/tools/0028-step3-readiness-audit.py" || { echo 'FAIL: readiness helper absent' >&2; exit 1; }
  test -d .git -o -f .git || { echo 'FAIL: .git metadata absent; do not run in exported source ZIP' >&2; exit 1; }
  test -d diaries-responder || { echo 'FAIL: responder submodule missing' >&2; exit 1; }
  test -f "$manifest/PREPARATION-RESULT.json" || { echo 'FAIL: frozen private prepared manifest missing' >&2; exit 1; }
  grep -Fxq '/evidence/Step 3/private/' "$feature/.gitignore" || { echo 'FAIL: private evidence ignored rule missing' >&2; exit 1; }
  command -v python3 >/dev/null || { echo 'FAIL: Python 3 required' >&2; exit 1; }
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-offline-readiness"
  test ! -e "$out" || { echo "FAIL: output already exists: $out" >&2; exit 1; }
  mkdir -p "$out"
  echo "Private Step 3 readiness evidence: $out"
  echo '=== Inspect Windows parent and Git submodules (READ-ONLY) ==='
  {
    echo "UTC: $stamp"
    echo '--- parent branch and revision ---'
    git branch --show-current
    git rev-parse HEAD
    echo '--- parent changes ---'
    git status --short
    echo '--- recorded submodule revisions and dirtiness ---'
    git submodule status
    for dir in diaries-responder diaries-client diaries-web; do
      echo "--- $dir branch, revision, changes ---"
      git -C "$dir" branch --show-current
      git -C "$dir" rev-parse HEAD
      git -C "$dir" status --short
    done
  } > "$out/checkout-and-submodules.txt" 2>&1 || { echo 'FAIL: could not inspect Git working copy; see private checkout record' >&2; exit 1; }
  echo 'PASS: captured current Windows parent and all submodule revisions/status (not claiming clean)'
  echo '=== Validate frozen reviewed manifest with no production access ==='
  python3 "$feature/tools/0028-step3-readiness-audit.py" --manifest "$manifest" --output "$out"
  echo '=== Record gate boundaries ==='
  cat > "$out/GATE-STATUS.txt" <<'GATES'
0028 Step 1: technically validated, formal owner signoff not yet recorded.
0028 Step 2: accepted integration logs exist; owner GUI image/navigation checks pass.
0028 Step 2 preserved external hyperlink click: pending owner confirmation.
0053-DEF: separate non-blocking Editor lock-release defect; remains open.
0028 Step 3 production source freshness/active locks/writer stop: NOT CHECKED HERE.
0028 Step 3 fresh verified production backups: NOT CHECKED HERE.
0028 Step 3 production apply: NOT AUTHORISED.
0028 Step 4 final feature closure: NOT AUTHORISED.
GATES
  echo 'PASS: 0028 offline production-readiness audit complete; NO database or MQTT access'
) && echo '0028 OFFLINE READINESS: PASS; PRODUCTION APPLY NOT AUTHORISED' || {
  rc=$?
  echo "FAIL: 0028 offline readiness audit incomplete (exit $rc)" >&2
  exit "$rc"
}
