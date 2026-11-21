#!/usr/bin/env bash
# 0051 Step 4 offline source review (standalone noninteractive script).
# Does not connect to hosts, restore data or modify source/Playbooks files.
set -euo pipefail
feature='change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees'
legacy='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
if [[ ! -d "$feature" || ! -d "$legacy" || ! -f .gitmodules ]]; then
  echo 'FAIL: Run from the Diaries parent repository root' >&2; exit 2
fi
run="$feature/evidence/Step 4/private/offline-$(date -u +%Y%m%dT%H%M%SZ)"
if [[ -e "$run" ]]; then echo 'FAIL: evidence directory exists' >&2; exit 2; fi
mkdir -p "$run"
{
  echo '=== Diaries parent revision/status ==='
  git branch --show-current; git rev-parse HEAD; git status --short; git submodule status
  for project in diaries-client diaries-responder diaries-web; do
    echo "=== $project revision/status ==="
    git -C "$project" branch --show-current
    git -C "$project" rev-parse HEAD
    git -C "$project" status --short
  done
} > "$run/git-revisions.log" 2>&1
if python3 -m unittest discover -s "$legacy/tests" -p 'test_step4_0051_compatibility_review.py' -q > "$run/0028-tests.log" 2>&1 &&
   python3 -m unittest discover -s "$legacy/tests" -p 'test_step1_inventory.py' -q >> "$run/0028-tests.log" 2>&1; then
  echo 'PASS: 0028 source regression'; tail -6 "$run/0028-tests.log"
else
  echo 'FAIL: 0028 source regression'; tail -80 "$run/0028-tests.log"; exit 1
fi
if python3 "$feature/tools/step4-static-rollout-preflight.py" --repo . \
   --output "$run/static-rollout-preflight.json" > "$run/static-preflight.log" 2>&1; then
  echo 'PASS: 0051 static source preflight'
else
  echo 'FAIL: 0051 static source preflight'; cat "$run/static-preflight.log"; exit 1
fi
# Use the immutable historical 0028 inputs for an OFFLINE/private v2 draft.
# Unlike a migration, this only produces a new review worksheet/check report.
source_private="$legacy/evidence/Step 1/private"
proposals="$source_private/0028-proposed-review.PRIVATE.csv"
frozen="$source_private/20261118T093606Z"
v1="$source_private/20261120-export-15-review-check/0028-human-review.DRAFT.PRIVATE.json"
if [[ -f "$proposals" && -f "$v1" && -f "$frozen/SHA256SUMS.txt" ]]; then
  draft="$run/v2-private-draft"
  review="$run/v2-private-check"
  if python3 "$legacy/tools/step4_0051_compatibility_review.py" prepare \
       --proposals "$proposals" --frozen "$frozen" --prior-v1-draft "$v1" \
       --output "$draft" > "$run/v2-prepare.log" 2>&1 &&
     python3 "$legacy/tools/step4_0051_compatibility_review.py" check \
       --proposals "$proposals" --frozen "$frozen" --prior-v1-draft "$v1" \
       --decisions "$draft/0028-0051-review-v2.DRAFT.PRIVATE.json" \
       --output "$review" > "$run/v2-check.log" 2>&1; then
    echo 'PASS: 0028 private v2 preview/check completed; all existing decisions remain UNAPPROVED'
  else
    echo 'FAIL: 0028 private review verification'
    tail -45 "$run/v2-prepare.log" "$run/v2-check.log" 2>/dev/null
    exit 1
  fi
else
  echo 'SKIP: original private 0028 frozen/proposal/export inputs absent from this checkout'
fi
echo "Evidence: $run"
echo 'PASS: offline tests only; Step 4 rollout rehearsal and production gate remain OPEN'
