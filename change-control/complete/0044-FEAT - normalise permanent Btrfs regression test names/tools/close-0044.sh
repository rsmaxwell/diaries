#!/usr/bin/env bash
# One-off 0044 source-only change-control closure, run via bash from Windows Cygwin.
# This is a standalone non-interactive Bash process; fail-fast does not alter the calling shell.
set -euo pipefail

expected_diaries_head='293a755248982ce7a5db28ca35854310eb0d7235'
expected_playbooks_head='7dfa93fef6d975aa82f5f4cfdf54497b106e7645'
feature='0044-FEAT - normalise permanent Btrfs regression test names'
src="change-control/in-progress/$feature"
dst="change-control/complete/$feature"

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }

repo=$(git rev-parse --show-toplevel) || fail 'Cannot locate Diaries Git checkout'
# Git for Windows can return C:/... even when invoked from Cygwin.
# Normalise before performing the strict checkout check and cd.
if command -v cygpath >/dev/null 2>&1; then
    repo=$(cygpath -u "$repo") || fail 'Cannot convert Git checkout path to Cygwin form'
fi
[[ "$repo" == '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries' ]] || fail "Unexpected checkout: $repo"
cd "$repo"
[[ "$(git branch --show-current)" == main ]] || fail 'Diaries must be on main'
[[ "$(git rev-parse HEAD)" == "$expected_diaries_head" ]] || fail 'Diaries HEAD changed; review new commits before closure'
[[ -z "$(git diff --cached --name-only)" ]] || fail 'Pre-existing staged changes; preserve and review first'
[[ -d "$src" && ! -e "$dst" ]] || fail 'Feature source missing or complete destination already exists'

for required in \
  'README.md' \
  'reports/FINAL-ACCEPTANCE-RECONCILIATION-20261110.md' \
  'evidence/Step 2/rename-and-regressions-20261110-143920.txt' \
  'evidence/Step 3/playbooks-source-commit-20261110.txt' \
  'evidence/Step 4/consolidation-and-commit-20261110.txt' \
  'evidence/Step 5/cutover-retirement-and-commit-20261110-150334.txt' \
  'evidence/Step 6/final-naming-and-regressions-20261110-152328.txt' \
  'tests/historical-verify-legacy-retirement-source.py' \
  'tests/historical-verify-simplified-cutover-readiness.py'; do
  [[ -f "$src/$required" ]] || fail "Missing required acceptance file: $required"
done

grep -Fq 'PASS: 0044 permanent regression naming complete' "$src/evidence/Step 6/final-naming-and-regressions-20261110-152328.txt" || fail 'Final regression PASS missing'
grep -Fq "$expected_playbooks_head" "$src/evidence/Step 6/final-naming-and-regressions-20261110-152328.txt" || fail 'Final commit missing from acceptance transcript'

# Verify committed Playbooks files and publication, without editing the Playbooks checkout.
# Failure output deliberately remains visible in the caller.
echo '=== Verify published Playbooks commit on mango ==='
ssh mango "
  cd /home/richard/playbooks || exit 1
  test \"\$(git branch --show-current)\" = main || exit 1
  test \"\$(git rev-parse HEAD)\" = '$expected_playbooks_head' || exit 1
  test \"\$(git rev-parse origin/main)\" = '$expected_playbooks_head' || exit 1
  test -z \"\$(git status --porcelain)\" || exit 1
  git status --short --branch
  git log -4 --format='%H %s'
" || fail 'Playbooks publication or cleanliness verification failed'

mkdir -p "$src/evidence/Step 7"
ssh mango "
  cd /home/richard/playbooks || exit 1
  test \"\$(git rev-parse HEAD)\" = '$expected_playbooks_head' || exit 1
  test \"\$(git rev-parse origin/main)\" = '$expected_playbooks_head' || exit 1
  git status --short --branch
  git log -4 --format='%H %s'
" > "$src/evidence/Step 7/playbooks-publication-20261110.txt" || fail 'Could not capture Playbooks publication receipt'

# Update exact strings once, before moving. No broad search-and-replace.
old_state='**State:** READY FOR CLOSURE — final Playbooks source verification and regression acceptance PASS; GitHub publication and formal change-control closure pending. 10 November 2026.'
new_state='**State:** CLOSED — accepted 10 November 2026; published Playbooks source and final regression evidence verified.'
old_report='**State:** READY FOR CLOSURE — accepted source-only regressions; source-control publication pending.'
new_report='**State:** CLOSED — implementation and Playbooks source publication accepted; feature moved to change-control/complete/.'

python3 - "$src/README.md" "$src/reports/FINAL-ACCEPTANCE-RECONCILIATION-20261110.md" "$old_state" "$new_state" "$old_report" "$new_report" <<'PY_CLOSE'
from pathlib import Path
import sys
readme, report, old1, new1, old2, new2 = sys.argv[1:]
for name, old, new in ((readme, old1, new1), (report, old2, new2)):
    path = Path(name)
    data = path.read_text(encoding='utf-8')
    if data.count(old) != 1:
        raise SystemExit(f'FAIL: expected exactly one closure state in {name}')
    data = data.replace(old, new)
    if name == readme:
        marker = '## Final steps\n'
        replacement = '## Formal closure\n\nPublished Playbooks commit `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` was verified against `origin/main` on `mango`. Publication receipt: `evidence/Step 7/playbooks-publication-20261110.txt`. All 0044 evidence was accepted and the entire feature directory moved to `change-control/complete/`. The resulting Diaries commit must be published separately.\n'
        if data.count(marker) != 1:
            raise SystemExit(f'FAIL: expected final steps marker in {name}')
        data = data[:data.index(marker)] + replacement
    else:
        marker = '**Pending:** Playbooks push and remote readback; feature move to `change-control/complete/` with this report marked CLOSED; Diaries commit and push. The closure script verifies those prerequisites and records publication evidence in `evidence/Step 7/` before moving the directory. Final Diaries publication is verified separately.'
        replacement = '**Accepted closure:** Playbooks `main` and `origin/main` matched commit `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` and had a clean working tree. Publication receipt is held in `evidence/Step 7/playbooks-publication-20261110.txt`. Feature moved to `change-control/complete/`; the local Diaries closure commit is ready for publication.'
        if data.count(marker) != 1:
            raise SystemExit(f'FAIL: expected pending gate in {name}')
        data = data.replace(marker, replacement)
    path.write_text(data, encoding='utf-8')
PY_CLOSE

# Leave the historical narrative intact; current state and receipt supersede prior pending text.
echo '=== Move feature to complete and stage ONLY 0044 ==='
mkdir -p 'change-control/complete'
mv -- "$src" "$dst"
git add -A -- "$dst"

unexpected=$(git diff --cached --name-only | grep -Fv "$dst/" || true)
[[ -z "$unexpected" ]] || fail "Unexpected staged files:\n$unexpected"
[[ -n "$(git diff --cached --name-only)" ]] || fail 'No 0044 evidence staged'
git diff --cached --check -- "$dst/README.md" "$dst/reports" "$dst/tools"
git diff --cached --stat

echo '=== Commit formal 0044 closure ==='
git commit -m '0044-FEAT: close permanent Btrfs regression consolidation'
git log -1 --format=fuller
git status --short --branch
printf 'PASS: 0044 formally closed in local Diaries Git; publish Diaries main next\n'
