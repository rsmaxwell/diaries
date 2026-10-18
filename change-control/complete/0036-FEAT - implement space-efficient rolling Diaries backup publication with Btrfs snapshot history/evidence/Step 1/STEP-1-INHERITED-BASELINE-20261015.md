# 0036-FEAT Step 1 — Inherited baseline and 0036 delta

**Date:** 2026-10-15  
**Disposition:** CLOSED — documentation/source review only; no live changes.

## Why no new baseline capture was run

0036 starts immediately after formal closure of 0034-FEAT and 0035-FEAT. Their accepted production evidence remains current for the contracts 0036 inherits. Re-running repository hash capture, timer inventory, snapshot counts, protected checkpoint/parent inventory, receiver receipts or the 0035 safety gates would add no new assurance before any 0036 code has changed.

Step 1 therefore adopts those closure records by reference and records only the source-level facts that define the 0036 optimisation target.

## Inherited accepted state

From 0035 formal closure on 2026-10-15:

- `mars` timestamp snapshot create/prune and native-push scheduling is accepted; legacy Snapper timers are disabled.
- `backup` remains the passive Btrfs receiver with accepted native receipts.
- `pluto` retains the accepted schema-2 publication path and is not Btrfs-mutated.
- The retained checkpoint and protected replication-parent rules remain safety constraints for 0036.
- The 0034 disposable schema-2 recovery and native `mars → backup` correctness evidence is inherited.
- Quantitative allocation/transfer benchmarking was intentionally excluded from 0035 and is therefore **new 0036 evidence**, not repeated evidence.

No claim is made here about a new repository HEAD after the 0035 archival commit; 0036 does not need another start-of-feature Git hash capture. Exact 0036 deployed commits will be recorded at feature close-out.

## Current source contract reviewed from the 2026-10-15 source bundles

### `pluto`

Playbooks defaults define:

- legacy complete-backup repository: `~/projects/diaries/data/dataset-backups/production`
- stable publication: `~/projects/diaries/data/diaries-backup`
- publisher generation store (derived by the publisher): `~/projects/diaries/data/.diaries-backup-generations`

The current production `publish` path does two complete Files copies per logical cycle:

1. `production-complete-dataset.py` captures a complete timestamp-ID backup into the legacy repository.
2. `complete-dataset-publisher.py` uses `shutil.copytree()` to copy that completed backup into a fresh publisher generation before atomically switching the stable symlink.

The old timestamp generation is deliberately retained, so repeated cycles accumulate full photo copies.

### `mars`

Playbooks defaults define:

- source parent on `pluto`: `/home/richard/projects/diaries/data`
- destination parent: `/media/usb/@data/backup/pluto`
- stable local publication: `/media/usb/@data/backup/pluto/diaries-backup`
- derived local publisher store: `/media/usb/@data/backup/pluto/.diaries-backup-generations`
- snapshot source root: `/media/usb/@data`
- verification marker: `/media/usb/@data/backup/.diaries-snapshot-verified.json`
- shared writer lock: `/media/usb/@data/backup/.btrfs-snapshot-writer.lock`

The current `diaries-pull.py` path also rewrites unchanged data twice per cycle:

1. rsync copies the stable `pluto` generation into a fresh empty temporary `incoming` tree.
2. the local publisher then `copytree()` copies that verified candidate into a fresh publisher generation.

Because the rsync target and publisher target are both new, Btrfs has no opportunity to preserve prior file extents through ordinary rolling updates.

## 0036 delta frozen by Step 1

0036 changes **generation construction and retention**, not the accepted external contracts. The optimisation targets are therefore:

1. eliminate unbounded full-copy accumulation on `pluto` while preserving bounded atomic rollback state;
2. avoid rewriting unchanged Files on `mars`, preserving Btrfs extents inside the existing `@data` scope;
3. keep stable `diaries-backup`, schema-2 verification, locks, snapshot eligibility, history/restore compatibility and native off-site replication behaviour intact;
4. introduce new quantitative storage/transfer evidence only where needed to prove the efficiency goal.

No production file, service, timer, snapshot, receipt or backup was changed by Step 1.
