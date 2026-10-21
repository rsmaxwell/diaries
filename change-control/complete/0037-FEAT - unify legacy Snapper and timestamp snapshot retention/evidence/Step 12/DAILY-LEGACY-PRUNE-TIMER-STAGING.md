> **Historical staging record (superseded 2026-10-20):** original Step 12 scheduler acceptance is now CLOSED — PASSED; see `STEP12-SCHEDULER-FORMAL-CLOSURE.md`. This file records the pre-activation design and should not be used as current operating state.

# Step 12 — Daily legacy prune timer correction (2026-10-20)

Status: STAGED / NOT ACTIVATED.

The installed native `btrfs-snapshot-prune.timer` uses `OnCalendar=*-*-* *:15:00` (hourly). Therefore the earlier plan to append a legacy-prune ExecStart to its service was unsafe: `--max-delete 1` limits deletions per invocation, not per day.

Playbooks correction package: `0037-FEAT-step12-daily-legacy-timer-playbooks-20261020.zip`.

- Native service template now has only `prune`; its hourly timer is unchanged.
- New `btrfs-legacy-prune.service` runs guarded `legacy-prune ... --max-delete 1 --execute` using configured `root=root` and `@data=@data` mapping.
- New `btrfs-legacy-prune.timer` runs `08:20:00 UTC` daily and uses `Persistent=true`.
- `btrfs_snapshot_unattended_legacy_prune_enabled` defaults to false; the role stops/disables the new timer by default.
- The opt-in is rejected unless native activation and retired Snapper scheduling are configured; deletion limit is restricted to one.

Source checks passed in isolated source tree: verify-unattended-legacy-prune.py, verify-legacy-prune-preview.py, verify-qgroup-status.py, verify-btrfs-snapshot-manager.py. These tests do not constitute live scheduler acceptance.

Before production activation:
1. Apply source package to Playbooks repository and run regressions on mango.
2. Deploy the role with opt-in **false**; inspect `systemctl cat btrfs-snapshot-prune.service`, `btrfs-legacy-prune.service`, and their timers; verify old Snapper cleanup/timeline/boot timers disabled.
3. Verify `legacy-prune` read-only plan, native holds, replication pin, and the installation status of both timers.
4. Verify calendar with `systemd-analyze calendar '*-*-* 08:20:00 UTC'` and the actual installed timer schedule; check boot catch-up implications of `Persistent=true`.
5. Only then explicitly set host override `btrfs_snapshot_unattended_legacy_prune_enabled: true` for mars and rerun the snapshot role. Check the journal after its first scheduled run. Do not manually start the legacy service as a test: that deletes a live snapshot.
6. Rollback: set opt-in false and rerun role, or `sudo systemctl disable --now btrfs-legacy-prune.timer`; leave native hourly prune untouched.

Baseline (2026-10-20): legacy read-only preview selected ID 19629 (8 eligible); native dry-run 58 complete sets / 0 deletions; two holds and replication pin preserved. No legacy timer has been activated by packaging this change.
