# 0036-FEAT — Implement space-efficient rolling Diaries backup publication with Btrfs snapshot history

**Status:** PROPOSED / NOT IMPLEMENTED  
**Created:** 2026-10-14  
**Dependencies:** Close 0034-FEAT and 0035-FEAT, retain their evidence and operational baselines before beginning disruptive work.  
**Repositories:** `diaries-application/diaries` (publisher and verified pull contracts); `playbooks` (deployment, schedules and snapshot integration).

## Problem and intent

Production `pluto` uses ext4 and currently retains timestamped full backup generations below `data/dataset-backups/production/`, each containing `database/`, `files/`, `verification/`, and `dataset-manifest.json`. Identical photographs are copied into each generation. `mars` uses Btrfs and captures timestamped snapshots, but separate full-copy generations imported into distinct paths are not automatically deduplicated merely because they have equal content. Hourly snapshots of those generations share extents *within the snapshot lineage*, not necessarily across separately imported full copies.

**Goal:** Maintain one *rolling current* logical Diaries backup dataset on `pluto` at a stable publication path, and one *rolling current* dataset on `mars` whose unchanged files keep their extents. Historical recovery points are provided by retained, independently verifiable timestamped Btrfs snapshots (and by off-site Btrfs send/receive), not repeated full-copy backup directories. New IDs, manifests, database dumps and other changing metadata remain legitimate changes.

This is a **storage-layout and publication-transaction change**, not a request to weaken the schema-2 backup/restore contract.

## Boundaries and non-goals

- Do not alter running production systems or enable new schedules as part of feature creation. Keep 0034/0035 functioning unchanged until explicitly cut over.
- Preserve schema-2 layout and correctness: `diaries-backup/database/{diaries.dump,diaries.sql}`, `files/`, `verification/`, `dataset-manifest.json`; preserve quiescence, hashing, logical dataset isolation, completeness checks, restore tools and history usability.
- Keep **pluto ext4 → mars Btrfs → backup Btrfs**, with `mars` initiating the pull and the off-site native Btrfs push. No new inbound home-network dependency.
- Avoid assuming Btrfs automatically deduplicates unrelated files. Reuse extents by **not rewriting unchanged files** in the rolling Btrfs tree; use reflink snapshots/worktrees as needed.
- Do not mix the independently verified backup ID (logical generation) with the Btrfs snapshot timestamp (physical recovery point).
- Do not silently change protection, pruning, native send/receive parent rules, checkpoint holds or historical recovery compatibility.

## Target logical and physical model

```text
pluto (ext4)
  .../dataset-backups/production/
    diaries-backup/                  <- single stable published schema-2 tree
      database/
      files/
      verification/
      dataset-manifest.json
    .publication-work/              <- private temporary construction, crash cleanup
    .publication-state/             <- latest publication journal/receipts
  (no accumulated full photo copies under timestamped generations after migration)
            |
            | mars-initiated verified rsync/pull, stable paths, changed files only
            v
mars (Btrfs)
  /media/usb/@data/backup/.../diaries-backup/   <- canonical rolling accepted logical tree
  /media/usb/@snapshots/@data/<timestamp>/      <- immutable historical recovery points
            |
            | existing protected native incremental Btrfs send/receive
            v
backup (Btrfs)
  /@data/mars-received/@data/<timestamp>/       <- read-only received snapshot sets
  /@data/mars-received/.replication-state/      <- acceptance receipts
```

**These paths are a logical illustration, not authority to create/delete directories.** Confirm actual deployment paths, symlinks and snapshot/subvolume boundaries from runtime inventory and source code in Step 1 before implementing. Keep the existing external fixed-path `diaries-backup` contract for consumers.

## Critical transaction design

**On ext4 `pluto`:** rsync/compare against the previous published `files/` and avoid recopying unchanged photos into the working publication; however, atomic replacement of an entire populated directory is not a single ordinary POSIX `rename`. Specify and test an actual commit protocol: isolated working publication, a stable indirection (`diaries-backup` symlink or equivalent), durable verification/manifest, atomic rename of the indirection, and retention of the previous target until publication and at least one receiver acknowledgement. This may temporarily require duplicate file trees on ext4; space is reclaimed after safe cutover and rollback window. Never expose a half-written tree as published. The transient use of hard links for unchanged *immutable* photos is permissible only after proving no source or staging writer can mutate linked inodes; otherwise use selective copying. Do not use hard links for changing database dumps or metadata. Revisit the old per-generation naming only as an internal bounded staging/rollback mechanism.

