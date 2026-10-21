# Step 08 — Live read-only reconciliation

**Date:** 2026-10-19  
**Source:** `diaries-sources-20261019-213142.zip`, captured under `evidence/Step 08/` on Windows through Cygwin SSH to `mars`.  
**Scope:** baseline and advisory retention decisions only; not a deletion authorisation.

## Observations

- Host `mars`; `Etc/UTC`; Btrfs mounted at `/media/usb` from `/dev/sdb1`, subvolid 5.
- `root` Snapper config SUBVOLUME `/media/usb`; CSV contains only current entry 0 and no numbered legacy snapshots.
- `@data` Snapper config SUBVOLUME `/media/usb/@data`; CSV contains current entry 0 and 25 numbered legacy snapshots. Both paths agree with the native manager source paths reported by `native-status.txt`.
- Native manager: 57 complete coordinated timestamp sets, zero incomplete sets, 57 managed snapshots for each `root` and `@data`; 57 native keepers in the JSON plan.
- Native retention: 48 hourly, 14 daily, 12 weekly, 24 monthly, 5 yearly; minimum age 30 minutes.
- Diaries verification valid for logicalDataset `production`, backupId `20261019-003106Z`.
- Enabled timers: `btrfs-snapshot-create.timer`, `btrfs-snapshot-prune.timer`. Legacy Snapper timers are reported disabled. The `mars` native push timer is listed; no replication operation was exercised.

## Plan and inventory reconciliation

- Text and JSON list the same 25 `@data` numbered snapshots; the Snapper CSV contains precisely those same numbered IDs.
- JSON `mode=READ_ONLY`, `authorizes_deletion=false`; 17 KEEP, 8 WOULD-DELETE, zero EXCLUDED or BLOCKED entries.
- Advisory candidates: **19605, 19629, 19677, 19701, 19725, 19773, 19869, 19885**. IDs match the previously recorded Step 4 snapshot candidates; they must be recalculated before any future approval.
- Historical `@data` ID 1 (2024-05-26) is retained for monthly/yearly coverage; ID 5145 (2025-01-01) is retained for historical coverage; ID 19886 (2026-10-09 17:00:01 UTC) is explicitly retained as `LATEST_LEGACY_ANCHOR`.
- Nothing in this inventory establishes that a legacy `@data` snapshot substitutes for a coordinated native `root` + `@data` set. The algorithm keeps all 57 native sets.

## Boundaries and limitations

- `legacy-plan` checked the native protection state without error; output does not enumerate pin/hold record contents individually, so this is not an independent forensic audit of those records.
- The receiver layout issue documented in Step 1 remains outside this `mars` read-only preflight; no operations on `backup` or proof of new replication health were performed.
- This preflight did **not** run `legacy-delete`, prune, snapshot creation, Btrfs receive, or restore. It has not tested a live deletion, deletion-time race, or deploy of the new Step 6 deletion interface to `mars`.
- Any future destructive pilot requires a fresh plan, explicit per-ID operator acceptance and protected approval flow under subsequent steps.

**Decision:** Source inventory and advisory plan are consistent. Step 8 closure is justified for the limited read-only acceptance criteria.
