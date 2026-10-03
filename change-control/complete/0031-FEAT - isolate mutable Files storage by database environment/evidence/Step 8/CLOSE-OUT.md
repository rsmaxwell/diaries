# 0031-FEAT — Step 8 close-out

**Decision:** COMPLETE — 2026-10-02

Step 8 — **Freeze mutable writes and take pre-migration backups** — is closed.

The live pre-migration capture has now been completed with both local and production mutable write paths frozen. Matching PostgreSQL backups were taken for the one effective local `common` dataset and for production, and the old shared mutable Files tree was copied to a dedicated rollback snapshot while the freeze remained in force.

## Completion evidence

### Local mutable-write freeze

The Windows Step 8 freeze completed successfully after the listener check was corrected to use the .NET active-listener API rather than `Get-NetTCPConnection`.

The successful run recorded:

```text
PASS: no known local Docker responder is running.
PASS: no process is listening on local TCP/8081.
Diaries source commit: b89ca157b33181aa5df1077aeb342a3b5b32da7d
Local mutable Image/File writes are frozen.
```

Runtime evidence:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 8/runtime/local-write-freeze-20261002-112909.txt
```

### Production mutable-write freeze

The production freeze on `pluto` stopped only the responder and deliberately left PostgreSQL running for the database backup.

The successful run recorded:

```text
PASS: production responder is stopped.
PASS: production database remains running for backup.
Production mutable Image/File writes are frozen.
```

Runtime evidence originated at:

```text
/home/richard/projects/diaries/data/0031-step8/production-write-freeze-20261002-142433.txt
```

The freeze helper reported the Playbooks/runtime source identity as `unknown`. This is retained as an observed value rather than replaced by an inferred identity. It does not prevent recovery to the captured pre-split data point because the production database, Files selector/root and rollback artifacts are explicitly identified below.

### Local database backup

The effective local mapping was resolved as:

```text
Launch mode:              development-infrastructure
Effective dataset:        common
Effective database data:  data/database/common
Configured Files selector: files-development-common
Pre-migration Files selector: files
```

The backup represents all three local launch modes because their paired `local.env` override intentionally selects the same `common` database dataset.

Captured database backup:

```text
data/database-backups/common/diaries-common-step8-premigration-20261002-142614.dump
```

SHA-256:

```text
d1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7
```

The Step-7 dataset sidecar and Step-8 runtime manifest were also written. The script explicitly records that this is a **DATABASE-ONLY** backup and that the matching mutable Files bytes are preserved separately.

### Production database backup

The production mapping was captured as:

```text
Effective dataset: production
Database storage:  docker-volume:diaries-db-data
Files selector:    files
Files root:        //nas.tail636235.ts.net/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files
```

Captured database backup:

```text
/home/richard/projects/diaries/data/database-backups/production/diaries-production-20261002-142838.dump
```

SHA-256:

```text
0a3026f95ff100fd2d200dedab777242568af4ab22b3d3ef2315ef75f547f5d9
```

The Step-7 dataset sidecar and Step-8 runtime manifest were also written. As with the local backup, the production helper explicitly records that this is a **DATABASE-ONLY** backup and does not claim to include mutable Files bytes.

### Shared Files rollback snapshot

With both write paths frozen, the old shared pre-split Files tree was captured from:

```text
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files
```

into:

```text
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\.0031-backups\step8-20261002-143134\files
```

The snapshot run recorded:

```text
Source file count: 90
Source total bytes: 100032776
robocopy exit code: 1 (success is < 8)
PASS: source and snapshot SHA-256 inventories are identical.
```

Both source and snapshot inventory SHA-256 values are:

```text
0170fa4b359538f92532a10fb02658c8fffadca2aff5290891196075a2ee48ff
```

Snapshot manifest:

```text
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\.0031-backups\step8-20261002-143134\SNAPSHOT-MANIFEST.json
```

Repository evidence copy:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 8/runtime/shared-files-snapshot-20261002-143134.json
```

### `.image-staging` review

The snapshot inspection found one file beneath `.image-staging`.

That content was deliberately retained in the exact rollback snapshot so the pre-split recovery point is complete, but it must **not** be blindly propagated when the new dataset-specific Files roots are seeded. Its disposition is deferred to the later migration step that reviews staging/transient content before copying into the new roots.

## Completion decision

Step 8 is complete because the retained runtime evidence establishes all of the required pre-migration recovery conditions:

- local mutable responder writes were frozen;
- production mutable responder writes were frozen;
- the one independent effective non-production database dataset (`common`) was backed up;
- the production database was backed up;
- both database backups have recorded dataset/Files identities and SHA-256 hashes;
- the old shared mutable Files tree was copied while both write paths were frozen;
- the Files source and rollback snapshot inventories are byte-for-byte equivalent according to the complete SHA-256 inventory comparison;
- `.image-staging` was explicitly inspected and its one retained item was identified for later review rather than silently copied into future dataset roots; and
- the rollback locations for the local database, production database and pre-split Files tree are known.

The Step 8 completion criterion is therefore satisfied: **rollback can restore each independent database/Files pair to the known pre-split point captured on 2026-10-02.**

## Operational hand-off

Do **not** restart the local or production responder write paths as part of this close-out. The frozen pre-split state is intentionally handed directly to Step 9 so reconciliation can run against the same data point that was backed up.

**Next implementation step:** Step 9 — reconcile each independent database against the frozen shared Files tree before any storage split/copy is performed.
