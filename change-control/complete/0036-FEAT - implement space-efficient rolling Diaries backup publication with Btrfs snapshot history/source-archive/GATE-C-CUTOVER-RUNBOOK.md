# 0036-FEAT Step 8 Gate C — Controlled production cutover (operator runbook)

**Status: PREPARED, NOT EXECUTED.** Retain Gate B rollback evidence and snapshot `20261016-030037Z` with verified off-site receipt. Changes below must be performed under a controlled maintenance window; do not run commands in a single unattended batch. No Docker image rebuild required.

## Blocking source and deployment checks

1. Deploy the new `diaries-pull.sh.j2` opt-in code to Playbooks; keep `diaries_pull_fixed_destination_enabled: false` initially. Validate the installed `mars` pull script and installed `pluto` fixed capture, including the location of the installed source guard. **Do not assume the default guard path exists:** determine it on `pluto` before setting `diaries_pull_fixed_source_guard`.
2. Confirm whether the live `pluto` complete-backup service still calls `publish`, as the uploaded source does. The fixed path is selected by `backup fixed-capture`, NOT by merely setting `DIARIES_0036_FIXED_CAPTURE_ENABLED=true`. The timer service must be deliberately reconfigured after manual acceptance, never before.
3. Confirm actual runtime env and deployed script paths, PostgreSQL environment, `DIARIES_0036_HOST_MOUNT_ROOT=/mnt/nas-diaries`, correct host Files selector and identity. Keep secrets out of logs.
4. Record `git status --short` and current committed revision of both repos. Back up all affected unit files, scripts, environment entries **without exposing secrets**, and record hashes. Gate B recorded previously installed unit hashes.
5. Verify checkpoint `20261016-030037Z` remains read-only and off-site receipt `/@data/mars-received/.replication-state/20261016-030037Z.json` still valid. Preserve old generations and snapshot pinning.
6. Run the read-only precheck on each host and record symlink target *again*, because daily jobs may have moved them.

## Maintenance sequence (separate operator approvals)

A. Disable *and stop timers*, not active services, for `diaries-complete-backup-publish.timer` on `pluto`, and `diaries-pull.timer`, `btrfs-snapshot-create.timer`, `btrfs-snapshot-prune.timer`, `btrfs-native-push.timer` on `mars`. Check `systemctl is-active` on **services** and any other writers; do not cut over during an active job. Preserve recorded enablement status for rollback. A disabled timer is not proof that its service has stopped.

B. Preserve exact existing symlinks under a dated rollback name in the same parent on each host, using `mv -T` only after verifying that the rollback name does not exist and the source still matches the recorded generation. Do not move or delete `.diaries-backup-generations`; do not copy entire generations unnecessarily. Do not rename the whole `@data` Btrfs subvolume.

C. Create new `diaries-backup/` real directories on both hosts, owned by `richard`, after the original symlinks have been safely preserved. On `mars` the target must remain within `/media/usb/@data` and share the existing marker/lock contract. Do not copy old publisher marker as acceptance of new data.

D. Set `DIARIES_0036_FIXED_CAPTURE_ENABLED=true` plus the validated host Files root, mount and identity variables in the secured `pluto` runtime environment. Run `production-complete-dataset.py backup fixed-capture-preflight`; confirm that it performs no writes. Run **one manually initiated** `backup fixed-capture` while the legacy publisher timer is disabled. Independently verify its schema-2 manifest and the source acceptance marker. On failure, preserve logs, keep timers disabled, and roll back; responder may deliberately remain stopped as a fail-closed contract.

E. Set `diaries_pull_fixed_destination_enabled: true` and the **verified absolute installed guard path** in Playbooks and deploy only the `mars` local-backup pull scripts, without enabling the timer. Run `diaries-pull.sh --preflight` and manually `diaries-pull.sh`; confirm independent schema-2 verification and that snapshot eligibility marker refers to the fixed real directory. On failure, leave snapshot and off-site timers disabled and roll back.

F. Manually request a verified timestamped read-only `mars` snapshot and check its manifest/history/restore-stage. A successful fixed receive alone does NOT authorise removal of old snapshots or generations. Restore timers *only after* evaluating the source/pull schedule separation, especially the GMT change 2026-10-25. A dependable completion dependency is preferable; otherwise configure non-overlapping UTC times with margin. Gate D must observe at least two unattended complete cycles and an accepted off-site receipt before retirement.

## Rollback (only while writers stopped)

1. Stop/disable new fixed capture/pull schedules and verify no capture/pull/snapshot/push services are running. Preserve failed fixed directories under new, explicitly unique diagnostic names; never overwrite a saved legacy symlink.
2. Restore each original publication symlink to exactly its recorded path, with its preserved generation directory intact. Restore recorded original unit files/env/script configs and `systemctl daemon-reload`; revalidate the legacy publish/pull preflights.
3. **Do not reuse a new fixed-destination eligibility marker with a restored legacy publication.** Restore the old accepted marker *only after* independent validation of the restored legacy generation against the 0035 contract; otherwise leave snapshot timer disabled until a verified legacy receive republishes marker.
4. Re-enable legacy timers in the original order after a successful legacy verification; keep old snapshots and off-site receipts. Record reason, actions, timestamps and hashes.

## Gate C evidence required

Pre/post symlink `readlink` and `stat`; service/timer states and unit hashes; fixed capture preflight and real capture exit/status; guarded receive exit/status; manifest, source marker and `mars` eligibility contents; snapshot read-only and history validation; exact deployed code/env revisions; rollback readiness; scheduling change. **Do not mark Gate C closed on source checks alone.**
