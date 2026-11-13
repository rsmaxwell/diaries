#!/usr/bin/env bash
# 0048 formal closure: run from Windows Cygwin at the Diaries repository root.
# Only invoke with --accept-and-publish after reviewing the acceptance report.
set -euo pipefail
if [[ "${1:-}" != --accept-and-publish || $# -ne 1 ]]; then
  echo 'Usage: bash finalise-0048-closure.sh --accept-and-publish' >&2
  exit 2
fi
feature='0048-FEAT - evaluate backup collection permissions and simplify tooling'
source_dir="change-control/in-progress/$feature"
target_dir="change-control/complete/$feature"
[[ -d "$source_dir" && ! -e "$target_dir" ]] || { echo 'FAIL: feature source absent or already completed' >&2; exit 1; }
[[ -f .gitmodules ]] || { echo 'FAIL: run from Diaries Git repository root' >&2; exit 1; }
[[ "$(git branch --show-current)" == main ]] || { echo 'FAIL: Diaries not on main' >&2; exit 1; }
[[ -z "$(git diff --cached --name-only)" ]] || { echo 'FAIL: unrelated staged changes present' >&2; exit 1; }
[[ -f "$source_dir/reports/STEP4-LIVE-ACCEPTANCE-20261113.md" ]] || exit 1
[[ -f "$source_dir/reports/0048-FEAT-CLOSURE-REVIEW-20261113.md" ]] || exit 1
[[ -f "$source_dir/tests/ACCEPTANCE-MATRIX.md" ]] || exit 1
[[ -d 'change-control/complete/0046-FEAT - move non-sensitive Ansible inventory into Playbooks Git' ]] || exit 1
[[ -d 'change-control/complete/0047-FEAT - retire legacy backup entry points and align collection role' ]] || exit 1
shopt -s nullglob
publications=("$source_dir"/evidence/Step\ 3/publication-*.txt)
deployments=("$source_dir"/evidence/Step\ 4/deployment-*.txt)
health_reports=("$source_dir"/evidence/Step\ 4/final-backup-health-*.txt)
[[ ${#publications[@]} -gt 0 && ${#deployments[@]} -gt 0 && ${#health_reports[@]} -gt 0 ]] || {
  echo 'FAIL: required Step 3/4 terminal evidence logs absent' >&2
  exit 1
}
grep -lq 'PASS: 0048 Playbooks and parent pin published' "${publications[@]}" || { echo 'FAIL: publication PASS receipt missing' >&2; exit 1; }
grep -lq 'PASS: 0048 targeted mars deployment, repeat idempotence and installed verification' "${deployments[@]}" || { echo 'FAIL: full live deployment PASS receipt missing' >&2; exit 1; }
# The health report is captured by tee around the remote command only.
# The Windows wrapper's final PASS message is printed after tee completes,
# so it is correctly absent from the saved evidence file. Validate the
# substantive, same-file health results instead of that wrapper message.
health_valid=false
for health_report in "${health_reports[@]}"; do
  if grep -Fq 'DIARIES BACKUP STATUS (read-only)' "$health_report" \
    && grep -Fq 'qgroups_status=ok' "$health_report" \
    && grep -Fq 'diaries_verification=valid' "$health_report" \
    && grep -Eq '(^|;)incomplete_timestamp_sets=0([;[:space:]]|$)' "$health_report" \
    && grep -Fq 'LAST VERIFIED PULL (CURRENT RECEIVING MARKER)' "$health_report" \
    && grep -Fq 'LAST ACCEPTED OFF-SITE REPLICATION' "$health_report" \
    && grep -Fq 'NEXT SIMPLIFIED PUSH PREFLIGHT (READ-ONLY)' "$health_report"; then
    health_valid=true
    break
  fi
done
[[ "$health_valid" == true ]] || {
  echo 'FAIL: required backup-health results missing from a single evidence report' >&2
  exit 1
}
echo 'PASS: saved backup-health evidence verified (wrapper PASS message not required)'

echo '=== Review Git state and upstream before accepting closure ==='
git status --short
git fetch origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo 'FAIL: Diaries main diverged from origin/main' >&2; exit 1; }
git diff --check -- "$source_dir"

echo '=== Stage only 0048 and move full feature to completed change control ==='
git add -- "$source_dir"
git mv -- "$source_dir" "$target_dir"
# Update disposition only on formal acceptance; proposed package leaves it pending.
sed -i 's/READY FOR FORMAL CLOSURE — implementation deployed and technically verified 13 November 2026; closure publication pending/CLOSED — formally accepted 13 November 2026; published in the Diaries closure commit/' "$target_dir/README.md"
sed -i 's/READY FOR FORMAL CLOSURE — Steps 1–4 technical acceptance evidence reviewed 13 November 2026. Repository relocation and Diaries closure publication have not yet been performed./CLOSED — Steps 1–4 technically accepted; moved to completed change control and included in the Diaries closure commit./' "$target_dir/IMPLEMENTATION-STEPS.md"
sed -i 's/READY FOR OPERATOR ACCEPTANCE; NOT YET CLOSED OR PUBLISHED in the Diaries repository./CLOSED — operator formally accepted; publication receipt is the Diaries closure commit./' "$target_dir/reports/0048-FEAT-CLOSURE-REVIEW-20261113.md"
sed -i 's/Technical acceptance PASS. Formal feature closure and Diaries publication remain pending operator acceptance./Technical acceptance PASS. Operator closure accepted; this record is included in the Diaries closure commit./' "$target_dir/tests/ACCEPTANCE-MATRIX.md"
sed -i 's/| CLOSE | Operator accepts record, feature moved to `complete\/`, closure commit pushed | PENDING |/| CLOSE | Operator accepts record, feature moved to `complete\/`, closure commit pushed | ACCEPTED (publication subject to successful push) |/' "$target_dir/tests/ACCEPTANCE-MATRIX.md"
sed -i 's/Closure remains pending operator review and a published Diaries change-control commit; do not treat/Closure was accepted by the operator in the Diaries closeout command; do not treat/' "$target_dir/README.md"
sed -i 's/this proposed package as proof that publication has occurred./the earlier proposed package alone as the publication receipt; use the closure Git commit./' "$target_dir/README.md"
sed -i 's/\*\*Formal closure remains pending:\*\*/**Formal closure accepted:**/' "$target_dir/IMPLEMENTATION-STEPS.md"
sed -i 's/operator acceptance of `reports\/0048-FEAT-CLOSURE-REVIEW-20261113.md`, movement of the full feature (including logs) from `in-progress` to `complete`, and the publication of the corresponding Windows Diaries commit./operator acceptance of `reports\/0048-FEAT-CLOSURE-REVIEW-20261113.md`, movement of the full feature to `complete`, and the corresponding Windows Diaries closure commit./' "$target_dir/IMPLEMENTATION-STEPS.md"
sed -i 's/Diaries closure commit PENDING/Diaries closure commit included in this publication/' "$target_dir/tests/ACCEPTANCE-MATRIX.md"
sed -i 's/Live deployment and operational verification PASS; formal feature closure requires a final Diaries commit and operator acceptance./Live deployment and operational verification PASS; operator accepted feature closure in the Diaries publication command./' "$target_dir/reports/STEP4-LIVE-ACCEPTANCE-20261113.md"
sed -i 's/\*\*Formal 0048 closure is not yet claimed.\*\*/**Formal 0048 closure accepted by operator.**/' "$target_dir/reports/STEP4-LIVE-ACCEPTANCE-20261113.md"
git add -A -- "$target_dir"

unexpected=$(git diff --cached --name-only | awk -v from="$source_dir/" -v to="$target_dir/" 'index($0,from)!=1 && index($0,to)!=1 {print}')
[[ -z "$unexpected" ]] || { printf 'FAIL: unrelated staged files:\n%s\n' "$unexpected" >&2; exit 1; }
git diff --cached --check
git diff --cached --stat

echo '=== Commit and publish accepted 0048 closure ==='
git commit -m '0048-FEAT: close Git-native backup collection permission simplification'
git push origin main
[[ "$(git rev-parse HEAD)" == "$(git rev-parse origin/main)" ]] || { echo 'FAIL: closure push not reflected in origin/main' >&2; exit 1; }
echo "CLOSURE_DIARIES=$(git rev-parse HEAD)"
echo 'PASS: 0048 formally closed and published in Diaries main'
