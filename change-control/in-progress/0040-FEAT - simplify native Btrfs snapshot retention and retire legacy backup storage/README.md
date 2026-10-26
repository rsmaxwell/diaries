# 0040-FEAT — Simplify native Btrfs snapshot retention and retire legacy backup storage

**Status: IN PROGRESS — Steps 1–8 CLOSED under their recorded acceptance decisions; Step 9 and overall Steps 10–14 remain OPEN.** Created 23 October 2026. Step 3 design acceptance includes the documented cross-host rehearsal waiver. The backup-only portions of Steps 10–11 are accepted; native `mars` root-snapshot retirement and receiver pruning remain unauthorised.

## Classification

**Feature**, not defect: an intentional architecture and operational simplification following the completed 0037-FEAT, 0038-FEAT and 0039-DEF work. Do not reopen their accepted closures. Defects discovered during implementation should be documented and triaged separately where appropriate.

## Objective

Use **the same source-controlled `btrfs-snapshot-manager` implementation on `mars` and `backup`**, differentiated by configuration and explicit source/receiver safety modes. Retain collection and snapshot creation on `mars`; keep `backup` as a **receive-only** Btrfs snapshot host with retention applied only to accepted received snapshots. Remove obsolete legacy backup data and snapshot trees after audited approvals.

## Intended receiver contract

- Retain `/@data/mars-received/@data/YYYYMMDD-HHmmssZ` read-only received snapshots.
- Retain `/@data/mars-received/.replication-state/` including receipts and `writer.lock` (and other required receiver state).
- Never treat a received snapshot as a mutable local snapshot or casually alter its Received UUID/read-only state.
- Retire, after verification and explicit destructive gate: `/@data/backup`, `/@data/.snapshots`, `/@snapshots/@data`, `/@snapshots/root`.
- Retire `/.snapshots`, APT-generated root Snapper pre/post snapshots, Snapper configs/packages/hooks and obsolete `/@snapshots` trees on `backup` after controlled safety and deletion gates. Root OS snapshots are not equivalent to received backup datasets; the operator explicitly accepted the loss of legacy-only rollback points.
- Preserve verified datasets, including `backup/pluto/diaries-backup`, within retained received snapshots. `datasetRelativePath` and `sourceIdentity` metadata describe the embedded Diaries dataset, not the overall multi-host snapshot.

## Confirmed scope extension — mars root snapshots (23 October 2026)

Read-only inspection established that `/media/usb/@snapshots/root/20261023-070038Z` contains only two empty nested-subvolume placeholders (`@data` and `@snapshots`), is read-only, and references/exclusively occupies 16 KiB. The live Btrfs root contains only these two nested subvolumes. The operator approved retiring the **mars root snapshot population**, while preserving all necessary `@data` snapshots and replication protection. This is an explicit extension of 0040-FEAT, not permission to delete anything during Step 1.

The desired steady state is **one `@data` snapshot population per host**: source snapshots under `/media/usb/@snapshots/@data/<timestamp>` on `mars`; accepted received snapshots under `/@data/mars-received/@data/<timestamp>` on `backup`. The same source-controlled manager and retention selector must handle both through configuration. Remove the paired-root/`@data` complete-set assumption, stop root snapshot creation **only after migration acceptance**, safely retire existing `mars` root snapshots under a separately approved destructive gate, and reconcile holds/replication safety. Root OS Snapper history on `backup` was also explicitly approved for retirement in Step 2.

## Scope

Playbooks source and Ansible configuration for `mars` and `backup`; snapshot-manager implementation/tests; native sender/receiver integration and locks; retention selection and GFS buckets; read-only inventories; planned guarded retirement; operator documentation and closure.

Out of scope unless separately approved: rebuilding/resending the full backup baseline, modifying `pluto` authoring backups, changing other host backup schedules, altering production NAS data, updating Diaries client/responder images, deleting received snapshots outside approved retention, or relaxing replication safeguards.

## Feature workspace (same model as 0037/0038)

- `DESIGN.md` — architecture, invariants, decision points.
- `IMPLEMENTATION-STEPS.md` — sequential acceptance gates.
- `PROMOTION-MANIFEST.md` — permanent changes and rollback evidence.
- `tools/` — temporary capture wrappers or experimental utilities.
- `tests/` — feature-local regressions and fixtures.
- `reports/` — interpreted inventories, comparisons and dry-run reviews.
- `evidence/Step NN/` — raw logs, approvals, outcomes and closure records.
- `scratch/` — disposable non-committed intermediates.

Permanent reusable code belongs in the Playbooks repository **only after review/promotion**. The Diaries change-control tree owns temporary material and evidence. Do not put experiment scripts or feature-numbered working files into production role directories.

## Workflow

One manageable stage at a time. Use **Cygwin** for ZIP application and local orchestration, SSH terminals on **mars** and **backup** for inspection, and **mango** for Ansible with `--vault-password-file ~/.vault_pass.txt`. Review `--check --diff`, then explicitly approve changes, deploy, verify and prove idempotency. Record results and exact source revisions. Close the feature only after all acceptance gates, then move its whole directory to `change-control/complete/`.

**Next action: Step 9 — reconcile native incremental and guarded-pruning safety evidence against the accepted accelerated-path waiver; do not activate receiver pruning or perform native `mars` root-snapshot deletion without their separate gates.** See `IMPLEMENTATION-STEPS.md`, `CONSOLIDATED-PRUNE-GATE.md` and `reports/STEP09-SOURCE-CLEANUP-RECONCILIATION-20261025.md`.
