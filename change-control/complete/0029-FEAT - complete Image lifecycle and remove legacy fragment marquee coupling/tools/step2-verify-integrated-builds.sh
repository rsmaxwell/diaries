#!/usr/bin/env bash
# Windows Cygwin: run with bash "${FEATURE}/tools/step2-verify-integrated-builds.sh" from parent root.
# Read-only for databases and production. Builds may write generated outputs locally.
ROOT="$(pwd)"
FEATURE="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
if [[ ! -f "$ROOT/settings.gradle" || ! -f "$ROOT/diaries-client/package.json" || ! -f "$ROOT/$FEATURE/IMPLEMENTATION-STEPS.md" ]]; then
  echo 'FAIL: run from the Diaries parent repository root' >&2
  exit 2
fi
EVIDENCE="$ROOT/$FEATURE/evidence/step-2-build"
mkdir -p "$EVIDENCE"
: > "$EVIDENCE/verification-summary.txt"
record() {
  local label="$1" logfile="$2"; shift 2
  echo "=== $label ==="
  ( "$@" ) >"$EVIDENCE/$logfile" 2>&1
  local rc=$?
  cat "$EVIDENCE/$logfile"
  if (( rc == 0 )); then
    echo "PASS: $label" | tee -a "$EVIDENCE/verification-summary.txt"
  else
    echo "FAIL: $label (exit $rc) — $logfile" | tee -a "$EVIDENCE/verification-summary.txt"
  fi
}
record 'Parent Git baseline' 01-git-baseline.log bash -c 'git status --short --branch; git submodule status; git -C diaries-client status --short --branch; git -C diaries-responder status --short --branch; git -C diaries-web status --short --branch'
record 'Parent and submodule diff whitespace' 02-diff-check.log bash -c 'git diff --check && git -C diaries-client diff --check && git -C diaries-responder diff --check && git -C diaries-web diff --check'
record 'Responder compile and tests' 03-responder-test.log bash ./gradlew :diaries-responder:test --stacktrace
record 'Reader compile and tests' 04-reader-test.log bash ./gradlew :diaries-web:test --stacktrace
if [[ -x "$ROOT/diaries-client/node_modules/.bin/ng" ]]; then
  record 'Angular production build' 05-angular-build.log bash -c 'cd diaries-client && npm run build'
  record 'Angular ChromeHeadless tests' 06-angular-test.log bash -c 'cd diaries-client && npm test -- --watch=false --browsers=ChromeHeadless'
else
  echo 'NOT RUN: Angular build/tests — dependencies missing; run npm ci in diaries-client, then rerun verification' | tee -a "$EVIDENCE/verification-summary.txt"
fi
echo '=== SUMMARY ==='
cat "$EVIDENCE/verification-summary.txt"
echo "Evidence directory: $EVIDENCE"
