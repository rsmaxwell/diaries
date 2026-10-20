# 0037-FEAT — Step 14 final reconciliation and closure gate

**Status: IN PROGRESS — final reconciliation; feature not yet marked COMPLETE.** Prepared 20 October 2026 from the newest uploaded Diaries and Playbooks source bundles and the operator's final full-playbook run. Step 13 remains formally CLOSED. This record does not authorise any snapshot deletion, restore, backup transfer or service restart.

## Acceptance matrix

| Implementation scope | Evidence / result | Decision |
| --- | --- | --- |
| Steps 1–3: baseline, scope, compatibility and combined selection design | Existing implementation plan and Step 1–3 records | Accepted previously |
| Step 4 read-only inventory / plan | Step 4 formal closure and reconciliation | Accepted previously |
| Step 5 adversarial planner regressions | Step 5 evidence; 20/20 tests | Accepted previously |
| Step 6 guarded deletion | Step 6 formal closure; 14/14 tests | Accepted previously |
| Step 7 source / integration regressions | Step 7 formal closure | Accepted previously |
| Step 8 live read-only preflight | Step 8 formal closure | Accepted previously |
| Steps 9–10 staged deployment / operator gate | Step 9 and Step 10 evidence | Accepted previously |
| Step 11 controlled pilot | Step 11 formal closure | Accepted previously |
| Step 12 scheduler and rollback | Step 12 scheduler formal closure; supplemental stale-qgroup records | Accepted previously |
| Step 13 documentation / deployment / housekeeping | Step 13 formal closure, `full-playbook-idempotent.txt` | CLOSED — remains closed |
| Step 14 post-cleanup Playbooks idempotency | 2026-10-20 operator log `note(20261020-174838).txt`: `ok=64 changed=0 failed=0 skipped=16` | PASS |
| Step 14 legacy root-helper retirement | Prior controlled real run followed by repeat `changed=0`; latest source no longer contains one-time cleanup task/variable | PASS, subject to independent final host confirmation |
| Step 14 final Git revision and clean source promotion | Both repositories' HEAD and `git status` not in latest execution log | OPEN |
| Step 14 move feature into `change-control/complete/` | Must follow final source acceptance | NOT YET AUTHORISED |

## Final host runtime evidence — 2026-10-20

`./scripts/local-backup.sh` on mango targeting mars succeeded after the obsolete cleanup code was retired: **64 OK, 0 changed, 0 failed, 0 unreachable, 16 skipped**. `btrfs-snapshot-manager status` showed `snapshot_root=/media/usb/@snapshots`, `complete_timestamp_sets=59`, `incomplete_timestamp_sets=0`, `qgroups_stale=10`, `qgroups_under_deletion=0`, `qgroups_status=ok`, and `diaries_verification=valid; logicalDataset=production; backupId=20261020-003106Z`. Snapshot manager, independent schema-2 verifier and systemd unit tasks were all `ok`. This confirms deployment idempotency, *not* a new full restore or independent off-site receipt audit.

The earlier cleanup-specific execution log showed a real guarded removal of `/root/scripts/backup/diaries-pull.py`, `/root/scripts/backup/complete-dataset-publisher.py` and `/root/scripts/backup/complete-dataset-manifest.py`, followed by `changed=0`. New Playbooks source omits that one-time task, its opt-in setting, and corresponding test references. The `getent` and `normal_user_home` prerequisite tasks remain tagged `always`.

## Outstanding final read-only acceptance checks

1. Record `git rev-parse HEAD`, `git status --short`, and `git diff --check` for both the Diaries repository and Playbooks repository. Distinguish intentional uncommitted changes from unsupported assumptions of committed promotion. Capture any outstanding deletion of older 0034/0036 documents separately; do not treat it as 0037 acceptance merely because it appears in the same Git diff.
2. Confirm the three retired root-owned pilot files are absent on mars; confirm current user-owned scripts exist and timers remain enabled. Do not delete anything automatically.
3. Inspect the feature's scratch/report directories, temporary captures on mango/mars/backup, and all pending Git deletions. Keep test and evidence records even when temporary. Do not move/delete unreviewed material.
4. Decide whether the optional deferred read-only Snapper performance check and historical receiver diagnostics remain explicitly excluded. Do not require extra restore or transfer measurement without a new acceptance decision.
5. Confirm evidence/documentation contains no credentials or unnecessary large files; record final Git revision(s).
6. **Only after sign-off**, change status to COMPLETE and relocate the entire feature directory from `change-control/in-progress/` to `change-control/complete/` preserving evidence history. Use `git mv` after both repositories' intended changes have been reconciled; adjust inbound links if necessary.

## Decision

**Step 14 opened; not yet formally closed.** The production functional gate passes. Outstanding close-out is Git/state/evidence inventory and deliberate feature-directory relocation. The existing Step 13 formal closure is not reopened.