**On Btrfs `mars`:** the authoritative accepted state must survive a failed sync or verification. Construct a transactionally isolated writable candidate (prefer a writable Btrfs snapshot/reflink clone of the last accepted working tree), apply changed files using rsync preserving untouched files (and appropriate delete handling), independently verify schema-2 consistency and manifest, then atomically promote the candidate by a proven pointer/transaction protocol. Maintain one current accepted logical state and a bounded transient candidate, not unbounded full-copy generations. The approved immutable timestamp snapshot is the durable historical version. Do not use `rsync --inplace` against data shared by historical snapshots; do not make mutable changes to any read-only snapshot or native send parent. Carefully scope `--delete` to the intended candidate `files/` tree, excluding receipts/locks and repositories. Avoid timestamp-only rsync false negatives by selecting an explicit policy for content verification (checksums/size/mtime and manifest verification).

**Publication handshake and crash safety:** define source backup ID and monotonic acceptance, manifest digest, verified-marker identity, current pointer, receiver acknowledgement and journal phases. Handle a crash before verification, during transfer, after verification and before pointer switch, after switch but before receipt, and during cleanup. Retrying identical backup IDs must be idempotent; conflicting same-ID content and rollback IDs must fail closed unless intentionally authorised. The previous accepted state and held checkpoints must remain recoverable at every phase.

**History and replication:** map logical backup IDs to the retained timestamp snapshots that contain each version; verify historical restore using snapshot paths, not vanished ext4 generation directories. Preserve the native Btrfs sender/receiver parent UUID lineage and protected replication source snapshots. Confirm that creating/replacing the rolling data tree does not move it outside the existing sent `@data` subvolume or create nested subvolumes silently excluded by snapshot/send.

## Storage-efficiency acceptance (measured, not assumed)

1. Two consecutive backups of unchanged photograph files result in **one** current published dataset on `pluto`, plus strictly bounded temporary/rollback staging; no indefinite timestamped full copies.
2. `mars` accepts a second logical backup with changed ID/metadata but unchanged photo content **without allocating new full-size photo extents**. Prove with representative file extent inspection and Btrfs exclusive/shared usage (not just apparent `du` values); tolerate small metadata/database differences.
3. Changed/additional/deleted files are reflected in the new verified current state, while the earlier read-only Btrfs snapshot restores the prior values, including deleted files.
4. At least two accepted logical generations and their snapshot-based history can be located and restored using unchanged schema-2 restore semantics.
5. A corrupt manifest, partial pull, power interruption or rollback attempt cannot replace the last accepted generation or break protected replication parents.
6. Existing `mars → backup` incremental send/receive completes after rolling publication, with accepted receipt, matching UUID/received UUID, and successful disposable off-site restore.
7. Storage consumption and network transferred bytes are measured before/after, with no claim of automatic Btrfs deduplication. Timers, permissions, quiescence, retention and recovery documentation remain correct.

## Migration and release conditions

- Inventory actual `pluto` generation directories, fixed publication link, current `mars` accepted generation, Btrfs subvolumes, live schedules, held checkpoint `20261013-171228Z` (if still present), latest accepted replication parent and `backup` receipts. Take and verify independent recovery points.
- Develop/test both sides against disposable fixtures and isolated directories first. Do not switch production while 0034/0035 acceptance is open.
- Install disabled or shadow-mode; execute preflight and controlled rehearsal; stop only relevant publisher/pull timers for brief authorised cutover; preserve reversible pointers and prior accepted data.
- Demonstrate rollback from new layout to old publisher/pull without relying on deleted old generations. Do not prune or remove old ext4 directories until full recovery proof and explicit operator approval.
- Document the operator inspection tools (`diaries-backup-history`, `diaries-backup-status`, snapshot manager and native push), including their new single-current-tree semantics.

## Change-control artefacts

- `IMPLEMENTATION-STEPS.md`: staged implementation and acceptance gates.
- `DESIGN-DECISIONS.md`: alternatives, risks and open detailed design choices.
- `evidence/`: add test, runtime, migration, recovery and close-out artefacts during implementation; do not fabricate successful live evidence.

**Feature is proposed only. No production code, Playbooks configuration, timers, backups or retention state is changed by these documents.**
