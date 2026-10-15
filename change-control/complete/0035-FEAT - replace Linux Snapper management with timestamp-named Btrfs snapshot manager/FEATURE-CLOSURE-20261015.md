# 0035-FEAT — Formal feature closure (2026-10-15)

**Decision: CLOSED.** The timestamp-named Btrfs snapshot manager feature has completed Steps 1–9 and is archived from `change-control/in-progress/` to `change-control/complete/`.

## Source revisions and status

| Repository | Last verified `main` / `origin/main` commit | Observed status |
| --- | --- | --- |
| Diaries | `bc441181bba128855f642773cee45a7ca795e877` (0035-FEAT Step 9) | clean, synchronized |
| Playbooks | `0bf68c5a46eed4975a002b55f29ba1bb94dfbb10` (0035-FEAT Step 8) | clean, synchronized |

These are **pre-closure** revisions recorded in the operator logs. The subsequent commit that archives this feature is not yet known and must not be fabricated. No new Playbooks code modification is required for the archival action.

## Signed-off acceptance

- Steps 1–7: previously recorded as CLOSED with scoped source and live acceptance evidence.
- Step 8: CLOSED; live retention and history verification, offline contract, kernel Btrfs full/incremental and truncated-stream tests, real receive ENOSPC, transport/acknowledgement injection, isolated loopback SSH interruption and actual receipt-publication ENOSPC passed within their stated scopes. See `evidence/Step 8/STEP-8-CLOSURE-20261015.md` and `FINAL-EVIDENCE-RECONCILIATION-20261015.md`.
- The prior 0034 disposable schema-2 recovery acceptance was accepted as inherited evidence. A second full restore was **not** undertaken; source 0034 execution transcripts were not independently re-read in Step 8.
- A combined production-equivalent sender/SSH failure integration test was **not required**, by explicit acceptance decision. The separate tests must not be portrayed as that combined test.
- Quantitative stream bytes, duration, disk allocation, and performance/capacity benchmarking were **excluded** from closure scope by explicit decision; no efficiency claims are made.
- Step 9: Gate 9A read-only scheduler inventory PASS; Gate 9B acceptance of the already-active schedule **without another cutover**; Gate 9C final read-only safety verification PASS. `mars`, `backup` and `pluto` each reported `ok=2 changed=0 failed=0` (log `evidence/Step 9/gate9c-mango-20261015-112318.txt`).

## Accepted deployed state

- `mars`: timestamp-named create/prune timers and native push timer enabled and active; Snapper legacy timers disabled. At Gate 9C, 52 paired complete sets, zero incomplete; retained checkpoint `20261013-171228Z` and replication-protected parent `20261015-030004Z`; prune dry-run would delete zero sets. No destructive prune was run **as part of Gate 9C**.
- `backup`: passive Btrfs receiver with local creation/prune disabled, accepted native receipts and historical repository preserved.
- `pluto`: existing schema-2 publication present; no Btrfs-specific mutation.

## Boundaries and further operations

Feature close-out is a documentation/change-control operation, **not** permission to delete historical Snapper data or backups, reseed a receiver, release replication pins, disable safety gates, alter timers, or run manual production pruning. Rollback is schedule-only, subject to active-transfer checks, and preserves receipts and source protections. See Step 9 rollback guidance. No Docker build or production deployment is required for archival.

## Archival procedure

Move the entire feature directory using `git mv` to retain all evidence and history, then overlay the three updated closure documents from the change package at their `change-control/complete/` paths. Commit/push that archival change; record the new commit in Git history.
