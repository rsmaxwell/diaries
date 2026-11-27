#!/usr/bin/env bash
# 0054 formal closure, approved 27 Nov 2026. Run with bash from Diaries parent repository root.
# Compatible with Cygwin GNU Bash 5.2. Does not alter interactive shell options.
set -euo pipefail

FEATURE='0054-FEAT - align annual PREAMBLE POSTAMBLE Quill editing with DATED fragments'
OLD="change-control/in-progress/$FEATURE"
NEW="change-control/complete/$FEATURE"
EXPECTED_PARENT='84921a2'
EXPECTED_CLIENT='aa6493557771f3d58c67db2842f9ff5978fe48d2'
EXPECTED_WEB='18b18c2c090e78fd3c3ae102df869527c5e4aa58'
EXPECTED_RESPONDER='a49c6abd0ce005d58eb516770f6515313e40cdf6'

fail() { printf 'FAIL: %s\n' "$*" >&2; exit 1; }
[ -f .gitmodules ] || fail 'Run from the Diaries parent repository root.'
[ "$(git branch --show-current)" = main ] || fail 'Parent must be on main.'
[ "$(git rev-parse --short=7 HEAD)" = "$EXPECTED_PARENT" ] || fail 'Unexpected parent HEAD; inspect before closure.'
[ -d "$OLD" ] || fail "Feature missing: $OLD"
[ ! -e "$NEW" ] || fail "Destination already exists: $NEW"
[ -f "$OLD/IMPLEMENTATION-STEPS.md" ] || fail 'Missing implementation steps.'
[ -f "$OLD/README.md" ] || fail 'Missing feature README.'
[ -f "$OLD/reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md" ] || fail 'Apply the supplied final review reports first.'
[ -f "$OLD/reports/0054-RELEASE-AND-CLOSURE-CHECKLIST.md" ] || fail 'Apply the supplied closure checklist first.'
[ "$(git -C diaries-client rev-parse HEAD)" = "$EXPECTED_CLIENT" ] || fail 'Client revision mismatch.'
[ "$(git -C diaries-web rev-parse HEAD)" = "$EXPECTED_WEB" ] || fail 'Reader revision mismatch.'
[ "$(git -C diaries-responder rev-parse HEAD)" = "$EXPECTED_RESPONDER" ] || fail 'Responder revision mismatch.'
[ -z "$(git diff --cached --name-only)" ] || fail 'Parent has staged changes; preserve/review those first.'
for module in diaries-client diaries-web diaries-responder; do
  [ -z "$(git -C "$module" status --porcelain)" ] || fail "$module has uncommitted changes."
done
# A git-tracked change outside the feature would invalidate this release closure baseline.
if git diff --name-only | grep -v -F "${OLD}/" | grep -q .; then
  fail 'Unstaged tracked changes exist outside 0054; inspect before closure.'
fi

mkdir -p change-control/complete
mv -- "$OLD" "$NEW"

# Update only feature status statements, preserving all historical reports/logs.
sed -i 's/\*\*Status:\*\* IN PROGRESS — opened 26 November 2026/**Status:** CLOSED — 27 November 2026 (owner approved)/' "$NEW/README.md"
sed -i 's/\*\*Status:\*\* IN PROGRESS — 26 November 2026/**Status:** CLOSED — 27 November 2026 (owner approved)/' "$NEW/IMPLEMENTATION-STEPS.md"
sed -i 's/## Step 2 — Implement annual Quill parity (IMPLEMENTED — validation pending)/## Step 2 — Implement annual Quill parity (CLOSED)/' "$NEW/IMPLEMENTATION-STEPS.md"
sed -i 's/## Step 3 — Consolidated verification and release (OPEN)/## Step 3 — Consolidated verification and release (CLOSED)/' "$NEW/IMPLEMENTATION-STEPS.md"
sed -i 's/\*\*Status: OPEN pending explicit formal closure approval\.\*\*/**Status: CLOSED — 27 November 2026; owner approved formal closure.**/' "$NEW/reports/0054-RELEASE-AND-CLOSURE-CHECKLIST.md"
sed -i 's/- \[ \] Owner explicitly approves \*\*formal feature closure\*\*\./- [x] Owner explicitly approved **formal feature closure** on 27 November 2026./' "$NEW/reports/0054-RELEASE-AND-CLOSURE-CHECKLIST.md"
sed -i 's/- \[ \] Mark final gate CLOSED and move the entire feature directory from `in-progress\/` to `complete\/`; commit\/push closure update and preserve evidence\./- [x] Final gate CLOSED; entire feature directory moved to `complete\/`, with historical evidence preserved. Closure commit\/push tracked separately./' "$NEW/reports/0054-RELEASE-AND-CLOSURE-CHECKLIST.md"
sed -i 's/\*\*Status:\*\* IN PROGRESS — all four production browser checks owner-accepted; \*\*formal feature closure not yet authorised\*\*\./**Status:** CLOSED — formal closure approved by owner on 27 November 2026./' "$NEW/reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md"
sed -i 's/- \[ \] \*\*Owner explicitly authorises formal closure of 0054-FEAT\.\*\*/- [x] **Owner explicitly authorised formal closure of 0054-FEAT on 27 November 2026.**/' "$NEW/reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md"
sed -i 's/- \[ \] Update `IMPLEMENTATION-STEPS.md` and feature status to CLOSED, move full directory to `change-control\/complete\/`, and commit\/push the parent repository closure change\. Preserve historical evidence and rollback references\./- [x] Status and steps marked CLOSED; feature moved to `change-control\/complete\/`, preserving evidence and rollback references. Closure commit\/push is a separate Git operation./' "$NEW/reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md"
sed -i 's/\*\*This report deliberately does not declare formal closure or claim that the feature directory has moved\.\*\*/**Closure approved and directory moved on 27 November 2026.**/' "$NEW/reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md"
cat >> "$NEW/IMPLEMENTATION-STEPS.md" <<'EOF'

