# 0045-FEAT — Step 4 closure preparation and remaining actions (11 November 2026)

**Status: OPEN.** Steps 1–3 are accepted; do not move the feature to `complete/` until the final Diaries Git/closure receipt is recorded and reviewed.

## To reconcile before feature closure

1. Confirm the latest authoritative Windows Diaries branch, HEAD, parent/submodule revisions, staged and untracked changes. The last known published Diaries baseline was `731c6a3` (Step 1 closure); later Step 2/3 tooling and reports may be uncommitted.
2. Review files under `evidence/Step 2/` and `evidence/Step 3/`, especially Ansible logs for secrets or other sensitive data before staging. The source log includes encoded checkpoint receipts, which are operational metadata, not proof of plaintext secret disclosure. Keep original raw evidence feature-local, subject to sensitivity review.
3. Record the managed asset comparison and runtime-health results from `reports/STEP3-FINAL-ACCEPTANCE-20261111.md`; the authoritative full before baseline is `evidence/Step 1/baseline-20261111-111819Z/`. Preserve the original mismatch and its reconciliation as separate evidence.
4. Confirm the Playbooks source remains `1939a0984934062d03c01de826ad4a5a87d3338d`, clean and synced with `origin/main`. The known-good rollback revision remains `7dfa93fef6d975aa82f5f4cfdf54497b106e7645`. No rollback should occur if equivalence passes.
5. Commit/publish the feature-local Diaries evidence and acceptance material, preserving other unrelated work. On final approved closure, move the whole 0045 feature from `change-control/in-progress/` to `change-control/complete/`, update README and implementation step 4 status, commit and push, then verify both repositories.

## Residual scope decision

The original local/remote backup operator playbooks and wrappers were deliberately retained for compatibility because external SCM Jenkinsfiles and unmanaged schedulers were not exhaustively audited. This is an explicit non-blocking residual audit scope, **not** an assertion that old callers do not exist. This feature did not alter the installed backup system to remove them.

## Final state expected

- All four steps marked CLOSED **after** final publication and evidence acceptance.
- No outstanding installed-state mismatch; both hosts still use the approved inventory and service/schedule contracts.
- Feature history and acceptance receipts available in the Diaries parent repository under `change-control/complete/0045-FEAT - reorganise backup and Btrfs Ansible deployment/`.
- Playbooks `main` remains at the accepted refactored revision; a later change, if any, must be reconciled explicitly.
- 0046 inventory migration remains separate work, not included in 0045 feature closure.
