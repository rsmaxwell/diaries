# Step 7 matched backup/restore semantics

The durable invariant remains:

```text
one effective PostgreSQL dataset <-> one effective mutable Files root
```

Step 7 does **not** turn the existing database scripts into complete dataset
backup tools. Instead it makes their limited scope explicit and records enough
identity to prevent a database snapshot being casually paired with the wrong
Files tree.

## Local default backup identity

The three Windows modes load their committed environment first and `local.env`
second, validate that the database + Files override is paired, then derive the
backup namespace from the effective `DIARIES_DB_DATA_DIR` leaf.

For the normal shared local override:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

all three launch modes therefore use:

```text
data/database-backups/common/
  diaries-common-YYYYMMDD-HHMMSS.dump
  diaries-common-YYYYMMDD-HHMMSS.dump.dataset.json
```

This is one durable dataset, not three mode-specific datasets.

With no `local.env` override, the committed isolated defaults produce separate
backup namespaces named from the effective database leaves:

```text
development-infrastructure
local-docker-build
local-published-smoke
```

## Sidecar manifest

A successful new database backup writes `<backup>.dataset.json` containing:

```text
schemaVersion
backupType = database-only
completeDatasetBackup = false
createdAt
launchMode
logicalDataset
effectiveDatabaseDataDir
databaseName
databaseBackupFile
databaseBackupFormat
effectiveFilesDir
resolvedPhysicalFilesRoot
applicationSourceIdentity
imageRowCount
cataloguedFileCount
filesSnapshot = null
```

`cataloguedFileCount` is currently the Image catalogue row count. The manifest
is identity/recovery metadata; it is not a physical Files inventory.

## Restore rule

If a sidecar is present, restore verifies that the recorded logical dataset,
database storage identity, Files selector and resolved physical Files root match
the current effective configuration. A mismatch is rejected before the current
database is dropped.

Legacy dumps without a sidecar remain usable so existing recovery material is
not invalidated. They produce an explicit warning that the operation is
DATABASE-ONLY and the matching Files root/snapshot must be verified manually.

## Production

The deployed Playbooks helpers use the same contract. The production database
identity is recorded as the `diaries-db-data` Docker volume, while the Files
identity is resolved from the deployed `.env` values:

```text
DIARIES_NAS_HOST
DIARIES_NAS_SHARE
DIARIES_NAS_CONTENT_PATH
DIARIES_FILES_DIR
```

The production sidecar also records the runtime Compose images as application
identity.

## Complete recoverable dataset

A complete recoverable backup remains a matched bundle:

```text
PostgreSQL database dump
+ matching mutable Files snapshot/copy
+ dataset/path identity manifest
+ application/source identity
+ optional reconciliation/checksum inventory
```

Step 8 is where those real pre-migration database and Files snapshots are taken
together while mutable writes are frozen. A Step-7 database sidecar deliberately
sets `filesSnapshot` to null and never claims that Files bytes were captured.