## Final acceptance and closure — 27 November 2026

Step 2 and Step 3 are CLOSED. Final Angular regression/build checks passed;
Reader regression/build checks passed; all four production browser smoke tests
were accepted by the owner. Production Client `0.0.9-build-82`, Reader
`0.0.9-build-11` and unchanged Responder `0.0.9-build-87` were healthy on
`pluto`. The owner explicitly approved formal feature closure on 27 November
2026. See `reports/0054-PRODUCTION-ACCEPTANCE-AND-CLOSURE-REVIEW.md` for
release/rollback evidence and the deferred cross-diary design consideration.

The implementation note dated 26 November above is historical and does not
supersede these final acceptance results.
EOF
cat >> "$NEW/README.md" <<'EOF'

## Formal closure — 27 November 2026

All acceptance gates are CLOSED following explicit owner approval. Production
Client `0.0.9-build-82`, Reader `0.0.9-build-11` and unchanged Responder
`0.0.9-build-87` were verified healthy. See the production acceptance report
for source revisions, smoke testing and rollback instructions. The separate
cross-diary annual-content design consideration remains deferred.
EOF
cat > "$NEW/reports/0054-FORMAL-CLOSURE-RECORD.md" <<'EOF'
# 0054-FEAT — Formal closure record

**Decision:** CLOSED, expressly approved by the owner on 27 November 2026.

## Accepted result

- Final Angular automated tests and build: PASS.
- Reader formatting/security tests and distribution build: PASS.
- Development browser editing/formatting/clipboard/navigation: PASS.
- GitHub source publication: Client `aa64935`, Reader `18b18c2`, parent release baseline `84921a2`.
- Ansible production deployment: exit 0, recap `ok=51 changed=3 failed=0 unreachable=0`.
- Production images healthy: Client `0.0.9-build-82`, Reader `0.0.9-build-11`, unchanged Responder `0.0.9-build-87`.
- Four owner-performed production browser smoke checks: PASS.

## Rollback

Previously running images: Client `0.0.9-build-81`, Reader `0.0.9-build-10`;
Responder remains `0.0.9-build-87`. Restore the former two tags through the
normal `mango` Playbooks procedure, preserving unrelated local changes, then
recheck container health and browser functionality. No schema migration occurred.

## Deferred question

The PREAMBLE/POSTAMBLE assignment across multiple physical diaries remains a
future design consideration, not a defect or closure blocker. See the deferred
design report under this feature directory.

## Evidence

All original reports, scripts and raw test evidence were retained when moving
the feature from `in-progress` to `complete`. The closure Git commit and push
are to be verified from the subsequent terminal output.
EOF

git add -A -- "$NEW"
# Remove only old 0054 paths from the index; do not stage other features.
git ls-files -z -- "$OLD" | xargs -0 -r git rm --cached --quiet --
# Confirm no unrelated paths entered the index.
if git diff --cached --name-only | grep -v -F -e "${OLD}/" -e "${NEW}/" | grep -q .; then
  fail 'Unexpected staged path outside 0054.'
fi
git -c core.whitespace=-blank-at-eol,-blank-at-eof diff --cached --check || fail 'Staged validation failed.'
printf '\n=== Closure staged summary ===\n'
git diff --cached --stat
printf '\n=== Closure changes (renames may be condensed) ===\n'
git status --short

git commit -m '0054-FEAT: formally close accepted Quill editor feature'
printf '\nPASS: closure committed locally; push remains to be performed.\n'
git log -1 --format='%H %s'
git status --short --branch
