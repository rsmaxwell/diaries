#!/usr/bin/env bash
# 0051 Step 3: local Windows Cygwin regression evidence. No production access.
# Run from the Windows Diaries parent checkout with: bash "<feature>/tools/verify-step3-local.sh"

repo="$(pwd)"
feature='change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'

if [ ! -f "$repo/gradlew" ] || [ ! -f "$repo/diaries-client/package.json" ] || [ ! -d "$repo/$feature" ]; then
  echo 'FAIL: run from the Diaries parent repository root (Windows Cygwin)' >&2
  exit 2
fi

stamp="$(date -u +%Y%m%dT%H%M%SZ)"
evidence="$repo/$feature/evidence/Step 3/private/run-$stamp"
mkdir -p "$evidence" || exit 2
printf 'Step 3 evidence: %s\n' "$evidence"

{
  printf 'UTC: %s\n' "$(date -u +%FT%TZ)"
  printf 'Repo: %s\n' "$repo"
  git branch --show-current
  git rev-parse HEAD
  git status --short
  git submodule status
  for module in diaries-client diaries-web diaries-responder; do
    printf '\n=== %s ===\n' "$module"
    git -C "$module" branch --show-current
    git -C "$module" rev-parse HEAD
    git -C "$module" status --short
  done
} > "$evidence/git-baseline.log" 2>&1

echo '=== Web reader Gradle build and tests ==='
if ./gradlew --no-daemon :diaries-web:build > "$evidence/web-build.log" 2>&1; then
  web_status=PASS
  echo 'PASS: Web reader build and tests'
else
  web_status=FAIL
  echo 'FAIL: Web reader build and tests'
  tail -80 "$evidence/web-build.log"
fi

echo '=== Angular Chrome Headless unit tests ==='
if (cd diaries-client && npm test -- --watch=false --browsers=ChromeHeadless) > "$evidence/client-tests.log" 2>&1; then
  client_test_status=PASS
  echo 'PASS: Angular tests'
else
  client_test_status=FAIL
  echo 'FAIL: Angular tests'
  tail -80 "$evidence/client-tests.log"
fi

echo '=== Angular production build ==='
if (cd diaries-client && npm run build) > "$evidence/client-build.log" 2>&1; then
  client_build_status=PASS
  echo 'PASS: Angular build'
else
  client_build_status=FAIL
  echo 'FAIL: Angular build'
  tail -80 "$evidence/client-build.log"
fi

{
  printf 'web_build=%s\n' "$web_status"
  printf 'client_tests=%s\n' "$client_test_status"
  printf 'client_build=%s\n' "$client_build_status"
} | tee "$evidence/result.txt"

if [ "$web_status" = PASS ] && [ "$client_test_status" = PASS ] && [ "$client_build_status" = PASS ]; then
  echo 'PASS: Step 3 local build/test gate (UI smoke still pending)'
else
  echo 'FAIL: Step 3 local build/test gate; preserve evidence and review failures'
  exit 1
fi
