# 0036-FEAT — Revised Step 2 design decision: fixed schema-2 working copies

**Decision date:** 2026-10-15  
**Status:** REVISED DESIGN FROZEN — Step 2 CLOSED at design level only.  
**Supersedes:** `evidence/Step 2/STEP-2-DESIGN-FREEZE-20261015.md` (original hard-link / rolling-generation decision). The original evidence remains preserved as historical, **not** the operative architecture.

## Intent

0036 is a physical storage/synchronisation optimisation, **not a change of the schema-2 logical backup format** and not a rewrite of 0034/0035. One current working backup is maintained on each of `pluto` and `mars`; read-only Btrfs snapshots, created frequently by the existing 0035 manager on `mars`, provide history and are pushed via existing Btrfs send/receive to `backup`.

## Target data flow

```text
pluto (ext4): consistent schema-2 capture -> fixed diaries-backup/ working dataset
      |           (incremental refresh; rsync --delete scoped to Files)
      |  mars initiates rsync pull (--delete)
      v
mars (Btrfs): fixed diaries-backup/ working dataset inside existing @data
      |   independently verify schema-2; mark eligible only after success
      |  0035 manager creates frequent timestamped read-only snapshots
      v
mars historical Btrfs snapshots -- mars-initiated btrfs send/receive --> backup
      0035 pruning on mars                             0035 pruning on backup
      protected parents / checkpoints / accepted receiver receipts retained
```

## Frozen decisions

1. Preserve `database/`, `files/`, `verification/`, `dataset-manifest.json` exactly as schema-2; retain logical dataset identity, backup IDs, database+Files consistency, integrity verification and restore compatibility.
2. `pluto` maintains one fixed current working dataset, updating Files incrementally rather than retaining multiple physical full-copy generations. PostgreSQL logical dumps continue to be generated consistently by the existing mechanism. Do not rsync a live PostgreSQL data directory.
3. `mars` initiates a changed-only `rsync --delete` into one existing mutable Btrfs working dataset. No nested new Btrfs subvolume outside the existing @data snapshot/send scope, and no assumption that Btrfs deduplicates separately copied identical files.
4. 0035 independently schedules frequent snapshots and progressively prunes on **both** `mars` and `backup` under the existing protection policy. These schedules and retention rules are inherited; 0036 does not alter them.
5. `mars` **pushes** timestamped Btrfs snapshot updates to `backup` using the existing 0034 send/receive machinery. Off-site receiver receipts, protected parents and held checkpoints remain in force.
6. Keep only lightweight safety interlocks: never pull a partially refreshed `pluto` dataset, never snapshot a partially updated `mars` working copy, and never mark an incomplete copy verified. Schedule separation is helpful but insufficient on its own. Implement with the smallest compatible existing lock/verified-marker mechanism, not complex generation retention/acknowledgement protocols.
7. The previous linked-generation publisher, ext4 hard-link optimisation, Btrfs reflink candidate system, per-generation receiver acknowledgement and dedicated `diaries-backup-maintenance:0036` image are **explicitly superseded**. Retain legacy 0034 implementation/rollback and restore support until an operator-approved migration and cleanup gate.
8. Preserve source-side read-only history and isolated recovery points throughout migration. An interrupted mutable rsync may leave partial data; the last read-only snapshot remains authoritative until successful verification and marker publication. `rsync --delete` must never target snapshots or inherited rollback media.
9. Quantitative changed-byte/storage-allocation measurements are useful 0036-specific acceptance evidence. Do not repeat 0034/0035 baseline inventories or already accepted end-to-end tests.

## Implementation questions to resolve within Steps 3–4

- Exact fixed working paths, ownership and source/pull interlock (without contradicting currently deployed 0034/0035 service paths).
- How `pluto` presents a consistent export while refreshing its Files and replacing dumps/manifest; schedule alone is inadequate for the correctness guarantee.
- How 0035 snapshot eligibility and verified markers are invalidated before a mutable pull and restored afterward.
- Safe incremental rsync options and metadata handling, preserving Btrfs extent sharing with older snapshots; never use `--inplace` on historical snapshots.

These are implementation details; no new 0035 scheduler or retention design is authorised.
