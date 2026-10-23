# 0040-FEAT — Receiver checkpoint-hold safety gate

Date: 2026-10-23. Status: source implementation and local regression only; **not deployed or closed**.

## Purpose

Avoid deleting accepted historical recovery checkpoints if they become ineligible under ordinary age-based retention. The receiver internal transaction now refuses destructive execution unless checkpoint holds are explicitly configured. It validates holds against matching verified receiver receipts and source UUIDs, and includes held snapshots in the retention keep set. The read-only `receiver-plan` also includes holds when configured.

## Scope

- Playbooks: `roles/snapshots/files/btrfs-snapshot-manager.py` only.
- No endpoint, sudoers, schedule, retention bucket, or CLI deletion change.
- The existing public receiver-prune CLI remains blocked.
- This is a safety prerequisite, **not** a functional cross-host deletion executor.

## Test evidence

Local execution with Python 3: eight unit tests passed, including valid hold, missing configuration, missing snapshot, missing/symlink receipt, mismatched UUID, and checks that hold enforcement precedes journal creation and public deletion stays disabled.

## Critical pre-deployment gate

The currently deployed receiver manager config does **not** declare mandatory receiver checkpoint holds. After this update, the internal destructive helper deliberately refuses deletion until `checkpoint_holds.required=true` and an independent root-owned `0600` hold file is installed and verified through Playbooks. Do not manufacture or alter historical receipts or snapshots. Define accepted checkpoints and UUIDs from authoritative on-host evidence, including previously protected historical checkpoints, through the normal change-control process.

Do not enable receiver deletion or add sudoers privileges. A disposable Btrfs end-to-end execution and interruption-recovery rehearsal is still required. Keep 0040-FEAT OPEN.
