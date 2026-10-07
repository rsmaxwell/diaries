# Step 1 evidence — freeze existing database-only tooling and effective dataset contract

Date: 2026-10-07

## Purpose

This step records and regression-freezes the database-only backup/restore behaviour which existed before 0033 adds complete-dataset operations.

No database, mutable Files tree, MQTT retained state, Docker service or production deployment is changed by Step 1. The existing database-only commands remain supported and deliberately remain **database-only**.

Source reviewed for this freeze:

```text
diaries-sources-20261007-102925.zip
playbook-sources-20261007-102933.zip
```

The permanent regressions strengthened by this step are:

```text
Diaries:
  python scripts/windows/validation/verify-local-backup-restore-semantics.py

Playbooks:
  python roles/diaries/tests/verify-production-backup-restore-semantics.py
```

Their captured output is in `REGRESSION.txt`.

## Frozen dataset contract

The 0031 invariant remains authoritative:

```text
one effective PostgreSQL dataset
    <->
one matching mutable Files root
```

Database-only backup media does not contain mutable Files bytes. Its `.dataset.json` sidecar records the Files identity which must remain paired with the database dump.

The local scripts load the committed mode environment first and `config/environments/local.env` second, validate the database/Files pair, and only then resolve the effective dataset. Consequently the launch mode does not, by itself, determine the database-backup namespace.

The normal shared-local example is explicitly:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

`resolve-effective-dataset.ps1` derives:

```text
DIARIES_DATASET_NAME=common
```

for all three launch modes when that pair is selected. The resulting database-only backup directory is therefore:

```text
<data project root>\data\database-backups\common
```

and not a separate mode-labelled backup directory.

## Current command inventory

| Environment | Binary backup | SQL backup | Binary restore | SQL restore |
| --- | --- | --- | --- | --- |
| development-infrastructure | `scripts/windows/development-infrastructure/backup-db-to-binary.bat` | `scripts/windows/development-infrastructure/backup-db-to-sql.bat` | `scripts/windows/development-infrastructure/restore-db-from-binary.bat` | `scripts/windows/development-infrastructure/restore-db-from-sql.bat` |
| local-docker-build | `scripts/windows/local-docker-build/backup-db-to-binary.bat` | `scripts/windows/local-docker-build/backup-db-to-sql.bat` | `scripts/windows/local-docker-build/restore-db-from-binary.bat` | `scripts/windows/local-docker-build/restore-db-from-sql.bat` |
| local-published-smoke | `scripts/windows/local-published-smoke/backup-db-to-binary.bat` | `scripts/windows/local-published-smoke/backup-db-to-sql.bat` | `scripts/windows/local-published-smoke/restore-db-from-binary.bat` | `scripts/windows/local-published-smoke/restore-db-from-sql.bat` |
| production | `roles/diaries/files/sync/scripts/backup-db-to-binary.sh` | `roles/diaries/files/sync/scripts/backup-db-to-sql.sh` | `roles/diaries/files/sync/scripts/restore-db-from-binary.sh` | `roles/diaries/files/sync/scripts/restore-db-from-sql.sh` |

## Local behaviour frozen by Step 1

For all three local modes:

| Contract item | Frozen behaviour |
| --- | --- |
| Effective database identity | `resolve-effective-dataset.ps1` canonicalises `DIARIES_DB_DATA_DIR`; `DIARIES_DATASET_NAME` is the leaf directory name. |
| Effective Files identity | Direct development resolves `diaries.root/<DIARIES_FILES_DIR>` from the developer responder JSON. Docker modes resolve the NAS path from `DIARIES_NAS_HOST`, `DIARIES_NAS_SHARE`, `DIARIES_NAS_CONTENT_PATH` and `DIARIES_FILES_DIR`. |
| Pair validation | `validate-dataset-pair.bat` / `validate-dataset-pair.ps1` must pass before backup or restore continues. |
| Backup directory | `data\database-backups\<DIARIES_DATASET_NAME>`. |
| Default binary name | `diaries-<DIARIES_DATASET_NAME>-yyyyMMdd-HHmmss.dump`. |
| Default SQL name | `diaries-<DIARIES_DATASET_NAME>-yyyyMMdd-HHmmss.sql`. |
| PostgreSQL executor | `docker compose ... exec -T diaries-db pg_dump`, `pg_restore` or `psql`. |
| Binary format | `pg_dump --format=custom`; restore validates using `pg_restore --list` and applies using `pg_restore`. |
| SQL format | `pg_dump --format=plain`; restore performs a plain-dump header check and applies using `psql`. |
| Restore writer quiescence | **Manual current behaviour:** the script tells the operator to stop any responder that can access the database before continuing. It does not automatically stop the responder. |
| Destructive confirmation | Operator must type `RESTORE`. |
| Manifest writer | `scripts/windows/common/write-db-backup-manifest.ps1`. |
| Manifest verifier | `scripts/windows/common/verify-db-backup-manifest.ps1`. |
| Legacy dump compatibility | A missing `.dataset.json` sidecar is allowed with an explicit database-only/manual-Files verification warning. |

