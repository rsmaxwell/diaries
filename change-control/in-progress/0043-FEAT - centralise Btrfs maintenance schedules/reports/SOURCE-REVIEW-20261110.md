# 0043 source review — 10 November 2026

## Verified against supplied Playbooks bundle and accepted 0039/0042 changes

- `roles/snapshots/templates/btrfs-snapshot-prune.timer.j2` uses variable
  `btrfs_snapshot_prune_on_calendar`, `Persistent=true`, `AccuracySec=1min`.
- `roles/btrfs-replication/templates/btrfs-receiver-simple-prune.timer.j2`
  uses `btrfs_simplified_receiver_prune_on_calendar`, `Persistent=false`.
- The sender uses `btrfs_native_push_on_calendar` (03:30 UTC).
- Both stale-qgroup timers use `btrfs_stale_qgroup_on_calendar` (05:30 UTC).
- Source creates hourly timestamps, before this feature prunes at `*:15`.
- The source manager and Ansible source role enforced 10 deletions per run.
  Enlarging the daily cap to 32 is necessary to avoid a growing retention
  backlog. Source cap remains bounded; no retention or parent/hold changes.
- Receiver pruning already runs daily 04:15 and retains cap 10; its source
  and receiver filesystems are independent.
- Effective `/etc/ansible` inventory is not in supplied ZIP; real host
  settings must be verified by the guarded installer and post-deployment
  readback. No live-state deployment claim is made by this report.

## Offline validation

The assembled Playbooks fixture (0042 retirement + 0039 cleaner) passed:

1. `verify-0040-step13-source-prune-cap.py` (including 40 eligible sets,
   32 selected, all 40 prevalidated, protected pins untouched).
2. `verify-btrfs-snapshot-manager.py`.
3. `verify-0040-prune-source-selection.py`.
4. `verify-checkpoint-holds.py`.
5. `verify-native-prune-subvolume-id.py`.
6. `verify-btrfs-clear-stale-qgroups.py` (22 tests).
7. `scripts/tests/verify-maintenance-schedule.py` (plan, apply, idempotence,
   conflict refusal, unknown-file refusal, failed-inventory rollback, remove).

The source calendar values were validated by `systemd-analyze calendar`.
Host Ansible deployment, host timer installation and next natural prune
execution are not evidenced until operator-provided logs are accepted.
