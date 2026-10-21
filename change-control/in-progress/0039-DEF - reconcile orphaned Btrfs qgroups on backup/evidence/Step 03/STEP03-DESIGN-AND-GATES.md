# Step 03 — Remediation safety design and acceptance gates

**Status:** IN PROGRESS (design only; no production mutation).

## Decision and boundaries

Construct a bounded, reproducible **read-only** qgroup-to-subvolume inventory on each Btrfs filesystem, independent of whether installed btrfs-progs prints `<stale>`. Preserve source/receiver read-only flags, received UUIDs, replication parentage and `.replication-state` receipts, operator holds, timers and retention. A zero-use qgroup is *never by itself* sufficient approval for destruction.

## Required inventory design

1. Freeze filesystem identity, mountpoint, Btrfs version, kernel, quota rescan state, root subvol ID 5 and all live subvolume IDs; detect enumeration errors and concurrent changes.
2. Enumerate level-0 and higher qgroups with limits, usage, parent/child relationships and command-version header; compare **IDs**, not zero usage or string markers. Classify `active`, `unmatched candidate`, `related/protected`, and `ambiguous`.
3. Verify candidate exclusion of active/received subvolumes, pending deletes, parent-child links, valid limits and changing inventory; emit machine-readable bounded summary plus deterministic fingerprint and human review sample.
4. Create regression fixtures for btrfs-progs 5.16.2 and 6.6.3, 30k+ qgroups, ambiguous columns, failing commands, interrupted reads and concurrent-change detection. Tests must not mutate real filesystem state.

## Remediation options to evaluate (none authorised)

- **Observe only** with trend and operational monitoring if risk remains tolerable.
- **Individually verified qgroup cleanup** only if a supported installed command safely applies to proven candidates, with explicit single/bounded approval and revalidation immediately before mutation; no bulk inferred deletion.
- **Distribution-managed OS/Btrfs upgrades** as separately approved maintenance: backup 22.04 → 24.04 first, mars already 24.04; consider newer supported versions only on their merits, not as a proven cure. Ensure remote console, boot fallback and recovery tests.
- Never use quota disable/re-enable, rescan, unapproved qgroup destroy, filesystem repair or forced pruning as an exploratory test.

## Acceptance gate to proceed beyond design

Require precise proposed commands and installed-version semantics; receiver dataset/receipt and UUID invariants; qgroup relationship/limit safety; pre/post fingerprint, bounded batch size and stop conditions; backup-space and runtime risk; credible rollback/recovery **limitations** (quota metadata operations are not necessarily reversible); independent operator approval.

**Immediate next execution stage:** inspect qgroup and subvolume commands and source options on `mango` against accepted code; then implement the read-only inventory and isolated regression tests. Do not run a destructive command on `mars` or `backup`.
