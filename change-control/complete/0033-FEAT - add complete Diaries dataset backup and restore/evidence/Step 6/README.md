# Step 6 evidence — controlled database + Files restore apply

## Status

**Completed 2026-10-07.** Permanent regression and the real Windows/Docker/NAS apply both pass.

Step 6 extends the permanent local complete-restore engine with controlled `apply` and `rollback` actions. It consumes the verified `prepared-awaiting-step6` state created by Step 5 and deliberately leaves the application stopped for Step 7 postflight.

## Operator commands

From any local mode resolving to the prepared effective dataset:

```bat
restore-dataset.bat apply    <backup-id-or-complete-backup-directory>
restore-dataset.bat rollback <backup-id-or-complete-backup-directory>
```

`apply` requires the exact token `APPLY`. `rollback` requires the exact token `ROLLBACK`.

## Pre-destructive revalidation

Before asking for `APPLY`, the engine independently revalidates:

1. the current effective database + Files target pair;
2. the selected completed schema-2 backup and its target identity;
3. the Step-5 prepared state and `prepared-awaiting-step6` status;
4. the mandatory safety backup and target identity;
5. the staged replacement Files tree by exact relative path, size and SHA-256;
6. writer quiescence;
7. current target staging state;
8. current database identity/row count against the mandatory safety backup.

A failure before explicit `APPLY` does not rewrite the prepared state as a destructive failure.

## Database half

The normal and only Step-6 application source is:

```text
database/diaries.dump
```

Immediately before destructive restore the archive is copied into the selected PostgreSQL container and rechecked with `pg_restore --list`. The engine then uses the already-proven local database restore mechanics:

```text
dropdb --force --if-exists
createdb --owner <DIARIES_DB_USERNAME>
pg_restore --exit-on-error --no-owner --no-privileges
```

`database/diaries.sql` is never applied after the custom dump. Restore state records the database OID and Image row count before and after application and verifies the restored Image row count against the selected complete-backup manifest.

## Files half — exact replacement, not merge

Step 5 already produced a verified same-parent sibling stage. Step 6 uses same-parent rename semantics:

```text
<live Files root>
    -> .<files-leaf>.pre-restore-<backup-id>.rollback

.<files-leaf>.restore-<backup-id>.staged
    -> <live Files root>
```

This preserves the old live Files tree as explicit rollback state and guarantees that a durable file absent from the selected backup cannot survive by virtue of having existed in the previous target.

If promotion of the staged directory fails immediately after the old live root was renamed away, the engine attempts to rename the original root straight back before reporting failure.

The selected backup never contains `.image-staging`. After successful promotion, Step 6 creates a new empty runtime `.image-staging`, then independently verifies the durable live tree against the backup while permitting only that empty directory (or the responder's normal zero-byte `catalogue.lock` on later checks). Stale staging payloads remain invalid.

## Failure and rollback state

Once destructive work starts, every state transition is persisted under the Step-5 prepared directory. On any failure the safe default is:

```text
writers remain stopped
status = step6-apply-failed
liveDataset.databaseChanged = true/false
liveDataset.filesRootChanged = true/false
mandatory safety backup retained
original Files rollback sibling retained when created
```

The error output includes the exact recovery assets and command:

```bat
restore-dataset.bat rollback <source-backup-id>
```

Rollback restores PostgreSQL from the mandatory safety backup's custom dump. If the pre-restore Files rollback sibling exists, the current replacement tree is moved to a timestamped failed-restoration diagnostic path and the original live Files root is renamed back. If Files application never began, rollback verifies that the unchanged live root still matches the safety backup instead. The resulting pre-restore durable Files are independently verified; writers still remain stopped for review.

## Success hand-off

A successful destructive apply ends with:

```text
status = applied-awaiting-step7
writers = stopped
mandatory safety backup = retained
original pre-restore Files rollback tree = retained
```

Step 6 does not restore prior writer state and does not delete rollback assets. Step 7 owns reconciliation, retained replay, final acceptance and failure-safe restart.

## Permanent regression

`REGRESSION.txt` records the permanent Step-6 regression. It protects:

- all three wrappers exposing `apply` and `rollback` through one common engine;
- custom-dump-only database application;
- proven drop/recreate/`pg_restore --exit-on-error` mechanics;
- exact Files replacement by rename rather than merge;
- retention and verification of rollback state;
- fresh/benign-only `.image-staging` semantics;
- changed-half failure reporting and writers-stopped policy;
- a synthetic replacement where a pre-restore extra durable file disappears after apply;
- synthetic Files rollback to the prior durable tree;
- an intentional promotion-failure model in which the original Files root is immediately recoverable.

## Real runtime apply — 2026-10-07

`RUNTIME-APPLY.txt` records the successful destructive rehearsal against the shared `common` dataset. Before apply, the selected restore backup `20261007-105033Z`, mandatory safety backup `20261007-114623Z`, and 89-file staged replacement tree were independently revalidated.

The real apply then recorded:

```text
Database before: OID=16385, Image rows=85
Database after:  OID=32842, Image rows=85
Files after:     89 files / 100032776 bytes; exact inventory verified
Runtime staging: empty .image-staging recreated
Writers:         STOPPED - Step 7 postflight required
```

The original live Files tree remains at `.files-development-common.pre-restore-20261007-105033Z.rollback`, the complete safety backup remains under `data/dataset-backups/common/20261007-114623Z`, and the executable rollback command remained available. This satisfies Step 6's completion criterion: database + Files were replaced together with exact Files semantics, explicit rollback state, and no writer restart before postflight.
