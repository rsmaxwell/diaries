# 0031-FEAT Step 8 Windows tooling

These scripts implement the local/Windows half of **Step 8 — Freeze mutable
writes and take pre-migration backups**.

They are intentionally operational tools. They do not run automatically during
normal startup and they do not create any new live Files root.

## Required order

After the updated production Playbooks have been deployed, perform the Step 8
capture in this order:

```text
1. Windows: freeze-local-writes.bat
2. pluto:   ./scripts/step8-freeze-writes.sh
3. Windows: capture-local-database-backup.bat
4. pluto:   ./scripts/step8-capture-production-database-backup.sh
5. Windows: capture-shared-files-snapshot.bat -ProductionWriteFreezeConfirmed
```

Do not restart either responder between these commands.

## `freeze-local-writes.bat`

Stops the two known local Docker responder containers when present and then
refuses to report success if TCP/8081 is still listening. The latter catches a
direct Windows development responder that must be stopped manually rather than
blindly killing an arbitrary Java process. The listener test uses the .NET
network-information API rather than `Get-NetTCPConnection`, so it does not depend
on the privileged CIM query that can fail in a normal PowerShell session.

The database/MQTT infrastructure is left alone so a database backup can still be
taken.

## `capture-local-database-backup.bat`

Requires the local write freeze still to be in force and requires exactly one
of these local database containers to be running:

```text
diaries-development-db
diaries-local-db
diaries-published-smoke-db
```

It selects the corresponding existing Step-7 `backup-db-to-binary.bat` helper,
so the normal common local override still produces exactly one backup for the
`common` durable database dataset.

The Step-7 database sidecar records the **currently configured target** Files
selector (normally `files-development-common`). Step 8 separately records the
actual pre-migration source identity:

```text
preMigrationSharedFilesDir = files
```

This distinction is deliberate: Step 3/4 prepared the future selector before
the physical split has happened.

## `capture-shared-files-snapshot.bat`

Run this only after the production Step-8 freeze script has succeeded. The
required `-ProductionWriteFreezeConfirmed` switch is an explicit operator guard;
the script cannot inspect the remote production responder itself.

By default it derives the old shared source from the local Docker NAS settings:

```text
\\<DIARIES_NAS_HOST>\<DIARIES_NAS_SHARE>\<DIARIES_NAS_CONTENT_PATH>\files
```

You can override that with, for example:

```bat
capture-shared-files-snapshot.bat ^
  -ProductionWriteFreezeConfirmed ^
  -SharedFilesRoot "P:\nancy-and-ronald-maxwell\documents\sea-captains-chest\diaries-content\files"
```

The snapshot is created as a sibling of the live content under:

```text
...\diaries-content\.0031-backups\step8-YYYYMMDD-HHMMSS\
```

It contains:

```text
files\                   exact rollback copy, including hidden/staging content
SOURCE-SHA256.tsv         source SHA-256 inventory
SNAPSHOT-SHA256.tsv       copied-tree SHA-256 inventory
STAGING-REVIEW.tsv        explicit .image-staging review
ROBOCOPY.log              copy log
SNAPSHOT-MANIFEST.json    source/destination/count/hash identity
```

The two complete SHA-256 inventories must compare identically before the script
reports success.

`.image-staging` is retained in this **rollback** snapshot so no recovery bytes
are lost. A non-empty staging directory is highlighted and is explicitly marked
as **not approved for blind propagation** when Step 10 seeds the new local Files
root.

## Runtime evidence

Small runtime summaries/manifests are written under:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 8/runtime/
```

The potentially large per-file inventories remain beside the NAS snapshot and
should not be committed to Git. Their SHA-256 digests are recorded in the small
manifest/evidence instead.

Keep the write freeze in force after Step 8. Step 9 is intended to reconcile the
independent databases against the frozen pre-split source tree before Step 10
creates/seeds the new local root.
