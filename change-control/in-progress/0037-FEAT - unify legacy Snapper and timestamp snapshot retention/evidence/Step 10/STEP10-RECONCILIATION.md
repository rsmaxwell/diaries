# Step 10 — Fresh preflight reconciliation (2026-10-20)

**Result:** Local technical preflight PASS; **operator acceptance OPEN / pilot deletion not authorised**.

## Evidence examined

Source: `diaries-sources-20261020-075134.zip`, `evidence/Step 10/fresh-preflight/`. Capture timestamp: `2026-10-20T06:44:37Z` on `mars` (Etc/UTC). Text and JSON plans agree (25 legacy `@data` entries: 16 KEEP, 9 WOULD-DELETE). All 58 native paired sets are complete and retained; 0 incomplete. Latest native manager SHA-256: `3eb8717fdb06410943a2e9513dfc5f3e8b6892021bac0d741b58e2524bdff671`.

The nine advisory IDs are: `19605`, `19629`, `19677`, `19701`, `19725`, `19773`, `19797`, `19869`, `19885`. ID `19797` changed from KEEP in the 2026-10-19 baseline to WOULD-DELETE in the fresh plan; this is consistent with advancing native daily coverage, but the plan must be regenerated immediately before a pilot.

## Proposed pilot: @data / 19605

- Plan decision `WOULD-DELETE`; created `2026-09-28 00:00:38 +0000`.
- Snapshot path `/media/usb/@data/.snapshots/19605/snapshot`.
- Btrfs subvolume ID `20165`, UUID `489332dc-3b48-eb40-b59a-d9bd86cc9915`, `ro=true`, flag `readonly`.
- Exclusive usage reported `398.66 MiB` (not a deletion space-saving guarantee).
- Latest legacy recovery anchor `19886` remains KEEP; historical 2024/2025 monthly/yearly snapshots remain KEEP.

## Other safeguards

- Native prune dry run: `RETENTION sets: total=58 keep=58 sources=2`, zero proposed deletions.
- Checkpoint holds: `20261013-171228Z`, `20261018-165453Z`.
- Replication pin: `20261020-030026Z`.
- Native creation and pruning timers enabled; associated services inactive/dead when inspected (normal outside activation).
- No matching current jobs in captured process listing; this is a point-in-time observation only.
- Dataset verification marker reported valid, backup ID `20261020-003106Z`.
- Legacy deletion remains explicit-only: the planner reports `authorizes_deletion=false`.

## Unresolved acceptance conditions

1. Independently validate *current* `mars → backup` receipt/parent health and usable recovery path. Earlier `backup` manager diagnostic had an obsolete parent-path discrepancy; the Step 10 mars-only capture does not resolve it.
2. Obtain an explicit operator decision to APPROVE or REJECT **only `@data` snapshot 19605** for a later one-ID pilot. Approval is not inferred from proceeding with this document.
3. Immediately before any pilot, recheck candidate identity and fresh plan, idle services, replication pins/holds and confirmation of safe recovery; stop if anything differs or cannot be verified.
4. Record Step 11 stop conditions, post-delete Snapper inventory and native status checks, and the one-way nature of deletion: restoring a deleted snapshot may require surviving backup copies, not reversal of the Snapper command.

**Decision:** PENDING. Do not create an approval file or invoke `legacy-delete --execute` as a consequence of this review.
