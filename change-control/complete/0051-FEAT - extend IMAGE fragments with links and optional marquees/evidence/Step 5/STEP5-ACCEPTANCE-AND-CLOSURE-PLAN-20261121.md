# 0051 Step 5 — final acceptance and closure plan

**Prepared:** 21 November 2026. **Current state:** documents ready for review; Step 5 OPEN, 0051 remains `in-progress`.

## Objective and gate

Step 5 in `IMPLEMENTATION-STEPS.md` requires accepted capability; exact build/revision and deployment evidence; updated permanent architecture/component docs; assurance that 0029 will not re-prohibit IMAGE Marquees; tooling classification; explicit 0028 resumption handoff; and formal owner closure. This is not a licence to alter production content or legacy data.

## Final acceptance matrix

| Criterion | Current evidence | Remaining Step 5 action |
| --- | --- | --- |
| IMAGE supports absent/present external link and source Marquee in all four combinations | Step 3 integrated tests, protected Step 4 published rehearsal and owner's 21 Nov production functional PASS statement | Obtain owner signoff to Step 4 review; retain existing run receipts |
| Safe HTTP(S) destinations, omitted/set/clear and lock/version controls | Step 2 responder contract/integration, Step 3 client/web suites, Step 4 isolated rollback | Record accepted behavioural boundary in permanent docs |
| Existing MARQUEE, legacy inline HTML, missing catalogue and Image ID/day-order behaviour | Client 244/244 tests; local and production IMAGE rendering verified; no reported regressions | Confirm historical exceptions remain documented; leave 0028 migration out of this closure |
| DB/MQTT/Files persistence and restart/replay | Protected rehearsal PASS and successful production startup, schema and health readback | Preserve private receipts and describe limits: no new full production restore was run |
| Production deployment and activation | `build-79 / build-85 / build-9`; Ansible production gate activation PASS; owner functional checks PASS | Inventory release refs and retain production activation log |
| Rollback and operational safety | Rehearsed **old binaries only before first extension write**; backups healthy by manifest identity | Explicitly document post-write gate-off and compatible forward-fix; don't promise old-image rollback |
| 0028 migration compatibility | Read-only source inventory and PRIVATE_UNAPPROVED_V2 reviewer exists; no production migration | Hand off v2 contract, require fresh snapshots/decisions and 0028 gates |
| 0029 planned invariants | Supplied 0029 TODO README accepts optional IMAGE Marquee and links | Re-verify current uncommitted 0029 file before future destructive cleanup; no migration in 0051 |
| Documentation | Updated parent `ARCHITECTURE.md`, `docs/IMAGE-FRAGMENT-AUTHORING.md`, plus client/responder/web README files in this package | Review against later Windows local changes; commit component docs in their independent submodule repositories before updating parent pins |
| Code/tool classification | Feature-specific scripts and tests under 0051; 0028 reviewer remains under 0028 | Confirm no ad-hoc deployed helpers, retain historical receipts; avoid deleting evidence or permanent regression scripts |
| Source control & formal closure | Client and parent feature commits pushed; Playbooks still dirty in last observed log | Record fresh parent/submodule/Playbooks status, commit only approved relevant files, explicitly approve closure, **then** move directory to `complete` |

## Work sequence — one consolidated closure operation

1. **Review/accept Step 4**: verify `STEP4-PRODUCTION-ACCEPTANCE-REVIEW-20261121.md` against existing evidence and owner-confirmed browser functional tests. Obtain explicit decision to mark **Step 4 CLOSED**; author a dated receipt at that point (not beforehand).
2. **Reconcile permanent documents**: compare the updated `docs/IMAGE-FRAGMENT-AUTHORING.md` and `ARCHITECTURE.md` and each component README from this ZIP against current Windows working copies. Verify no overwriting of later local edits and correct old `IMAGE => no Marquee` descriptions. Each modified component README must be committed/pushed within its own Git submodule, then the parent pin updated; do not stage unrelated work.
3. **Check evidence and tools**: run the read-only Git/evidence inventory below. Keep historical test harnesses and receipts within the feature. Review whether any one-off helpers were mistakenly installed into permanent Playbooks roles; none is claimed removed by this plan.
4. **0028/0029 handoff**: accept `STEP5-0028-0029-HANDOFF-20261121.md` while preserving 0028 v1 decisions as historical, v2 as private unapproved drafts and 0029 as TODO; identify all separate future approval gates.
5. **Formal 0051 closure decision**: only upon explicit owner approval after checking the complete evidence set, update feature README and steps status, record final revisions and owner decision, commit approved changes, and move 0051 from `change-control/in-progress` to `change-control/complete`. Do not change production DB, NAS Files, Docker, or 0028 states in this step.

## Read-only working-tree/evidence preflight

**Windows Cygwin terminal** (paste from the actual Windows repository, not from extracted ZIPs):

```bash
repo=/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
if (
    set -euo pipefail
    cd "$repo"
    printf '=== parent ===\n'
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
for submodule in diaries-client diaries-responder diaries-web; do
    printf '=== %s ===\n' "$submodule"
    git -C "$submodule" branch --show-current
    git -C "$submodule" rev-parse HEAD
    git -C "$submodule" status --short
done
printf '=== 0051 step4/step5 reports ===\n'
find 'change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/evidence' -maxdepth 3 -type f -name '*.md' -print
); then
    echo 'PASS: Read-only working-tree/evidence inventory'
else
    echo 'FAIL: Read-only working-tree/evidence inventory'
fi
```

**Windows Cygwin terminal — read-only `mango` Playbooks revision/status**:

```bash
ssh mango 'cd /home/richard/ansible-controller/playbooks && git branch --show-current && git rev-parse HEAD && git status --short'
```

Do not automatically stage or push all uncommitted parent/Playbooks changes: 0028, 0029 and 0051 work coexist in the same working trees.

## Owner decisions required

- [ ] Formal Step 4 acceptance and closure, referencing the production review.
- [ ] Acceptance of final permanent documentation / 0028 and 0029 handoff.
- [ ] Formal Step 5 and 0051 feature closure, following evidence/revision inventory.
- [ ] Separate future approval, within **0028**, to resume its own reviewed migration and eventually apply it; **no approval implied here**.

## Outstanding independent work

- 0052 Whitley Park image content correction is a separately filed/requested TODO defect, not a media renderer failure and not part of 0051 deployment.
- Production npm audit findings (55 packages/security findings reported in Jenkins including 2 critical and 35 high) should be handled in a separate dependency/security backlog rather than silently declared resolved by 0051.
- The long mobile diary title clipping noted during accepted Step 3 remains a non-blocking presentation observation.
