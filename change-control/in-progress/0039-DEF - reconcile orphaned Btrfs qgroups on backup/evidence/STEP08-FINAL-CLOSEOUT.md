# 0039-DEF — Step 8 final closeout and residual-risk acceptance

**Prepared:** 2026-10-22. **Scope:** documentation and controlled repository relocation only. **Status:** acceptance prepared; final administrative closure conditional on operator's Git review, relocation and commit.

## Accepted outcomes

- Step 1 inventory and Step 2 diagnosis/source deployment are CLOSED, with source and original logs preserved under `evidence/Step 01/` and `evidence/Step 02/`.
- Step 3 guarded `backup` qgroup removal: 29,437 targeted unmatched level-0 qgroups removed. The interrupted 675-deletion journal remains an explicitly recorded FAIL and was separately reconciled; do not hide this exception. Independent post-remediation checks, including successful incremental `mars` → `backup` replication, read-only state, received UUIDs and receipts, recorded zero unmatched qgroups. See `evidence/Step 03/STEP03-PRODUCTION-REMEDIATION-ACCEPTANCE.md`.
- Steps 4–7 CLOSED by acceptance of existing Step 2–3 evidence, with limitations in `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`. No new tests, Ansible deploy, live qgroup operation or restore claimed.

## Risks and handoff

- Root cause is consistent with persisted Btrfs quota metadata after historical snapshot deletion. The precise kernel/userspace lifecycle failure and recurrence-prevention mechanism are **not proven**.
- `backup` was running Ubuntu 22.04.5/kernel 5.15/Btrfs userspace 5.16.2; upgrade to Ubuntu 24.04 is the immediate separately approved follow-on (not part of 0039-DEF). Preserve console/recovery access, boot fallback, filesystem UUID/receipt/ro checks, protected snapshots, and Ansible check/diff/idempotency gates.
- New stale orphans can recur on either `backup` or `mars` despite the clean post-remediation point-in-time observation. Keep diagnostics and investigate post-upgrade recurrence before adopting any automatic deletion mechanism.
- No mass qgroup cleanup, snapshot retention/hold changes, extra full restore, or OS upgrade is authorised by this closeout record.

## Source and operator validation

- Operator-supplied clean, synchronized starting revisions: Diaries `6d682e48bb31513c19f6f7600d1b05e082cd9f12`; Playbooks `b55d1f4cf0d72dbbca461bedd2338b0bcf1b98fc` (merge of `e685066` and `dcbc7b0`). These are **pre-closeout** revisions.
- Operator Cygwin `git diff --check` after Step 4–7 reconciliation produced no warnings; files listed: `IMPLEMENTATION-STEPS.md`, `README.md`, and untracked `evidence/STEPS04-07-EVIDENCE-RECONCILIATION.md`.
- **Pending, do not pre-claim:** compare and apply this ZIP, move the entire feature directory intact to `change-control/complete/`, verify staged changes and commit; capture final Diaries HEAD and clean/synced Git state.

**Recommended final status after these pending checks pass:** Step 8 CLOSED; 0039-DEF CLOSED with explicitly accepted temporary recurrence risk and a separate Ubuntu 24.04 upgrade follow-on.
