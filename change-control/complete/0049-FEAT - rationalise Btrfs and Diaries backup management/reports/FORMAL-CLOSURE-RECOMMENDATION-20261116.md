# 0049 — Formal closure recommendation (16 November 2026)

**Proposed decision: APPROVE FEATURE CLOSURE.** **Decision state: PENDING OPERATOR APPROVAL — NOT CLOSED.**

The recorded evidence supports acceptance of 0049's implemented management interface and historical command/unit migration. Source regression and negative tests passed, receiver-first/sender deployments succeeded, a live incremental push completed through dedicated 0041 identity, on-disk received UUID and read-only state were checked independently, old timers were removed, the receiver retention preview proposed no deletions, historical holds/receipts were preserved, and Ansible reapply was strictly idempotent on both endpoints. All three Git repositories are now published with exact SHA verification and the intended controller Playbooks pointer.

## Accepted limitations and out-of-scope follow-up

- No production prune, destructive rollback or restore test was performed (none is justified for this naming/reporting change).
- The `last verified transfer` field correctly remains unknown without independent receipt evidence. This does not invalidate the proven receive/read-back and agreed-parent verification.
- Two stale sender qgroups observed with qgroups_status `ok` belong to **0039-DEF**. The receiver had no stale qgroups in final read-back.
- Internal `.simple-*` persistent state filenames deliberately remain unchanged; relabelling recovery state would introduce needless risk.
- The implementation has no change to retained datasets, retention buckets, 0041 keys or privilege model, or original service schedules.

## Proposed formal acceptance and final controlled operation

Operator approval should explicitly accept the 0049 technical result, source/manifests, published revision record, rollback readiness (not a live rollback), and known limitations above. Only **after approval**:

1. In the authoritative **Windows Diaries** repo, review current `main`, status and 0049 directory.
2. Update the living README, implementation-steps summary and acceptance matrix to mark relevant steps **CLOSED**, and record the operator acceptance and date in a formal closure document under the feature.
3. Move the whole feature directory from `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/` to the same name under `change-control/complete/`, preserving every historical report and raw log.
4. Stage **only** the feature's moved paths, verify a Git rename/move with complete evidence, commit the closure and push Diaries `main` (no Playbooks or Ansible-controller change), then verify the published SHA.

This report is a recommendation, not the approval itself. No repository move or CLOSED status is claimed here.
