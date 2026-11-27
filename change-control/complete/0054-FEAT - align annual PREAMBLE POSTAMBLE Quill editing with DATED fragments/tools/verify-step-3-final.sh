#!/usr/bin/env bash
# 0054-FEAT final client verification. Run using Cygwin Bash from the Diaries parent repository.
# Does not deploy or commit anything; evidence is stored in the 0054 feature directory.

FEATURE='change-control/in-progress/0054-FEAT - align annual PREAMBLE POSTAMBLE Quill editing with DATED fragments'
EVIDENCE="$FEATURE/evidence/step-3-final-verification"

if [ ! -f .gitmodules ] || [ ! -d diaries-client ] || [ ! -d diaries-web ] || [ ! -f gradlew ]; then
  printf 'FAIL: run from the Diaries parent repository root\n' >&2
  exit 2
fi
if ! mkdir -p "$EVIDENCE"; then
  printf 'FAIL: cannot create evidence directory: %s\n' "$EVIDENCE" >&2
  exit 2
fi

{
  printf '%s\n' '=== Capture time (UTC) ==='
  date -u '+%Y-%m-%dT%H:%M:%SZ'
  printf '%s\n' '=== Host and Bash ==='
  hostname
  bash --version | head -n 1
  printf '%s\n' '=== Parent HEAD/status ==='
  git rev-parse HEAD
  git status --short --branch
  printf '%s\n' '=== Submodule revisions ==='
  git submodule status
  printf '%s\n' '=== .gitmodules ==='
  cat .gitmodules
  for module in diaries-client diaries-responder diaries-web; do
    if [ -d "$module" ]; then
      printf '\n=== %s HEAD/status ===\n' "$module"
      ( cd "$module" && git rev-parse HEAD && git status --short --branch )
    fi
  done
} > "$EVIDENCE/git-state.log" 2>&1
STATE_RC=$?

( cd diaries-client && npx ng test --watch=false --browsers=ChromeHeadless \
    --include=src/app/fragment/quill-text-toolbar.spec.ts \
    --include=src/app/diary/annual-editor/annual-editor.component.spec.ts \
    --include=src/app/diary/annual-editor/annual-quill-preview.directive.spec.ts \
    --include=src/app/fragment/text-panel/text-panel.component.spec.ts \
) > "$EVIDENCE/angular-tests.log" 2>&1
TEST_RC=$?

( cd diaries-client && npm run build ) > "$EVIDENCE/angular-build.log" 2>&1
BUILD_RC=$?

{
  printf 'Git state capture: %s\n' "$STATE_RC"
  printf 'Angular tests: %s\n' "$TEST_RC"
  printf 'Angular build: %s\n' "$BUILD_RC"
  printf 'Reader tests/build: prior accepted evidence; not rerun (no subsequent Reader changes)\n'
  printf 'Browser acceptance: previously reported by owner; final acceptance still pending\n'
  if [ "$STATE_RC" -eq 0 ] && [ "$TEST_RC" -eq 0 ] && [ "$BUILD_RC" -eq 0 ]; then
    printf 'RESULT: PASS — final client automated verification\n'
  else
    printf 'RESULT: FAIL — inspect the three logs\n'
  fi
} | tee "$EVIDENCE/results.txt"

printf 'Evidence directory: %s\n' "$EVIDENCE"
if [ "$STATE_RC" -ne 0 ] || [ "$TEST_RC" -ne 0 ] || [ "$BUILD_RC" -ne 0 ]; then
  exit 1
fi
