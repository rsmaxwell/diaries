# 0034-FEAT — Step 11.4 unattended operating arrangements

**Status: CLOSED — live unattended acceptance passed 2026-10-15 UTC.**

This substep selects the preferred operating policy left open by Step 11.1/11.3: normal off-site replication is **scheduled, source-initiated `mars -> backup` native Btrfs push**, not a permanently manual operation. All newly introduced schedules are explicit opt-ins and default **OFF** in Playbooks. Source implementation therefore does not itself change production runtime state.

## Operating ownership

| Stage | Host | Source-owned mechanism | Default-off calendar |
|---|---|---|---|
| Production schema-2 capture + stable publication | `pluto` | `diaries-complete-backup-publish.timer` | 00:30 UTC daily |
| Verified current-publication collection | `mars` | `diaries-pull.timer` | 01:30 UTC daily |
| Native timestamp snapshot creation | `mars` | existing `btrfs-snapshot-create.timer` | hourly at :00 |
| Native timestamp prune | `mars` | existing `btrfs-snapshot-prune.timer` | hourly at :15 |
| Off-site native incremental replication | `mars` | `btrfs-native-push.timer` | 03:30 UTC daily |
| Receiver verification/receipt | `backup` | invoked by source push | no receiver replication timer |

The calendars deliberately leave an hourly snapshot boundary between collection and off-site push. They are defaults only: external inventory remains authoritative and may deliberately override them.

## Safety decisions implemented

- `pluto` unattended backup runs the permanent supported `backup-dataset.sh publish-preflight` followed by `backup-dataset.sh publish`; no restore path is scheduled.
- `mars` unattended collection reuses the already accepted verified pull, atomic publication, schema-2 verification, snapshot eligibility marker and whole-backup writer lock.
- `btrfs-native-push --latest` selects only validated read-only `@data` snapshots through the constrained privileged endpoint. It revalidates the selected UUID before transfer.
- `--latest` is **incremental-only**. It refuses to create an implicit full baseline/reseed when no accepted common parent exists. Recovery/full reseed remains an explicit operator action.
- A newest snapshot already accepted on `backup` is a successful no-op, making timer retries/idempotent reruns safe.
- Native push timer activation checks the rendered `mars` root backup wrapper and refuses activation while its historical `remote/backup.sh` rsync phase is still active.
- The old rsync source remains available behind `legacy_remote_rsync_push_enabled` as a rollback transport, but final 11.4 acceptance requires that switch to be `false` so there is exactly one off-site transport.
- Receiver-side obsolete pull helpers remain retired. No new receiver scheduler is introduced.
- The independently held `20261013-171228Z` checkpoint and the active replication-parent protection remain untouched until final feature close-out.

## Monitoring/audit arrangement

Systemd owns the three new unattended jobs. `systemctl status`, `systemctl list-timers` and the journal provide an explicit last-result/next-run audit trail. `verification/0034-step11-4/verify-unattended.yaml` checks:

- publisher/pull/snapshot/push timers enabled and active where applicable;
- successful previous oneshot service results;
- fresh schema-2 publication on `pluto` and verified current collection on `mars`;
- a recent native `mars` snapshot;
- a non-mutating `btrfs-native-push --latest --preflight` plan;
- no active historical rsync off-site phase in the rendered `mars` machine wrapper;
- no obsolete receiver pull helpers;
- a recent accepted receiver receipt and immutable received subvolume on `backup`.

The verifier is read-only. It does not create a backup, pull data, create/prune snapshots, send/receive Btrfs data, or restore anything.

## External inventory intent

Inventory is intentionally not stored in the source bundle. The final effective intent is:

```yaml
# pluto
diaries_complete_backup_schedule_enabled: true

# mars
diaries_pull_install: true
diaries_snapshot_integration_enabled: true
diaries_pull_schedule_enabled: true
legacy_remote_rsync_push_enabled: false
btrfs_native_push_schedule_enabled: true

# already accepted on mars under 0035
btrfs_snapshot_activation_enabled: true
```

Existing host-specific path, disk UUID, SSH and secret variables must be preserved. Do not replace inventory wholesale with this illustrative block.

## Source verification completed

The modified source passes:

```text
roles/remote-backup/tests/verify-native-btrfs-static.py
roles/remote-backup/tests/verify-native-btrfs-push.py
roles/remote-backup/tests/verify-replication-protection.py
roles/local-backup/tests/verify-diaries-pull.py
roles/snapshots/tests/verify-checkpoint-holds.py
roles/snapshots/tests/verify-diaries-backup-history.py
verification/0034-step11-4/verify-source-contract.py
```

The modified YAML parses successfully, the modified Python compiles, rendered root-wrapper variants pass `bash -n`, and the three new service/timer pairs pass `systemd-analyze verify`. `systemd-analyze calendar` accepts and normalises the 00:30, 01:30 and 03:30 UTC schedules. These are source-level checks only; they are not production acceptance.

A broader unchanged 0035 regression in the uploaded 2026-10-14 source bundle, `roles/snapshots/tests/verify-btrfs-snapshot-manager.py`, still fails its pre-existing launcher assertion because `scripts/snapshots.sh` contains fixed `host="mars"` rather than the test's expected `host="${1:-mars}"` / `mars|backup` dispatch. The same test fails against the untouched uploaded source, so this is recorded as an existing 0035 source/test mismatch and is not altered as part of 0034 Step 11.4.

## Required live acceptance before closing 11.4

1. Apply the Playbooks source and persist the explicit inventory decisions above.
2. Deploy `local-backup.yaml` to `mars` first with `legacy_remote_rsync_push_enabled=false`; prove the rendered root wrapper no longer invokes the old remote rsync phase.
3. Deploy the `pluto` publisher timer and `mars` collection timer in their enabled state.
4. Preserve/verify existing accepted snapshot create/prune timer state on `mars`.
5. Deploy `native-btrfs.yaml`; enable the source push timer only after the legacy-rsync interlock passes.
6. Exercise each new oneshot service once deliberately, then leave timers enabled. Native test traffic must be incremental through the accepted common parent; do not run a full/reseed merely for this step.
7. From `mango`, run `ansible-playbook verification/0034-step11-4/verify-unattended.yaml` and retain the successful transcript.
8. Prefer one naturally timer-triggered cycle before final 11.4 close-out so the evidence demonstrates the scheduler, not only a manually started service plus an enabled timer.

**CLOSED 2026-10-15:** All eight live acceptance actions were demonstrated, including the naturally timer-triggered overnight cycle and the read-only cross-host verifier. See `STEP-11.4-UNATTENDED-ACCEPTANCE-CLOSEOUT-20261015.md` for Gate 6A–6E evidence, operational warning and corrected schedule. The 01:45 user cron timing has been deployed and shown idempotent, but its first unattended post-correction run is a follow-up observation. Step 11 and 0034-FEAT remain OPEN for their separate final reconciliation and feature closure.

## Rollback

Disable the three new application/replication timers before changing transport ownership. Scheduling rollback must not delete schema-2 generations, accepted receiver snapshots/receipts, the held checkpoint, the active parent, snapshot media, or production data. If the historical rsync push is reactivated, first disable the native push timer and verify exactly one off-site transport is active.

The `diaries-backup-history` configuration limitation observed in Step 11.3 (`verification.required=false`) remains explicitly deferred to **0035-FEAT**. Step 11.4 does not alter that configuration or claim a history-tool pass.
