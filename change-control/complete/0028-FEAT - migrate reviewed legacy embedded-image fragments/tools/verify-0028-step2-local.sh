#!/usr/bin/env bash
# Standalone read-only verification (Windows PC Cygwin). No DB or MQTT calls.
# Fail-fast is confined to this non-interactive script.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  [[ -f "$feature/IMPLEMENTATION-STEPS.md" ]] || { echo 'FAIL: run from Windows Diaries checkout root' >&2; exit 1; }
  [[ -f './gradlew' ]] || { echo 'FAIL: Gradle wrapper missing' >&2; exit 1; }
  [[ -f '.gitmodules' ]] || { echo 'FAIL: parent .gitmodules missing' >&2; exit 1; }
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  out="$feature/evidence/Step 2/private/${stamp}-java-check"
  mkdir -p "$out"
  {
    echo "UTC: $stamp"
    echo 'Parent:'
    git branch --show-current
    git rev-parse HEAD
    git status --short
    git submodule status
    echo 'Responder:'
    git -C diaries-responder branch --show-current
    git -C diaries-responder rev-parse HEAD
    git -C diaries-responder status --short
  } > "$out/checkout.txt" 2>&1
  echo "Evidence: $out"
  echo '=== Full responder Gradle classes and JUnit tests ==='
  # Full responder tests rather than test-only stubs; preserve visible diagnostics.
  if ./gradlew --no-daemon :diaries-responder:classes :diaries-responder:test 2>&1 | tee "$out/gradle.log"; then
    echo 'PASS: responder Gradle classes and full JUnit suite'
  else
    rc=$?
    printf 'FAIL: Gradle verification failed with status %s; see %s/gradle.log\n' "$rc" "$out" >&2
    printf 'FAIL: Gradle exit code %s\n' "$rc" > "$out/RESULT.txt"
    exit "$rc"
  fi
  manifest="$feature/evidence/Step 1/private/20261123T144651Z-reviewed-manifest-prepared"
  [[ -f "$manifest/PREPARATION-RESULT.json" ]] || {
    echo "FAIL: expected prepared Step 1 manifest missing: $manifest" >&2
    echo 'FAIL: manifest unavailable' > "$out/RESULT.txt"
    exit 1
  }
  command -v cygpath >/dev/null || { echo 'FAIL: run in Windows Cygwin' >&2; exit 1; }
  echo '=== Validate all 72 actual prepared decisions with compiled Java command (NO DB) ==='
  if ./gradlew --no-daemon :diaries-responder:migration0028ReviewedFragments \
       -PmigrationMode=validate-manifest \
       "-PmigrationManifest=$(cygpath -aw "$manifest")" \
       "-PmigrationOutput=$(cygpath -aw "$out/manifest-validation")" \
       2>&1 | tee "$out/manifest-validation.log"; then
    echo 'PASS: offline Java reviewed-manifest validation'
    printf 'PASS: Java build/tests and reviewed manifest validation, no DB changes\n' > "$out/RESULT.txt"
  else
    rc=$?
    printf 'FAIL: actual reviewed-manifest validation failed (%s)\n' "$rc" >&2
    printf 'FAIL: actual reviewed-manifest validation failed (%s)\n' "$rc" > "$out/RESULT.txt"
    exit "$rc"
  fi
) && echo 'PASS: 0028 Step 2 local Java verification completed' || {
  rc=$?
  echo 'FAIL: 0028 Step 2 local Java verification incomplete' >&2
  exit "$rc"
}
