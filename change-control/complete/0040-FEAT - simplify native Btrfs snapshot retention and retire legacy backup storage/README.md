# 0040-FEAT — Simplify native Btrfs snapshot retention and retire legacy backup storage

**Closure status (9 November 2026): Steps 1–13 CLOSED; Step 14 operational verification PASSED. Overall 0040-FEAT remains IN PROGRESS until the operator explicitly accepts the historical-storage exception described below and the complete feature directory is committed and pushed under `change-control/complete/`.** The verified Step 13 closure commit is Diaries `815eb25`; Playbooks source HEAD is `e0da797`. Historical decisions and evidence are preserved. The feature was created on 23 October 2026.

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

The operator imported and verified **21** original raw `evidence/Step 13/` files into Windows on 9 November; the final Playbooks removal log is preserved as a **22nd** evidence file. The current Playbooks source revision is **`e0da797`**, which only removes the unreferenced tracked `roles/btrfs-replication/tasks/native.yaml.pre-wrapper-tags` file. The runtime deployment implementing source pruning remains `6ccbf73`; no production redeployment was needed for the housekeeping commit. See [`reports/STEP13-FORMAL-CLOSURE-20261109.md`](reports/STEP13-FORMAL-CLOSURE-20261109.md) for Step 13 acceptance, the evidence index and Git-promotion gate. **Step 14 operational checks have since PASSED**, including read-only root and legacy-tree inspections, shared manager SHA-256 parity after the receiver's Ansible update, `backup changed=0 failed=0` check-mode idempotency, and verified equal sender/receiver agreed parents. Five raw Step 14 investigation/deployment logs were imported into the Windows repository on 9 November; a sixth raw log records their import. The 0039-DEF stale-qgroup recurrence and 0041-FEAT dedicated-account hardening remain separate. See `reports/STEP14-FINAL-ACCEPTANCE-AND-FEATURE-CLOSURE-20261109.md` for the exact evidence and conditional closure decision.


## Step 14 — historical storage scope clarification and final closure

The original 0040 objective listed `/@data/backup` on `backup` among legacy retirement targets. Final read-only inspection established that it **still contains historical backups for multiple machines**, is an ordinary data directory (not a received Btrfs subvolume), and is explicitly protected against deletion by `roles/remote-backup/README.md` and historical 0035 verification guidance. **It was NOT retired.** This material exception requires the operator's explicit acceptance at feature closure; absence of changes after 10 October is not proof of redundant data. No snapshot/data deletion is authorised by acceptance of this exception.

The legacy paths `/@snapshots/@data` and `/@snapshots/root` remain as **empty ordinary directories** with no Btrfs subvolumes, not as retained snapshot histories. Keep these harmless containers rather than introduce another filesystem mutation for cosmetic cleanup. On `mars`, the root snapshot directory is empty and contains no matching root subvolumes; `@data` snapshot creation/pruning remains in service.

The current shared-manager SHA-256 on Playbooks, `mars` and `backup` is `89602f0aac07900b367a82728e42339ee9c9d3ed40e55010af87576dadc7a2b7`; the simplified-replication executable matched on the two hosts in the Step 14 audit. Receiver Ansible recheck was `changed=0 failed=0`, 32 accepted received snapshots were retained with 0 candidates, and source/receiver agreed-parent status was equal. Source and receiver retention schedules and parent/checkpoint protections remain unchanged. Retained historical `/@data/backup` does not replace the native received snapshot population.

**Formal closure rule:** 0040-FEAT is CLOSED only when the operator affirmatively accepts this historical-storage exception and the full feature directory (including its unmodified prior evidence, Step 14 logs and closure report) has been moved with Git from `change-control/in-progress/` to `change-control/complete/`, committed and pushed successfully. Until that promotion, the feature is OPEN. No repeat full restore, large replication test or snapshot deletion is needed for the accepted result.
