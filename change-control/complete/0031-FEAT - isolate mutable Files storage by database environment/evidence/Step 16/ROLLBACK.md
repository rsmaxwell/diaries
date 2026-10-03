# 0031-FEAT rollback procedure

0031 changed the **selection and isolation of mutable Files storage**, not the logical Image path contract. Rollback must therefore always treat PostgreSQL and mutable Files as a matched durable pair.

## Preserved Step 8 recovery point

Local common database backup:

```text
data/database-backups/common/diaries-common-step8-premigration-20261002-142614.dump
SHA-256 d1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7
```

Production database backup:

```text
/home/richard/projects/diaries/data/database-backups/production/diaries-production-20261002-142838.dump
SHA-256 0a3026f95ff100fd2d200dedab777242568af4ab22b3d3ef2315ef75f547f5d9
```

Pre-split shared Files rollback snapshot:

```text
P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\.0031-backups\step8-20261002-143134\files
```

The Step 8 source/snapshot complete-inventory SHA-256 is:

```text
0170fa4b359538f92532a10fb02658c8fffadca2aff5290891196075a2ee48ff
```

## Normal rollback sequence

1. **Stop the responder for the affected dataset.** Keep PostgreSQL available only when the selected restore helper requires it. Do not permit Image/File lifecycle operations during rollback/reconciliation.
2. **Preserve the current isolated state first.** Take/copy a new database backup and Files inventory/snapshot before replacing anything. Never destroy `files-development-common`, production `files`, or another isolated root merely because an older state is being restored.
3. **Choose one known matched recovery point.** Restore the database dump and the Files snapshot/root that belong to the same point. Do not restore one durable side and assume the other is compatible.
4. **Restore configuration as one pair.** For the normal common-local model, restore both:

   ```text
   DIARIES_DB_DATA_DIR=./data/database/common
   DIARIES_FILES_DIR=files-development-common
   ```

   together. Never change just one selector.
5. **Reconcile read-only before writes resume.** Run the 0024 dry-run reconciliation and review missing/untracked/conflict entries. A database-only restore is explicitly treated as potentially requiring Files reconciliation.
6. **Only restart the responder after the pair is understood.** Confirm stable `/data/files` runtime mounting and `/files/...` public serving; persisted `Image.relativePath` values must remain environment-neutral.

## Temporary reversion to the old shared tree

The old pre-split `files` tree exists only as a recovery mechanism. If two datasets that have changed independently are temporarily pointed back at that one tree, **disable destructive Image/File lifecycle operations for both datasets** until reconciliation determines a safe disposition.

Never merge divergent roots automatically. Do not use `robocopy /MIR`, `rsync --delete`, bulk overwrite, or automatic newest-file-wins logic to collapse independently changed roots into one shared tree.

If the goal is to restore the exact Step 8 pre-split state, restore the corresponding Step 8 database backup(s) and the preserved Step 8 shared Files snapshot together while responders are stopped. If only one dataset is being rolled back, prefer restoring/copying its own matching isolated root rather than re-sharing the old tree.

## Production-specific rollback

Production currently selects:

```text
DIARIES_FILES_DIR=files
```

through explicit Ansible inventory `diaries_files_dir: files`. Do not point production at any `files-development-*` root. Preserve the current production database/Files pair, restore the selected matched recovery pair, run the production read-only reconciliation, and restart only after the explicit selector/mount and reconciliation are clean.

## Rebuildable state

MQTT retained state is not a durable recovery side. It is mode/broker-specific and can be rebuilt from the restored matching database by responder synchronisation. Do not use retained MQTT state as a substitute for PostgreSQL/Files recovery.
