# 0049 — Receiver deployment and read-back, 16 November 2026

**Status:** `backup` receiver deployment accepted; sender deployment to `mars` pending.

## Inputs

- `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/evidence/Step 4/MANGO-RECEIVER-DEPLOYMENT-20261116.txt` — supplied complete Ansible deployment terminal log.
- `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/evidence/Step 4/BACKUP-RECEIVER-READBACK-20261116.txt` — supplied terminal read-back from `backup`.

## Receiver deployment result

- Existing source and regression tests passed (19 0049, 8 0041, 25 replication cases).
- Ansible run `btrfs-replication.yaml --limit backup` completed with `ok=35 changed=9 unreachable=0 failed=0`.
- New `btrfs-receiver-prune.timer`: `loaded active enabled`; older `btrfs-receiver-simple-prune.timer`: `not-found inactive`.
- New service invokes `/usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json prune --max-delete 10` as root. No manual prune executed as part of the read-back.
- `btrfs-backup-status --local-only`: HEALTHY, 40 received snapshots, latest `20261116-030016Z`, qgroups total=43 stale=0 under_deletion=0.
- Current agreed parent `20261116-030016Z`; prior parent `20261115-140017Z`. Read-only plan selected **zero deletions**; 2 holds and 27 preserved historical receipts were reported.
- Next receiver-prune timer firing reported as **2026-11-17 04:15 UTC**.
- Independent transfer receipt remains unavailable; the report correctly shows the transfer time as unknown.

## Source integration correction identified before sender deployment

The 0049 infrastructure report called `btrfs-replication sender status` with no `BTRFS_REPLICATION_IDENTITY_MODE` environment setting. The accepted 0041 sender service sets `BTRFS_REPLICATION_IDENTITY_MODE=dedicated` in its root-owned wrapper; an unset mode instead selects the retained historical SSH transport. The receiver-only test could not expose this sender-side integration problem.

Corrected in Playbooks package `0049-FEAT-playbooks-sender-status-0041-fix.zip`:

1. Source-side `btrfs-backup-status` now forces the accepted dedicated 0041 transport **only for the read-only sender status subprocess**; `--local-only` remains offline.
2. 0049 regression tests assert the dedicated mode is supplied on sender reports, and not on receiver reports.
3. Playbooks operator guidance documents the explicit environment assignment required for direct sender CLI inspection.

No 0041 wrapper, SSH forced command, sudoers policy, replication wire protocol, state record, snapshot, scheduled operation or retention setting is modified by this corrective package. Offline regression after the correction: **19 + 8 + 25 tests passed**; Python source compiles. Live sender verification remains pending.

## Acceptance boundary / next action

Review/apply the small Playbooks correction via Beyond Compare, deploy `btrfs-replication.yaml --limit mars` from `mango`, and capture `mars` and `backup` read-only status/timer/parent evidence. Do not mark 0049 CLOSED or claim an end-to-end push succeeded until live sender and both-end checks are accepted. Preserve pre-0049 evidence and existing snapshot lineage.
