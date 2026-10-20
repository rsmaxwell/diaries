# Step 11 — Operational check and single-pilot GO decision

**Source:** `diaries-sources-20261020-085718.zip`; captured `mars` 2026-10-20 07:56:49 UTC. `operational-check/SHA256SUMS.txt` matches `mars-operational.txt` (checked independently).

**Decision: GO for exactly one guarded pilot, `mars` / `@data` / `19605`, subject to same-session STOP checks in the execution runbook.** This is not evidence that deletion has run.

- `snapper-timeline.service` failed at 2026-10-09 17:00:02 UTC, well before today's preflight; the prior error is stale.
- `snapper-timeline.timer` and `snapper-cleanup.timer` are both `disabled` and `inactive`.
- No active matching Snapper maintenance, Btrfs send/receive, snapshot-manager, or diaries pull/push process appeared in the captured process list other than the read-only diagnostic command itself.
- Native `btrfs-snapshot-create.timer` and `btrfs-snapshot-prune.timer` are active, scheduled for 08:00 and 08:15 UTC respectively, so recheck for active work immediately before the pilot; do not run during a timer job.
- The historical Step 11 preflight at 07:40–07:47 UTC matched subvolume ID `20165`, UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`, `ro=true`, and `WOULD-DELETE`; source/receiver holds and pins were intact. These must be revalidated at execution time.
- `diaries-pull.timer` displayed 01:30 UTC in the capture, whereas the previously agreed schedule is 01:45 UTC. Treat this as a separate configuration discrepancy to reconcile; it is not proof of a competing process during the pilot.

**Recovery caveat:** receiver presence and receipts do not substitute for a tested restore; the earlier Step 10 operator acceptance accepted that evidentiary limit. **Only one ID is authorised.** No other legacy deletion, timer enablement, or policy extension is allowed.

If an identity, timer, process, hold, pin, or receiver check differs unexpectedly, stop and record **NO-GO**. Post-pilot verification and evidence are mandatory before declaring Step 11 closed.
