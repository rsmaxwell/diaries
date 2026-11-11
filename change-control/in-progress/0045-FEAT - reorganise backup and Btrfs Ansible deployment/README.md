# 0045-FEAT — Reorganise backup and Btrfs Ansible deployment

**State:** PLANNED — NOT STARTED  
**Created:** 10 November 2026  
**Ownership:** Diaries parent repository, `change-control/in-progress/0045-FEAT - reorganise backup and Btrfs Ansible deployment/`  
**Implementation location:** `/home/richard/playbooks` on `mango`  
**Execution window:** **After both 0039-DEF and 0043-FEAT have been formally closed.**

## Objective

Make the backup-collection, Btrfs snapshot and native-replication Ansible deployment easier to understand and maintain, following the established structural pattern in `roles/ledger/tasks/`: validate configuration; create directories; synchronise explicitly managed static files; render templates; apply required ownership/security; validate; then activate or reconcile services and schedules.

**Non-negotiable result:** An implementation using the reorganised Playbooks must produce the **same installed configuration and operational behaviour** as the accepted original Playbooks, on the same inventory, for `mars` and `backup` (and any other verified in-scope backup host). This is an internal source refactor, **not** a backup migration, reinstall, retention change, scheduler change or service redesign.

The old and new source layouts may differ; the installed artifacts, activation states, intended operations and protected runtime data must not. Approved operator-facing playbook/launcher renames are the only expected interface differences, and these must be documented and checked for callers first.

## Dependencies and starting point

- Do **not** start implementation or modify the installed systems before formal acceptance/closure of **0039-DEF** (stale-qgroup reconciliation) and **0043-FEAT** (central Btrfs maintenance scheduling).
- The uploaded **9 November 2026 Playbooks source bundle** is the basis for the source review. It predates the accepted 10 November changes, particularly 0043 scheduling and 0044 permanent regression naming. **Do not use that bundle as the implementation baseline.**
- At plan creation, the last verified Playbooks `main` publication was `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` (0044), and Diaries `main` was `30eeb2e71bfa0de9030eefcef009e06a4e27d572`. Refresh Git, working-tree and effective-inventory baselines at the actual start of this feature; both may have advanced when 0039/0043 close.
- The authoritative inventory is **`/etc/ansible` on `mango`**, including `/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml`. Do not create a duplicate `inventory/` tree in Playbooks. Playbooks Git is `/home/richard/playbooks`; the authoritative Diaries working copy is on Windows.

## In scope

1. Clean up the **playbook and launcher interface**, subject to reference/caller audit:
   - Propose `local-backup.yaml` → **`backup-collection.yaml`** and `scripts/local-backup.sh` → **`scripts/backup-collection.sh`**.
   - Retire **`remote-backup.yaml`** and **`scripts/remote-backup.sh`** only after proving no required caller remains and documenting the `btrfs-replication.yaml` replacement.
   - Keep `btrfs-replication.yaml`, `snapshots.yaml`, `btrfs.yaml` and their existing valid execution contracts.
2. Retain the distinct functional roles **`local-backup`**, **`snapshots`**, **`btrfs-replication`** and **`btrfs`**; do not combine them into a monolithic `backup` role. Retain inventory groups `local_backup` / `remote_backup` and endpoint values **`source`** / **`receiver`** for `btrfs_native_endpoint_role`.
3. Refactor repetitive deployment tasks into coherent Ledger-style orchestration and bulk file/template manifests, especially `roles/snapshots/tasks/main.yaml` and `roles/btrfs-replication/tasks/native.yaml`, while preserving order-sensitive validation, locks, privileged state, timer gates and source/receiver separation.
4. Update active operator documentation, launcher references and maintained regression tests; preserve historical evidence and completed feature documents unchanged.

## Out of scope / prohibited incidental changes

- No changes to retention buckets, prune limits, scheduled times, timer persistence, enabled/disabled states or maintenance ordering.
- No changes to snapshot/replication algorithms, checkpoint or agreed-parent states, state schemas, SSH trust, sudoers privilege, mounts, ACLs, services/cron definitions, ownership, permissions, executable contents or installed paths.
- No migration, deleting backups, destructive Btrfs maintenance, manual send/receive, recovery restore, qgroup reset, legacy snapshot removal, or opportunistic cleanup of installed files.
- No permanent feature-specific migration/test scripts in the Playbooks repo; tools and evidence live under **this** Diaries feature's `tools/`, `tests/`, `evidence/`, `reports/`.

## Deliverables

- One coherent Playbooks refactor with the simplified playbook/launcher interface, updated operator documentation and maintained tests.
- A recorded **before/after installation equivalence** comparison based on the then-current approved `mars` and `backup` installations and effective inventory.
- A single consolidated offline regression, controlled deployment and live readback, without a full restore or unnecessary manual replication.
- Commit and publication receipts for Playbooks and Diaries, rollback plan and accepted final evidence, followed by formal feature closure.

## Feature documents

- [`IMPLEMENTATION-STEPS.md`](IMPLEMENTATION-STEPS.md) — practical sequence and acceptance gates.
- [`INSTALLATION-EQUIVALENCE-CONTRACT.md`](INSTALLATION-EQUIVALENCE-CONTRACT.md) — what “identical installation” means and how to demonstrate it.
- [`reports/SOURCE-REVIEW-20261110.md`](reports/SOURCE-REVIEW-20261110.md) — actual source observations and assumptions requiring reconfirmation.
- [`tests/ACCEPTANCE-MATRIX.md`](tests/ACCEPTANCE-MATRIX.md) — consolidated regression/deployment/readback evidence matrix.

**Closure rule:** Leave this feature `in-progress` and its steps OPEN until the accepted comparison and source-control evidence support formal closure. Preserve all original evidence under this feature, not `/home/richard` or the Playbooks repository.
