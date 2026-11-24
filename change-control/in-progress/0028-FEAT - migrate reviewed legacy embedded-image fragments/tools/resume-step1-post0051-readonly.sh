#!/usr/bin/env bash
# 0028 Step 1 post-0051: one-off read-only production inventory + private v2 draft.
# Intended terminal: Windows 11 Cygwin at Diaries parent repository root.
# Run using bash path/to/script.sh (no shell options set in interactive caller).
set -euo pipefail

feature='change-control/in-progress/0028-FEAT - migrate reviewed legacy embedded-image fragments'
if [[ ! -f "$feature/tools/step1_inventory.py" || ! -f "$feature/tools/step4_0051_compatibility_review.py" ]]; then
    echo 'FAIL: Run from the Windows Diaries parent repository root with 0028 tools present' >&2
    exit 1
fi
if [[ $(git branch --show-current) != main ]]; then
    echo 'FAIL: Diaries parent repository must be on main; no checkout will be changed' >&2
    exit 1
fi
if [[ ! -f "$feature/.gitignore" ]] || ! grep -Fxq '/evidence/Step 1/private/' "$feature/.gitignore"; then
    echo 'FAIL: Private evidence ignore policy is absent' >&2
    exit 1
fi

private="$feature/evidence/Step 1/private"
frozen="$private/20261118T093606Z"
proposals="$private/0028-proposed-review.PRIVATE.csv"
prior="$private/20261120-export-15-review-check/0028-human-review.DRAFT.PRIVATE.json"
for required in "$frozen/SHA256SUMS.txt" "$proposals" "$prior"; do
    if [[ ! -f "$required" ]]; then
        echo "FAIL: Required historical private input missing: $required" >&2
        exit 1
    fi
done

run=$(date -u +%Y%m%dT%H%M%SZ)
current="$private/${run}-post0051-current"
review="$private/${run}-post0051-v2"
check="$private/${run}-post0051-v2-check"
for out in "$current" "$review" "$check"; do
    if [[ -e "$out" ]]; then
        echo "FAIL: Refusing to overwrite private evidence: $out" >&2
        exit 1
    fi
done

echo '=== 0028 Windows source state (read-only) ==='
git rev-parse HEAD
git submodule status
printf '%s\n' '=== Check local private source checksums and synthetic unit tests ==='
python3 -m unittest discover -s "$feature/tests" -p test_step1_inventory.py -v
python3 -m unittest discover -s "$feature/tests" -p test_step4_0051_compatibility_review.py -v

echo '=== Verify production Compose service presence (read-only) ==='
ssh -T pluto 'cd "$HOME/projects/diaries" && docker compose --file compose.yaml --env-file .env ps'

echo '=== Fresh production PostgreSQL COPY SELECT, transaction read-only ==='
python3 "$feature/tools/step1_inventory.py" \
    --ssh-host pluto \
    --output "$current"

echo '=== Generate private v2 review, carrying v1 decisions as unapproved hints ==='
python3 "$feature/tools/step4_0051_compatibility_review.py" prepare \
    --proposals "$proposals" \
    --frozen "$frozen" \
    --prior-v1-draft "$prior" \
    --current-snapshot "$current/current-schema-snapshot.PRIVATE.csv" \
    --output "$review"

echo '=== Validate new private unapproved draft against the same read-only snapshot ==='
python3 "$feature/tools/step4_0051_compatibility_review.py" check \
    --proposals "$proposals" \
    --frozen "$frozen" \
    --prior-v1-draft "$prior" \
    --decisions "$review/0028-0051-review-v2.DRAFT.PRIVATE.json" \
    --current-snapshot "$current/current-schema-snapshot.PRIVATE.csv" \
    --output "$check"

python3 - "$current/0028-summary.json" \
          "$review/0028-0051-compatibility-summary.json" \
          "$check/0028-0051-v2-review-check.json" <<'PYREPORT'
import json,sys
inv,pre,chk=[json.load(open(p,encoding='utf-8')) for p in sys.argv[1:]]
print('=== Non-sensitive aggregate resumption results ===')
print('Inventory counts:',json.dumps(inv.get('counts',{}),sort_keys=True))
print('Historical v2 occurrence count:',pre['candidateOccurrences'])
print('Draft v2 blocked occurrences:',chk['rowsWithBlockers'])
print('Draft blocker categories:',json.dumps(chk['blockers'],sort_keys=True))
if chk['productionApplyAllowed'] or pre['productionApplyAllowed']:
    raise SystemExit('FAIL: Reviewer unexpectedly authorised production apply')
print('PASS: Read-only inventory and unapproved review created; Step 1 remains OPEN')
PYREPORT

printf 'Private evidence (do not commit/upload):\n %s\n %s\n %s\n' "$current" "$review" "$check"
