# 0037-FEAT — Step 12 scheduler acceptance and rollback: FORMAL CLOSURE

**Decision: CLOSED — PASSED, 2026-10-20.**

This is **original implementation-plan Step 12**, not the separately closed supplemental Step 12 Btrfs stale-qgroup cleanup (`STEP12-RECONCILIATION-AND-CLOSURE.md`). Step 13 production documentation/housekeeping and Step 14 feature reconciliation remain OPEN.

## Accepted production configuration (`mars`)

| Control | Accepted state |
| --- | --- |
| Permanent deployment entry point | `local-backup.yaml --limit mars --tags legacy-prune-units` |
| New service | `btrfs-legacy-prune.service`, guarded `legacy-prune --legacy-map root=root --legacy-map @data=@data --max-delete 1 --execute` |
| New timer | `btrfs-legacy-prune.timer`, daily `*-*-* 08:20:00 UTC`, `Persistent=true`; enabled and active |
| Native prune | `btrfs-snapshot-prune.timer`, hourly `*-*-* *:15:00`, enabled and active |
| Obsolete Snapper timeline/cleanup timers | Disabled in prior checks; no parallel legacy scheduler authorized |
| Host opt-in | `/etc/ansible/host_vars/mars/backup.yaml`: `btrfs_snapshot_unattended_legacy_prune_enabled: true`, `btrfs_snapshot_unattended_legacy_prune_max_delete: 1`, native activation true and legacy timers retired true |
| Deploy safety | First-install `--check --diff` passed; actual installation passed; repeat run yielded `changed=0`; final activation dry run passed, actual activation `changed=1` |

The permanent role and Playbooks inventory are the source of truth. No temporary staging playbook is required. The focused tag avoided unrelated changes to `/usr/local/lib/diaries-backup/complete-dataset-manifest.py`.

## Observed systemd deletion results (20 October 2026, UTC)

| Start–finish | Legacy Snapper config / ID | Subvolume ID | UUID | Exit |
| --- | --- | --- | --- | --- |
| 15:41:49–15:41:54 | `@data` / `19629` | `20189` | `d8dd07a1-c5bb-fd46-8ca7-442add43653d` | `0/SUCCESS` |
| 15:43:08–15:43:13 | `@data` / `19677` | `20237` | `42698393-7fbd-b74f-ae68-f06028fcda9c` | `0/SUCCESS` |

Each invocation performed exactly **one** eligible guarded deletion; its retention plan was recalculated independently (candidate counts 8 then 7). Two actual executions occurred; do **not** describe the result as only one deletion or as one deletion per calendar day. Subsequent preview: **6** eligible legacy candidates, next `19701`, **no further deletion authorised by the preview**. The two observed service executions exited successfully and systemd marked them deactivated successfully.

## Post-execution protections and service state

- `complete_timestamp_sets=58;incomplete_timestamp_sets=0`; root and `@data` each report 58 managed sets.
- `diaries_verification=valid;logicalDataset=production;backupId=20261020-003106Z`.
- Held checkpoints `20261013-171228Z`, `20261018-165453Z` remain present. Earlier verification of replication pin `20261020-030026Z` and independent backup receiver remains the recovery baseline; receiver transfer/restore was **not repeated** during Step 12.
- `qgroups_total=151`, `qgroups_stale=8`, `qgroups_under_deletion=0`, `qgroups_status=ok`; stale metadata count rose by two after the two deletions.
- Final timer verification: legacy and native prune timers **enabled / active**; next legacy scheduled run `Wed 2026-10-21 08:20:00 UTC`.

## Scheduling, limits and outstanding observations

`--max-delete 1` limits **one deletion per execution**, not one per day. Normal unattended frequency is supplied by the separately scheduled daily timer. A manual `systemctl start btrfs-legacy-prune.service` can initiate another eligible deletion and does **not** reset the timer.

The first **natural** daily timer-triggered execution has not yet been observed; acceptance relies on timer configuration/active state and two successful live runs of the exact installed oneshot service. Calendar-trigger proof may be gathered as routine unattended evidence without reopening Step 12 unless it reveals a defect. No additional full transfer or restore was requested.

## Rollback and recovery boundary

Immediately stop future unattended legacy pruning with `sudo systemctl disable --now btrfs-legacy-prune.timer`. For durable rollback, change the `mars` inventory `btrfs_snapshot_unattended_legacy_prune_enabled` to Boolean `false` and rerun `local-backup.yaml --limit mars --tags legacy-prune-units`. Preserve native creation and hourly prune services/timers. **This cannot restore deleted snapshots.** Review journal, retained anchors, backup receiver receipts and recovery options if any unexpected deletion is discovered.

## Operator evidence and scope

- `scheduler-acceptance/operator-systemd-execution.txt` — verbatim two-execution systemd transcript and post-state.
- `scheduler-acceptance/operator-final-timers.txt` — verbatim final enabled/active timer checks.
- `scheduler-acceptance/SHA256SUMS.txt` — preserved transcript digests.
- Earlier operator logs in the conversation recorded repeat-run `changed=0`, activation `changed=1`, live read-only preview, qgroup and retention state. The latter Ansible outputs are **summarized** here and are not claimed to be attached verbatim.
- Earlier receiver preflight remains filed under `evidence/Step 10/`; original guarded one-ID pilot under `evidence/Step 11/`.

**Formal closure:** Step 12 **CLOSED — PASSED**. Step 13 **NEXT**. Overall feature **OPEN**.
