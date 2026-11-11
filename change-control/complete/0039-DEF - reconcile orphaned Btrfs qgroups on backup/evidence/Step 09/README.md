# Step 9 — Shared cleanup implementation — CLOSED (10 November 2026)

22 source regressions passed and the same installed `btrfs-clear-stale-qgroups` code was validated in read-only mode on both `mars` and `backup`. The corrected real-host run on 9 November 22:58 UTC removed 95 eligible stale entries on `mars` and deferred eight whose IDs precisely matched pending deleted subvolumes; service result was success, with no unexpected unmatched/orphan entry. Before/after snapshot counts were 69 and production verification remained valid.

`raw-terminal/` contains verbatim uploaded terminal transcripts of the diagnostic and deployment sequence, including the earlier unsuccessful native cleanup, quota rescan and 20-minute deletion-sync timeout. **Historical failures remain failures**; the later accepted execution and fixed code do not rewrite those records.

See `../../reports/STEP08-10-ACCEPTANCE-RECONCILIATION-20261110.md`. The remaining Step 11 gate is repeat unattended behaviour, not another manually triggered cleanup.
