#!/usr/bin/env bash
# Windows PC / Cygwin. Evidence-only: no SSH, Docker, SQL, services or backup writes.
# Fail-fast settings are isolated in a subshell, not in the interactive shell.
(
  set -euo pipefail
  umask 077
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  prior="$feature/evidence/Step 3/private/20261124T142644Z-retained-restore-and-writers"
  python="$feature/tools/step3_release_gate_assessment.py"
  test -f "$feature/IMPLEMENTATION-STEPS.md" || { echo 'FAIL: run from Windows Diaries parent repository root' >&2; exit 2; }
  test -f "$python" || { echo 'FAIL: release assessment tool missing' >&2; exit 2; }
  test -s "$prior/pluto-writer-channels.json" || { echo 'FAIL: accepted production writer receipt missing' >&2; exit 2; }
  test -s "$prior/READINESS-RESULT.json" || { echo 'FAIL: accepted recovery receipt missing' >&2; exit 2; }
  grep -Fxq '/evidence/Step 3/private/' "$feature/.gitignore" || {
    echo 'FAIL: private Step 3 evidence must be Git ignored' >&2; exit 2;
  }
  echo '=== Release-gate evidence regression tests ==='
  python3 "$feature/tests/test_step3_release_gate_assessment.py"
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 3/private/${stamp}-maintenance-gate-assessment"
  test ! -e "$out" || { echo 'FAIL: refusing to overwrite prior evidence' >&2; exit 2; }
  mkdir -p "$out"
  echo '=== Verify accepted writer/recovery receipts (LOCAL only) ==='
  python3 "$python" --writer "$prior/pluto-writer-channels.json" \
    --recovery "$prior/READINESS-RESULT.json" --output "$out/MAINTENANCE-GATES.json"
  echo '=== Record current source-control identities (without changing Git) ==='
  {
    echo 'Parent branch / revision:'
    git branch --show-current
    git rev-parse HEAD
    git status --short
    echo 'Submodule pinned and working revisions:'
    git submodule status
    for name in diaries-responder diaries-client diaries-web; do
      git -C "$name" rev-parse HEAD
      git -C "$name" status --short
    done
    echo 'Migration CLI and Gradle source digests:'
    sha256sum diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/migration/migration0028/Migration0028ReviewedFragments.java \
              diaries-responder/build.gradle
  } > "$out/WINDOWS-CHECKOUT-IDENTITY.txt" 2>&1
  echo "PASS: release-gate assessment recorded: $out"
  echo 'This script NEVER stops writers, creates backups, or authorises apply.'
) && echo '0028 MAINTENANCE PREPARATION: PASS; PRODUCTION APPLY NOT AUTHORISED' || {
  rc=$?
  echo "FAIL: 0028 maintenance preparation incomplete (exit $rc)" >&2
  exit "$rc"
}