The automatic writer-quiescence limitation above is intentionally recorded, not corrected in Step 1. The later complete-dataset backup/restore engine must provide stronger coherent writer quiescence without silently changing these existing database-only commands.

## Production behaviour frozen by Step 1

| Contract item | Frozen behaviour |
| --- | --- |
| Effective database identity | Logical dataset `production`; database storage identity `docker-volume:diaries-db-data`; database name from deployed `.env`. |
| Effective Files identity | `DIARIES_FILES_DIR` plus deployed NAS host/share/content-path values, resolved by `dataset-backup-manifest.py`. |
| Backup directory | `<production project>/data/database-backups/production`. |
| Default binary name | `diaries-production-yyyyMMdd-HHmmss.dump`. |
| Default SQL name | `diaries-production-yyyyMMdd-HHmmss.sql`. |
| PostgreSQL executor | `DIARIES_DB_SERVICE`, default `diaries-db`, performs `pg_dump`, `pg_restore` and `psql`. |
| Restore writer quiescence | If `DIARIES_RESPONDER_SERVICE` (default `diaries-responder`) was running, the restore stops it. It is restarted after successful restore; restore failure deliberately leaves it stopped. |
| Destructive confirmation | Operator must type `RESTORE`. |
| Manifest helper | `roles/diaries/files/sync/scripts/dataset-backup-manifest.py` provides `describe`, `write` and `verify`. |
| Legacy dump compatibility | A missing `.dataset.json` sidecar is allowed with an explicit database-only/manual-Files verification warning. |

## Frozen database-only manifest semantics

Local and production helpers both retain schema version 1 and the same semantic markers:

```json
{
  "schemaVersion": 1,
  "backupType": "database-only",
  "completeDatasetBackup": false,
  "filesSnapshot": null
}
```

The sidecar also records:

```text
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
```

The restore guard compares the current effective logical dataset, database storage identity, Files selector and physical Files root with the sidecar before destructive restore. A mismatch is refused.

Representative, deliberately non-secret examples are retained beside this document as:

```text
local-database-only-manifest.example.json
production-database-only-manifest.example.json
```

They are contract examples, not restorable backup metadata.

## Regression freeze added by 0033 Step 1

The local permanent validator now additionally proves:

- environment override order is committed mode first, `local.env` second;
- the common pair is explicitly present in `local.env.example` and in the 0031 pair guard;
- all 12 existing local database-only commands keep effective-dataset backup naming;
- all local backup operations still run `pg_dump` in `diaries-db` and retain custom/plain formats;
- all local restores retain the current manual responder-quiescence warning and `RESTORE` confirmation;
- existing sidecars cannot silently change into complete-dataset manifests.

The production permanent validator now additionally proves:

- the effective database identity remains `production` / `docker-volume:diaries-db-data`;
- Files identity still comes from the deployed `.env` values;
- the production backup namespace and filename forms remain unchanged;
- `diaries-db` remains the default PostgreSQL service;
- production restore retains the stop/restart-on-success and leave-stopped-on-failure responder behaviour;
- the manifest helper is exercised for `describe`, `write`, matching `verify`, mismatched-Files rejection and legacy-sidecar compatibility;
- schema-1 database-only markers remain unchanged.

## Step 1 conclusion

Step 1 is complete. The pre-0033 database-only behaviour and the 0031 effective database/Files pairing contract are now documented and protected by repeatable permanent checks in both source repositories.

No complete-dataset command exists yet; that starts with Step 2's complete-backup directory and manifest contract.
