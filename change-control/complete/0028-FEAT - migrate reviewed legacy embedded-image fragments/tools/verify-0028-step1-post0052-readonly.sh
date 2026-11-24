#!/usr/bin/env bash
# Windows PC / Cygwin, from the Diaries parent repository root.
# One read-only production inventory, V2 draft check, and post-0052 catalogue
# reconciliation. No migration, no writes to PostgreSQL/Files/MQTT.
(
  set -euo pipefail
  feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
  private="$feature/evidence/Step 1/private"
  frozen="$private/20261118T093606Z"
  old="$private/20261121T122838Z-post0051-current/current-schema-snapshot.PRIVATE.csv"
  proposals="$private/0028-proposed-review.PRIVATE.csv"
  prior="$private/20261120-export-15-review-check/0028-human-review.DRAFT.PRIVATE.json"
  review="${1:-$private/0028-0051-review-v2.RECOVERED-598-CONFIRMED.PRIVATE.json}"
  inventory="$feature/tools/step1_inventory.py"
  checker="$feature/tools/step4_0051_compatibility_review.py"
  reconciler="$feature/tools/step1_post0052_reconcile_readonly.py"
  testfile="$feature/tests/test_step1_post0052_reconcile.py"
  for file in "$frozen/SHA256SUMS.txt" "$frozen/current-schema-snapshot.PRIVATE.csv" \
              "$old" "$proposals" "$prior" "$review" "$inventory" "$checker" \
              "$reconciler" "$testfile"; do
    if [[ ! -f "$file" ]]; then
      echo "FAIL: missing prerequisite (private draft may need recovery ZIP): $file" >&2
      exit 1
    fi
  done
  if [[ $(git branch --show-current) != main ]]; then
    echo 'FAIL: run from the authoritative Windows Diaries main checkout' >&2
    exit 1
  fi
  if ! grep -Fxq '/evidence/Step 1/private/' "$feature/.gitignore"; then
    echo 'FAIL: private evidence ignore policy is not present' >&2
    exit 1
  fi
  command -v python3 >/dev/null
  command -v ssh >/dev/null
  echo '=== Non-mutating regression tests ==='
  python3 -m unittest discover -s "$feature/tests" -p 'test_step1_post0052_reconcile.py' -v

  stamp=$(date -u +%Y%m%dT%H%M%SZ)
  run="$private/${stamp}-post0052-readonly"
  if [[ -e "$run" ]]; then
    echo "FAIL: evidence output already exists: $run" >&2
    exit 1
  fi
  mkdir -p "$run"
  chmod 700 "$run"
  {
    date -u '+UTC: %Y-%m-%dT%H:%M:%SZ'
    echo 'Diaries parent branch and revision:'
    git branch --show-current
    git rev-parse HEAD
    echo 'Diaries parent status:'
    git status --short
    echo 'Submodule identities:'
    git submodule status
    echo 'Submodule working trees:'
    git -C diaries-client status --short
    git -C diaries-responder status --short
    git -C diaries-web status --short
    echo 'Review input sha256:'
    sha256sum "$review"
  } > "$run/git-and-input-identity.txt" 2>&1

  echo '=== Fresh production inventory: read-only COPY SELECT via SSH to pluto ==='
  python3 "$inventory" --ssh-host pluto --output "$run/current"

  echo '=== Check all 72 recovered decisions against frozen and fresh source ==='
  python3 "$checker" check \
    --proposals "$proposals" --frozen "$frozen" \
    --prior-v1-draft "$prior" --decisions "$review" \
    --current-snapshot "$run/current/current-schema-snapshot.PRIVATE.csv" \
    --output "$run/checked"

  echo '=== Catalogue and legacy candidate reconciliation after 0052 ==='
  python3 "$reconciler" \
    --frozen-snapshot "$frozen/current-schema-snapshot.PRIVATE.csv" \
    --previous-snapshot "$old" \
    --current-snapshot "$run/current/current-schema-snapshot.PRIVATE.csv" \
    --current-candidates "$run/current/0028-image-decisions.UNREVIEWED.csv" \
    --proposals "$proposals" --review "$review" --output "$run/mapped"

  python3 - "$run/checked/0028-0051-v2-review-check.json" \
              "$run/mapped/0028-post0052-reconciliation-summary.json" <<'PYREPORT'
import json,sys
check, report = [json.load(open(p, encoding='utf-8')) for p in sys.argv[1:]]
print('=== Consolidated aggregate result ===')
print('V2 reviewed occurrence blockers:', check['rowsWithBlockers'])
print('V2 dispositions:', json.dumps(check['byDisposition'],sort_keys=True))
print('Catalogue mapping:',report['status'])
print('Corrected Image IDs:', ','.join(report['catalogue_metadata_changed_image_ids']))
if check['rowsWithBlockers'] or report['status']!='PASS' or \
        check['productionApplyAllowed'] or report['productionApplyAllowed']:
    raise SystemExit('FAIL: Step 1 post-0052 reconciliation did not pass')
if report['reviewed_conversions']!=71 or report['explicit_deferred']!=1:
    raise SystemExit('FAIL: Reviewed conversion coverage mismatch')
print('PASS: Step 1 refreshed database and catalogue reconciliation, READ-ONLY')
print('Step 1 formal acceptance, exact migration manifest and production apply remain separate')
PYREPORT
  echo "Private evidence: $run"
) || {
  rc=$?
  echo "FAIL: 0028 Step 1 post-0052 read-only reconciliation incomplete (exit $rc)" >&2
  exit "$rc"
}
