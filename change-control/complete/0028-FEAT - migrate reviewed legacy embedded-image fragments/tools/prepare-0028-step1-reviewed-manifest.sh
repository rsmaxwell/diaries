#!/usr/bin/env bash
# Windows PC / Cygwin shell. From the Windows Diaries parent checkout root.
# Review and frozen evidence only; no PostgreSQL, MQTT or Files-root writes.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  private="$feature/evidence/Step 1/private"
  run="${1:-$private/20261123T143827Z-post0052-readonly}"
  review="$private/0028-0051-review-v2.RECOVERED-598-CONFIRMED.PRIVATE.json"
  generator="$feature/tools/step1_prepare_reviewed_manifest.py"
  tests="$feature/tests/test_step1_manifest_preparation.py"
  [[ -d "$run/checked" && -d "$run/mapped" && -d "$run/current" ]] || {
    echo "FAIL: missing Step 1 reconciliation evidence directory: $run" >&2; exit 1;
  }
  [[ -f "$review" && -f "$generator" && -f "$tests" ]] || {
    echo 'FAIL: missing recovered draft or Step 1 manifest tool/test' >&2; exit 1;
  }
  [[ $(git branch --show-current) == main ]] || {
    echo 'FAIL: run from the Windows Diaries parent main checkout' >&2; exit 1;
  }
  grep -Fxq '/evidence/Step 1/private/' "$feature/.gitignore" || {
    echo 'FAIL: private evidence Git exclusion missing' >&2; exit 1;
  }
  command -v python3 >/dev/null || { echo 'FAIL: Python 3 not found' >&2; exit 1; }
  command -v sha256sum >/dev/null || { echo 'FAIL: sha256sum not found' >&2; exit 1; }
  echo '=== Run synthetic, non-mutating manifest tests ==='
  python3 -m unittest discover -s "$feature/tests" -p test_step1_manifest_preparation.py -v
  echo '=== Verify existing mapped evidence digests ==='
  (cd "$run/mapped" && sha256sum -c SHA256SUMS.txt)
  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  dest="$private/${stamp}-reviewed-manifest-prepared"
  [[ ! -e "$dest" ]] || { echo "FAIL: output exists: $dest" >&2; exit 1; }
  echo '=== Prepare reviewed Step 1 manifest inputs (READ-ONLY) ==='
  python3 "$generator" \
    --review "$review" \
    --snapshot "$run/current/current-schema-snapshot.PRIVATE.csv" \
    --mapping "$run/mapped/0028-current-catalogue-mapping.PRIVATE.csv" \
    --check "$run/checked/0028-0051-v2-review-check.json" \
    --summary "$run/mapped/0028-post0052-reconciliation-summary.json" \
    --output "$dest"
  {
    echo 'Windows parent revision:'
    git branch --show-current
    git rev-parse HEAD
    echo 'Windows parent and submodule state (read-only):'
    git status --short
    git submodule status
    git -C diaries-responder status --short
    echo 'Evidence source directory:'
    printf '%s\n' "$run"
  } > "$dest/git-and-input-identity.txt"
  echo '=== Verify prepared file digests ==='
  (cd "$dest" && sha256sum -c SHA256SUMS.txt)
  echo 'PASS: 0028 Step 1 prepared migration inputs complete; NOT owner-approved for apply'
  echo "PRIVATE evidence: $dest"
) && echo 'PASS: 0028 Step 1 prepared manifest workflow complete' || {
  rc=$?
  echo "FAIL: 0028 Step 1 manifest preparation incomplete (exit $rc)" >&2
  exit "$rc"
}
