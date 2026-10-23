# 0040-FEAT — Simplify native Btrfs snapshot retention and retire legacy backup storage

**Status: OPEN — planning only.** Created 23 October 2026. No production changes, deletion approvals or step closures are implied.

## Classification

**Feature**, not defect: an intentional architecture and operational simplification following the completed 0037-FEAT, 0038-FEAT and 0039-DEF work. Do not reopen their accepted closures. Defects discovered during implementation should be documented and triaged separately where appropriate.

## Objective

Use **the same source-controlled `btrfs-snapshot-manager` implementation on `mars` and `backup`**, differentiated by configuration and explicit source/receiver safety modes. Retain collection and snapshot creation on `mars`; keep `backup` as a **receive-only** Btrfs snapshot host with retention applied only to accepted received snapshots. Remove obsolete legacy backup data and snapshot trees after audited approvals.

## Intended receiver contract

- Retain `/@data/mars-received/@data/YYYYMMDD-HHmmssZ` read-only received snapshots.
- Retain `/@data/mars-received/.replication-state/` including receipts and `writer.lock` (and other required receiver state).
- Never treat a received snapshot as a mutable local snapshot or casually alter its Received UUID/read-only state.
- Retire, after verification and explicit destructive gate: `/@data/backup`, `/@data/.snapshots`, `/@snapshots/@data`, `/@snapshots/root`.
- Investigate and explicitly decide the disposition of `/.snapshots`, APT-generated root Snapper pre/post snapshots, Snapper configs/packages/hooks, and unused `/@snapshots` parents. Do **not** silently equate OS snapshots with replicated data.
- Preserve verified datasets, including `backup/pluto/diaries-backup`, within retained received snapshots. `datasetRelativePath` and `sourceIdentity` metadata describe the embedded Diaries dataset, not the overall multi-host snapshot.

## Scope

Playbooks source and Ansible configuration for `mars` and `backup`; snapshot-manager implementation/tests; native sender/receiver integration and locks; retention selection and GFS buckets; read-only inventories; planned guarded retirement; operator documentation and closure.

Out of scope unless separately approved: rebuilding/resending the full backup baseline, modifying `pluto` authoring backups, changing other host backup schedules, altering production NAS data, updating Diaries client/responder images, deleting received snapshots outside approved retention, or relaxing replication safeguards.

## Feature workspace (same model as 0037/0038)

- `DESIGN.md` — architecture, invariants, decision points.
- `IMPLEMENTATION-STEPS.md` — sequential acceptance gates.
- `WORKSPACE-POLICY.md` — hygiene and evidence placement.
- `PROMOTION-MANIFEST.md` — permanent changes and rollback evidence.
- `tools/` — temporary capture wrappers or experimental utilities.
- `tests/` — feature-local regressions and fixtures.
- `reports/` — interpreted inventories, comparisons and dry-run reviews.
- `evidence/Step NN/` — raw logs, approvals, outcomes and closure records.
- `scratch/` — disposable non-committed intermediates.

Permanent reusable code belongs in the Playbooks repository **only after review/promotion**. The Diaries change-control tree owns temporary material and evidence. Do not put experiment scripts or feature-numbered working files into production role directories.

## Workflow

One manageable stage at a time. Use **Cygwin** for ZIP application and local orchestration, SSH terminals on **mars** and **backup** for inspection, and **mango** for Ansible with `--vault-password-file ~/.vault_pass.txt`. Review `--check --diff`, then explicitly approve changes, deploy, verify and prove idempotency. Record results and exact source revisions. Close the feature only after all acceptance gates, then move its whole directory to `change-control/complete/`.

**Next action: Step 1 — read-only baseline and deletion-dependency inventory.**
