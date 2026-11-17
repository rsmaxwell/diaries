#!/usr/bin/env bash
# 0050-FEAT approved formal closure.
# Run from Windows Cygwin using: bash -c "$(cat "$script")"
# Read the script into memory before moving the directory containing it.
# This is a non-interactive Bash process; fail-fast flags are intentional.
set -euo pipefail
fail() { echo "0050 CLOSURE: FAIL — $*" >&2; exit 1; }
repo='/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
base='0050-FEAT - expose Diaries backup history on Btrfs receiver'
source="change-control/in-progress/$base"
target="change-control/complete/$base"
baseline='06ae009f2b840a9021045a9da3266d022ab6c65d'
cd "$repo" || fail 'Expected Windows Diaries checkout unavailable'
[[ "$(git rev-parse --is-inside-work-tree)" == true ]] || fail 'Not inside a Git checkout'
[[ -z "$(git rev-parse --show-prefix)" ]] || fail 'Must operate at Diaries Git checkout root'
[[ -z "$(git rev-parse --show-superproject-working-tree)" ]] || fail 'Unexpected nested submodule checkout'
[[ "$(git branch --show-current)" == main ]] || fail 'Not on main'
[[ "$(git rev-parse HEAD)" == "$baseline" ]] || fail 'Unexpected Diaries baseline; inspect before closure'
[[ "$(git remote get-url origin)" == 'git@github.com:rsmaxwell/diaries.git' ]] || fail 'Unexpected origin'
[[ -d "$source" && ! -e "$target" ]] || fail 'Source feature missing or complete/ destination already exists'
[[ -f "$source/reports/FORMAL-CLOSURE-DECISION-20261117.md" ]] || fail 'Formal owner approval document missing'
[[ -f "$source/reports/FINAL-OPERATIONAL-ACCEPTANCE-20261117.md" ]] || fail 'Final operational acceptance report missing'
[[ -f "$source/reports/FINAL-PUBLICATION-AND-REVISION-RECORD-20261117.md" ]] || fail 'Final repository revision record missing'
[[ -f "$source/evidence/Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt" ]] || fail 'Critical receiver-only acceptance transcript missing'
[[ -f "$source/evidence/Step 4/WINDOWS-DIARIES-PUBLICATION-20261117.txt" ]] || fail 'Published Diaries evidence transcript missing'
[[ -f "$source/tools/close-0050-feature.sh" ]] || fail 'Closure helper missing'
[[ -z "$(git diff --cached --name-only)" ]] || fail 'Unrelated staged changes already exist'
# Keep uncommitted tracked changes outside the feature untouched; refuse if any exist.
while IFS= read -r -d '' path; do
  [[ "$path" == "$source/"* ]] || fail "Tracked modification outside 0050: $path"
done < <(git diff --name-only -z --ignore-submodules=untracked)
# Guard the minimum published history count (new docs and evidence are not yet tracked).
count_before="$(git ls-files -z -- "$source" | tr -cd '\0' | wc -c | tr -d ' ')"
[[ "$count_before" -ge 33 ]] || fail "Expected at least 33 published feature files, found $count_before"
git fetch origin
[[ "$(git rev-parse origin/main)" == "$baseline" ]] || fail 'Remote main differs from expected published baseline'
[[ "$(git ls-remote origin refs/heads/main | awk '{print $1}')" == "$baseline" ]] || fail 'Remote readback differs from expected published baseline'
# Verify mandatory completed gates in the verbatim receipts.
grep -q '0050 ANSIBLE IDEMPOTENCE: PASS' "$source/evidence/Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt" || fail 'Idempotence PASS evidence missing'
grep -q 'Backups only on backup: 11' "$source/evidence/Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt" || fail 'Receiver-only evidence missing'
grep -q '0050 FINAL OPERATIONAL CHECK: PASS' "$source/evidence/Step 3/MANGO-STRICT-IDEMPOTENCE-AND-HISTORY-COMPARISON-20261117.txt" || fail 'Final operational PASS evidence missing'
grep -q "0050 DIARIES PUBLISHED: $baseline" "$source/evidence/Step 4/WINDOWS-DIARIES-PUBLICATION-20261117.txt" || fail 'Pre-closure Diaries publication evidence mismatched'
echo '=== 0050 PRE-CLOSURE ==='
echo "Published Diaries baseline: $baseline"
echo "Tracked historical files: $count_before"
git status --short
git submodule status
mkdir -p change-control/complete
# Script must have been loaded into memory before this git mv to avoid Windows file lock.
git mv -- "$source" "$target"
git add -A -- "$target"
[[ -d "$target" && ! -e "$source" ]] || fail 'Feature relocation incomplete'
# Require every previously published source feature file at the new path.
while IFS= read -r -d '' path; do
  dest="$target/${path#"$source/"}"
  [[ -e "$dest" || -L "$dest" ]] || fail "Published file missing after migration: $dest"
done < <(git ls-tree -rz --name-only HEAD -- "$source")
# Ensure staged changes concern this feature ONLY, not unrelated work.
while IFS= read -r -d '' path; do
  [[ "$path" == "$source/"* || "$path" == "$target/"* ]] || fail "Unrelated staged path: $path"
done < <(git diff --cached --name-only -z)
[[ -n "$(git diff --cached --name-only)" ]] || fail 'No relocation changes staged'
# Raw captured terminal logs may contain intentional whitespace; check edited Markdown only.
git diff --cached --check -- \
  "$target/README.md" \
  "$target/IMPLEMENTATION-STEPS.md" \
  "$target/evidence/README.md" \
  "$target/tests/ACCEPTANCE-MATRIX.md" \
  "$target/reports/FORMAL-CLOSURE-DECISION-20261117.md" \
  "$target/reports/FINAL-PUBLICATION-AND-REVISION-RECORD-20261117.md"
echo '=== 0050 STAGED CLOSURE ==='
git diff --cached --stat
git diff --cached --summary | tail -20
git commit -m '0050-FEAT: formally close receiver Diaries history feature'
closure_sha="$(git rev-parse HEAD)"
echo "0050 CLOSURE COMMIT: $closure_sha"
[[ "$(git merge-base "$baseline" HEAD)" == "$baseline" ]] || fail 'Closure commit is not descendant of approved baseline'
git fetch origin
[[ "$(git rev-parse origin/main)" == "$baseline" ]] || fail 'Remote main moved before closure push'
git push origin main
published="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$published" == "$closure_sha" ]] || fail "Published closure mismatch: $published"
echo "0050 CLOSURE PUBLISHED: $published"
echo '=== FINAL REPOSITORY STATUS ==='
git status --short
git submodule status
[[ -d "$target" && ! -e "$source" ]] || fail 'Post-publication archive location inconsistent'
git diff --quiet --ignore-submodules=untracked || fail 'Unexpected tracked modifications after commit'
git diff --cached --quiet || fail 'Unexpected staged changes after commit'
echo '0050 FORMAL CLOSURE: PASS'
