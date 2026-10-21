# Design boundary — backup is a native Btrfs receive-only host

## Current state observed 20 October 2026

- Installed manager currently fails: `ERROR: verified Diaries dataset parent missing/unsafe: /@data/diaries-mars-replica/pluto`.
- Installed `/etc/btrfs-snapshot-manager.json` has obsolete writer lock ` /@data/diaries-mars-replica/.btrfs-snapshot-writer.lock` (without leading space) and verification `diaries-mars-replica/pluto/diaries-backup` / marker `diaries-mars-replica/.diaries-snapshot-verified.json`; `required: true`.
- `backup` contains 14 observed native received `@data` snapshots from `20261009-170001Z` through `20261020-030026Z`; paths `/@data/mars-received/@data/YYYYMMDD-HHmmssZ`; `.replication-state` present. An inventory at one point in time is not evidence of all ongoing transfers.
- No timer matches returned by `systemctl list-timers --all | grep -Ei 'btrfs|snapper' || true` in the earlier capture. Explicit `is-enabled` and `is-active` checks are still required.
- Effective `ansible-inventory --host backup` showed `btrfs_filesystem_path: /`, `btrfs_subvolume_path: /@data`, no `btrfs_snapshot_*` overrides in filtered output. Role defaults set `btrfs_snapshot_activation_enabled: false`, `btrfs_snapshot_require_verified_diaries: false`, `btrfs_snapshot_writer_lock_path: ''`.
- `remote-backup.yaml` calls `roles/remote-backup`, which includes `roles/snapshots`. Receiver routines use `/@data/mars-received` and are separate from local manager under `/@snapshots`.

## Safety invariants

1. Do **not** reinterpret `/@data/mars-received/@data` as the local manager's `snapshot_root`.
2. Do **not** run `btrfs-snapshot-manager create`, `prune`, `run`, `legacy-delete` or `legacy-prune` on `backup` as part of this correction.
3. Do **not** enable `btrfs-snapshot-create.timer`, `btrfs-snapshot-prune.timer` or `btrfs-legacy-prune.timer` on `backup`.
4. Preserve read-only receiver snapshots, parent UUID dependencies, replication receipts and `.replication-state` writer locks.
5. Retire stale verified mutable-dataset paths on `backup`; do not recreate an obsolete replica.
6. Source-controlled Playbooks is authoritative. Existing remote config and binaries receive rollback copies before any real deployment.
7. Confirm real deployment and a separate repeat run. `--check` predictions do not prove that a real host state changed.
8. If the Ansible diff shows unexpected receiver data, service activation, deletion, or retention change, stop for review.

## Baseline dry-run (operator evidence)

`ansible-playbook remote-backup.yaml --limit backup --check --diff --vault-password-file ~/.vault_pass.txt` ended `ok=22 changed=5 failed=0 skipped=13`. The five proposed changes were manager, `diaries-backup-history`, schema-2 manifest verifier, manager JSON, and **two installed legacy-prune unit files** (the unit-file loop was one changed task with two changed items). No timer activation task was run. No real reconciliation has yet been demonstrated.

## Acceptance

Manager `status` works on `backup`; no obsolete replica references remain in manager JSON; all three local manager timers disabled/inactive; received snapshots and receipt state preserved; native receiver independently confirmed healthy; Ansible second real run `changed=0` (or documented benign reason); reviewed code/docs in version control. No full restore required unless evidence contradicts earlier accepted correctness.
