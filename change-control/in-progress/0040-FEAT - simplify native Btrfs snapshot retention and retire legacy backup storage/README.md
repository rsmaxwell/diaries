# 0040-FEAT — Simplify native Btrfs snapshot retention and retire legacy backup storage

**Status: IN PROGRESS — Step 12 CLOSED (8 November 2026); Step 13 CLOSED (9 November 2026, effective on Git promotion of this closure record); Step 14 overall feature closure OPEN.** Step 13 acceptance includes capped unattended `mars` source pruning, Windows evidence import, and the final Playbooks housekeeping commit `e0da797`. The overall 0040 feature remains in `change-control/in-progress/` until Step 14 formal approval. The Step 13 Git promotion must pass before its closure is considered recorded in source control. Created 23 October 2026. Historical acceptance records remain unchanged.

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

Playbooks source and Ansible configuration for `mars` and `backup`; snapshot-manager implementation/tests; native sender/receiver integration and simple local non-blocking locks; retention selection and GFS buckets; read-only inventories; planned guarded retirement; operator documentation and closure.

Out of scope unless separately approved: rebuilding/resending the full backup baseline, modifying `pluto` authoring backups, changing other host backup schedules, altering production NAS data, updating Diaries client/responder images, deleting received snapshots outside approved retention, or relaxing replication safeguards.

## Step 12 design revision — 5 November 2026

The operator selected a simpler **native send/receive + small agreed-parent state file on both hosts + ordinary logs + non-blocking per-host lock** design. An interrupted receive should normally be **cleaned up and retried at the next scheduled run** when the incomplete destination is unambiguously identified and unprotected; recurring failures are resolved manually. Avoid per-transfer durable journals, stream rewriting, staged publication, systemd receive scopes and elaborate proof/ownership protocols. Preserve existing accepted production snapshots and independent holds.

The authoritative decision is [`reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md`](reports/STEP12-3-SIMPLIFIED-DESIGN-DECISION-20261105.md). The revised [`IMPLEMENTATION-STEPS.md`](IMPLEMENTATION-STEPS.md) supersedes old Step 12.3 gate lists; earlier reports/tests are historical. See [`reports/STEP12-3-TEST-CLEANUP-20261105.md`](reports/STEP12-3-TEST-CLEANUP-20261105.md) for guarded retirement of obsolete Playbooks verification scripts.

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

Implement the simplified Step 12 workflow as one coherent change, followed by consolidated tests and controlled cutover. Use **Cygwin** for ZIP application and local orchestration, SSH terminals on **mars** and **backup** for inspection, and **mango** for Ansible with `--vault-password-file ~/.vault_pass.txt`. Review `--check --diff`, then explicitly approve changes, deploy, verify and prove idempotency. Record results and exact source revisions. Close the feature only after all acceptance gates, then move its whole directory to `change-control/complete/`.

**Current position (9 November 2026):** Step 12 is **CLOSED**; its final record is [`reports/STEP12-FINAL-ACCEPTANCE-AND-CLOSURE-20261108.md`](reports/STEP12-FINAL-ACCEPTANCE-AND-CLOSURE-20261108.md). Step 13 **operational acceptance is PASSED**: the source pruning role was deployed in Playbooks `6ccbf73`, and `mars` now creates hourly at `:00` and prunes at `:45`, limited to 10 snapshot sets per run. The first normal `:45` run on 9 November finished successfully with 10 deletions, 146 complete snapshots, no incomplete sets, and verified sender/receiver agreed parents. The previous `:15` lock-contention failures remain preserved in evidence. See [`reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md`](reports/STEP13-BOUNDED-SOURCE-PRUNING-OPERATIONAL-ACCEPTANCE-20261109.md) and [`reports/STEP13-SOURCE-PRUNING-RUNBOOK-20261109.md`](reports/STEP13-SOURCE-PRUNING-RUNBOOK-20261109.md).

The operator imported and verified **21** original raw `evidence/Step 13/` files into Windows on 9 November; the final Playbooks removal log is preserved as a **22nd** evidence file. The current Playbooks source revision is **`e0da797`**, which only removes the unreferenced tracked `roles/btrfs-replication/tasks/native.yaml.pre-wrapper-tags` file. The runtime deployment implementing source pruning remains `6ccbf73`; no production redeployment was needed for the housekeeping commit. See [`reports/STEP13-FORMAL-CLOSURE-20261109.md`](reports/STEP13-FORMAL-CLOSURE-20261109.md) for Step 13 acceptance, the evidence index and Git-promotion gate. **Step 14 remains OPEN**, including the final feature-wide review and move to `change-control/complete/`. **0039-DEF** owns recurring stale Btrfs qgroups (606 at the accepted 08:45 prune); **0041-FEAT** retains dedicated-account hardening.
