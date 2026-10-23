# Step 01 — Read-only baseline

**Status: CLOSED — 23 October 2026.** This replaces the obsolete placeholder “OPEN — NOT EXECUTED.” The controlling acceptance record is `../../reports/STEP01-BASELINE-PROGRESS.md` and the Step 1 closure decision in `../../IMPLEMENTATION-STEPS.md`.

## Evidence accepted

- Source revisions recorded: Diaries `f01bd76a6d5fbb42bb90979d9d13857b9b8aa4be`; Playbooks `0d487706518fa73bf621545906f3deea97bce9b2` at original baseline. `mars` manager SHA mismatch attributed to 0039-DEF qgroup parser update and deferred for controlled reconciliation.
- `mars`: existing native source snapshots and source pin/holds/lock contract reviewed; active legacy @data Snapper prune and 08:20 UTC timer identified; root snapshot population and negligible placeholder contents examined.
- `backup`: 19 read-only received snapshots, associated receipt identities and writer lock reviewed; latest lineage through `20261023-030037Z`. Original 0040 baseline identified separate legacy trees (`/@data/backup`, `/@data/.snapshots`, `/.snapshots`, unused ` /@snapshots` tree) and Snapper APT integration.
- Kernel, btrfs-progs, filesystem/qgroup counts, capacity and relevant schedules recorded in the Step 1 report. Cumulative `du` figures are *not* treated as reclaimable space.
- Exact subvolume deletion identifiers intentionally deferred to Step 10 for a fresh pre-destructive inventory.

## Acceptance / scope

Baseline reconciliation accepted **read-only**, without authorising snapshot deletion, timer changes or a full restore. The original underlying terminal capture files are not embedded in this index; consult the existing Step 1 evidence and source report for the evidence trail, and archive raw console captures separately if required.
