#!/usr/bin/env bash
# 0049 feature-specific formal closure: Windows Cygwin terminal, from Diaries parent checkout.
# User approval dated 2026-11-16. This script never operates on backup hosts.
set -euo pipefail
fail() { echo "0049 CLOSURE: FAIL — $*" >&2; exit 1; }
repo='/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
base='0049-FEAT - rationalise Btrfs and Diaries backup management'
source="change-control/in-progress/$base"
target="change-control/complete/$base"
baseline='34be53fe219dbe773b516596e3d36fa5b29801bb'
cd "$repo" || fail "Diaries parent checkout not found"
# Git for Windows and Cygwin can describe the same checkout using different path syntaxes.
# Since the script already cd's to the explicitly configured Windows checkout,
# use Git's repository-relative check rather than comparing absolute path strings.
[[ "$(git rev-parse --is-inside-work-tree)" == 'true' ]] || fail 'Not inside a Git worktree'
[[ -z "$(git rev-parse --show-prefix)" ]] || fail 'Wrong repository root (not at top level)'
[[ -e .git ]] || fail 'Git metadata missing at expected repository root'
[[ "$(git branch --show-current)" == 'main' ]] || fail 'Not on main'
[[ "$(git rev-parse HEAD)" == "$baseline" ]] || fail 'Unexpected Diaries commit; inspect before closure'
[[ "$(git remote get-url origin)" == 'git@github.com:rsmaxwell/diaries.git' ]] || fail 'Unexpected origin'
[[ -d "$source" && ! -e "$target" ]] || fail 'Expected source directory / absent destination not satisfied'
[[ -f "$source/reports/FORMAL-CLOSURE-DECISION-20261116.md" ]] || fail 'Approved closure decision absent'
[[ -f "$source/reports/REPOSITORY-REVISION-RECORD-20261116.md" ]] || fail 'Published revision record absent; apply final closure ZIP first'
[[ -f "$source/evidence/Step 4/WINDOWS-DIARIES-PUBLICATION-20261116.txt" ]] || fail 'Final Diaries publication log absent'
[[ -f "$source/reports/FINAL-TECHNICAL-ACCEPTANCE-20261116.md" ]] || fail 'Technical acceptance evidence absent'
[[ -f "$source/evidence/Step 4/MARS-FIRST-PUSH-ACCEPTANCE-20261116.txt" ]] || fail 'Live transfer acceptance log absent'
[[ -f "$source/evidence/Step 4/BACKUP-FINAL-READBACK-20261116.txt" ]] || fail 'Receiver readback log absent'
[[ -f "$source/evidence/Step 4/MANGO-FINAL-IDEMPOTENCE-20261116.txt" ]] || fail 'Idempotence log absent'
[[ -z "$(git diff --cached --name-only)" ]] || fail 'Already staged changes exist; do not overwrite index'
# Modified tracked files must be confined to the source feature. Submodule working-tree caches are out of scope.
while IFS= read -r path; do
  [[ -z "$path" || "$path" == "$source/"* ]] || fail "Unrelated tracked modification: $path"
done < <(git -c core.quotePath=false diff --name-only --ignore-submodules=untracked)
# Require that the source feature includes its original published history.
count_before="$(git ls-files -- "$source" | wc -l | tr -d ' ')"
[[ "$count_before" -ge 46 ]] || fail "Expected at least 46 published feature files, found $count_before"
echo "=== 0049 PRE-CLOSURE ==="
git status --short
echo "Published baseline: $baseline"
echo "Tracked source feature files: $count_before"
git fetch origin
[[ "$(git rev-parse origin/main)" == "$baseline" ]] || fail 'Remote main changed; inspect before closure'
mkdir -p change-control/complete
git mv -- "$source" "$target"
git add -A -- "$target"
[[ ! -e "$source" ]] || fail 'Old feature directory still exists'
# Check every previously committed original file still exists in complete/.
while IFS= read -r path; do
  [[ -z "$path" ]] && continue
  dest="$target/${path#"$source/"}"
  [[ -e "$dest" || -L "$dest" ]] || fail "Missing migrated file: $dest"
done < <(git ls-tree -r --name-only HEAD -- "$source")
while IFS= read -r path; do
  [[ -z "$path" || "$path" == "$source/"* || "$path" == "$target/"* ]] || fail "Unrelated staged file: $path"
done < <(git -c core.quotePath=false diff --cached --name-only)
[[ -n "$(git diff --cached --name-only)" ]] || fail 'No closure changes staged'
# Some verbatim terminal transcripts contain intentional shell/console whitespace.
# Validate the edited closure documents without mutating or normalising those raw logs.
git diff --cached --check --   "$target/README.md"   "$target/IMPLEMENTATION-STEPS.md"   "$target/tests/ACCEPTANCE-MATRIX.md"   "$target/evidence/README.md"   "$target/reports/FORMAL-CLOSURE-DECISION-20261116.md"
echo "=== 0049 STAGED CLOSURE ==="
git diff --cached --stat
git diff --cached --summary | tail -25
git commit -m '0049-FEAT: formally close and archive accepted feature'
echo '=== DIARIES CLOSURE COMMIT ==='
new_commit="$(git rev-parse HEAD)"
echo "0049 CLOSURE COMMIT: $new_commit"
[[ "$(git merge-base "$baseline" HEAD)" == "$baseline" ]] || fail 'Closure commit not descended from baseline'
git fetch origin
[[ "$(git rev-parse origin/main)" == "$baseline" ]] || fail 'Remote changed before publication'
git push origin main
published="$(git ls-remote origin refs/heads/main | awk '{print $1}')"
[[ "$published" == "$new_commit" ]] || fail "Published mismatch: $published"
echo "0049 CLOSURE PUBLISHED: $published"
echo '=== POST-CLOSURE STATUS ==='
git status --short
git submodule status
[[ -d "$target" && ! -e "$source" ]] || fail 'Relocation status inconsistent'
echo '0049 FORMAL CLOSURE: PASS'
