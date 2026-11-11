# Step 01 accepted baseline evidence — CLOSED 2026-10-21

Source: user-supplied terminal captures on 2026-10-21.

| Evidence | Observation |
|---|---|
| `note(20261021-075633).txt` | Large qgroup output with numerous `0.00B` entries; selected nonzero entry `0/55805` references 325.63 GiB, exclusive 45.48 MiB |
| `note(20261021-080412).txt` | `sudo btrfs subvolume list / | wc -l` = **133** |
| `note(20261021-080412).txt` | qgroups **29,571**; zero **29,437**; nonzero **134** |
| `note(20261021-080412).txt` | `btrfs-progs v5.16.2`; kernel **5.15.0-164-generic** |
| `note(20261021-080412).txt` | `btrfs quota status` not a recognized command on host; no quota-health inference |
| 0038 accepted verification | `backup` off-site incremental receive/receipt and read-only received snapshots verified separately; no later verification in this defect yet |

**Inference, not fact:** many level-0 qgroups may be left from deleted subvolumes; matching row counts (133 versus 134 nonzero) are suggestive but not proof. Zero-valued records must be cross-checked with IDs and deletion status.

**Step 01 CLOSED (2026-10-21):** read-only ID comparisons, usage/limits/relationship counts, pending-deletion query and rescan-state check accepted. No mutation performed. Refer to Step 02 findings for analysis still in progress.

## Step 01 additional accepted results
| Evidence | Observation |
|---|---|
| `note(20261021-081546).txt` | 133 listed subvolume IDs all matched; 29,438 unmatched qgroup IDs before allowing top-level ID 5; **29,437** remaining candidates |
| `note(20261021-081652).txt` | No pending deleted subvolumes; no rescan running; sample obsolete zero-sized qgroups with 1.00TiB limits |
| `note(20261021-081914).txt` | 134 existing qgroups including ID 5; **29,437 unmatched, all zero-sized; 13,962 with limits; 0 relationships; 0 with nonzero usage** |
| `note(20261021-082042).txt` | `backup` 1.9 TB filesystem, 1.6 TB used, 297 GB available (84%); Snapper configs `QGROUP=""` |

**Acceptance:** Sufficient identity and state inventory for design investigation; stale classification still cannot automatically justify destruction.
