# 0033-FEAT - Add complete Diaries dataset backup and restore

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-10-05

## Summary

Add a first-class **complete Diaries dataset backup and restore** operation which treats the durable PostgreSQL database and its matching mutable Files root as one recoverable unit.

A successful complete backup must create one self-contained backup directory containing:

```text
PostgreSQL custom/binary dump
+ PostgreSQL plain SQL dump
+ exact durable mutable Files snapshot
+ dataset manifest
+ verification/checksum inventory
```

A complete restore must restore the matching database and mutable Files snapshot together. It must not silently restore one half of the dataset, merge backup Files into an unrelated live Files tree, or allow a database/Files pairing which violates the invariant established by 0031.

The existing database-only backup and restore scripts remain supported. This feature adds a higher-level operation; it does not redefine a database-only backup as a complete dataset backup.

## Background

0031-FEAT established the core durable-storage invariant:

```text
one effective PostgreSQL dataset
    <->
one matching mutable Files root
```

0031 also changed the existing database backup helpers so each new `.dump` or `.sql` backup has a `.dataset.json` sidecar identifying the effective database dataset and matching Files root. Those helpers deliberately label themselves `DATABASE-ONLY` and record:

```json
"backupType": "database-only",
"completeDatasetBackup": false,
"filesSnapshot": null
```

That is correct and should remain correct: an SQL or binary PostgreSQL dump alone is not enough to recover the complete mutable Diaries dataset when Image catalogue records refer to physical files in the matching Files root.

During 0031, database backups and Files snapshots were coordinated manually for migration/rollback evidence. That was sufficient for the storage split, but it is not the desired permanent operator experience.

The permanent operational model should provide an explicit complete-dataset command which creates and verifies both sides together, and a complementary restore command which restores both sides together.

## Dataset boundary

For this feature, a **complete Diaries dataset** means:

```text
PostgreSQL durable application data
+
matching mutable Files root selected by DIARIES_FILES_DIR / diaries_files_dir
```

It does **not** include:

- the original shared/read-only diary scan tree (`diaries` / `/data/diaries`);
- retained MQTT topics, because retained state is derived/replayed from PostgreSQL;
- Docker images or application binaries;
- environment files, credentials, secrets or Mosquitto password files;
- NAS/platform backups outside the Diaries application dataset.

Those items have their own configuration, deployment or infrastructure backup responsibilities.

## Required operator model

Retain the existing distinction:

```text
DATABASE-ONLY BACKUP
    diaries-....dump OR diaries-....sql
    + .dataset.json sidecar

COMPLETE DATASET BACKUP
    one backup directory
        + binary database backup
        + SQL database backup
        + mutable Files snapshot
        + complete dataset manifest
        + verification inventories/checksums
```

The complete-dataset operation is the preferred choice when the goal is disaster recovery, environment rollback, or a durable point-in-time copy of application data.

The database-only helpers remain useful for database inspection, focused database rollback, migration work and other cases where the operator deliberately manages the matching Files state separately.

## Proposed complete backup layout

The exact root directory may differ between local Windows and production, but each completed backup must have the same logical structure. A local example is:

```text
data/
└── dataset-backups/
    └── common/
        └── 20261005-183000/
            ├── dataset-manifest.json
            ├── database/
            │   ├── diaries.dump
            │   └── diaries.sql
            ├── files/
            │   └── <snapshot of the durable mutable Files tree>
            └── verification/
                ├── database.sha256
                ├── files.sha256
                └── inventory.json
```

The backup must be built under a temporary/incomplete name and promoted to its final directory name only after every component has been created and verified. An interrupted operation must never leave a partial directory which looks like a valid complete backup.

If all three local launch modes resolve through `local.env` to:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

they are one effective dataset and therefore share the same complete-backup namespace. The backup identity is determined from the **effective dataset**, not from the launch script used to invoke it.

## Backup consistency requirements

The database dumps and Files snapshot must describe one coherent point in the dataset's history.

Before capture, the tooling must:

1. resolve and validate the effective database + Files pair;
2. identify every application writer which can mutate that pair;
3. quiesce or prove stopped those writers while keeping PostgreSQL available for `pg_dump`;
4. inspect `.image-staging` and refuse unexplained in-flight/transient content;
5. capture enough preflight identity/count information to prove what is being backed up.

While writers are quiesced, the operation must create both PostgreSQL representations and the Files snapshot. The custom/binary dump is the normal restore source; the SQL dump is a human-readable/portable companion and independent fallback representation.

The backup must not silently resume or declare success after any failed dump, failed file copy, checksum mismatch or manifest validation failure.

## Mutable Files snapshot semantics

The backup must preserve the durable Files directory hierarchy and file bytes exactly.

At minimum verification must record:

```text
file count
total bytes
relative paths
SHA-256 per durable file
aggregate/inventory identity
```

`.image-staging` is transient/recovery state and must not be blindly treated as ordinary durable content. The implementation must define a conservative policy which:

- inventories staging before backup;
- permits only understood benign state (for example an expected empty/lock condition);
- stops for review if unexplained staged payloads exist;
- records the disposition in the manifest/evidence;
- does not blindly restore stale staging payloads into a live Files root.

## Complete dataset manifest

A complete backup has one directory-level `dataset-manifest.json`. It is separate from, and stronger than, the current database-only `.dataset.json` sidecars.

The final schema should contain at least:

```text
schema/version
backupType = complete-dataset
completeDatasetBackup = true
backup status/completion marker
creation start/end timestamps
logical dataset identity
invoking launch mode / known consumers
effective database storage identity
database name
effective Files selector
resolved physical Files root
application/source/runtime identity
writer-quiescence evidence
Image row count
catalogued/durable file count
```

and, for each captured component:

```text
relative backup path
format/type
size
SHA-256/inventory reference
verification result
```

For example:

```json
{
  "schemaVersion": 1,
  "backupType": "complete-dataset",
  "completeDatasetBackup": true,
  "status": "complete",
  "logicalDataset": "common",
  "database": {
    "name": "diaries",
    "customDump": "database/diaries.dump",
    "sqlDump": "database/diaries.sql"
  },
  "files": {
    "selector": "files-development-common",
    "snapshotDirectory": "files",
    "inventory": "verification/files.sha256"
  }
}
```

The implementation may extend this structure, but restore must validate a supported schema before making any destructive change.

## Complete restore semantics

The primary restore interface must accept a **complete backup directory**, not an arbitrary combination of independent database and Files paths.

The normal restore source is the custom/binary PostgreSQL dump. The SQL dump is retained as a second representation and fallback/inspection artifact rather than being applied in addition to the binary dump.

Before touching the current dataset, restore must:

1. resolve the current effective database + Files target pair;
2. load and validate `dataset-manifest.json`;
3. verify every required backup component and checksum;
4. reject an unsupported/incomplete manifest;
5. reject a mismatched dataset/Files identity by default;
6. verify adequate staging/rollback space as far as practical;
7. stop/quiesce all writers for the target pair;
8. require an explicit destructive confirmation;
9. create or require a verified pre-restore safety backup unless an exceptional, explicitly documented recovery override is used.

The Files part of restore must be **replacement semantics, not merge semantics**.

For example, if live Files contains:

```text
a.jpg
b.jpg
obsolete.jpg
```

and the selected complete backup contains only:

```text
a.jpg
b.jpg
```

then a successful restore must not leave `obsolete.jpg` behind.

Files should be staged and verified before promotion to the live root. The implementation must preserve a rollback path if the database or Files apply fails part-way through.

## Post-restore verification

Before writers are re-enabled, verify at least:

```text
database restore completed without error
manifest database identity matches target
restored Files SHA-256 inventory matches backup
Image row count matches the backed-up value
Image catalogue -> physical file reconciliation has no unexplained mismatch
public /files URL contract still resolves through the selected Files root
responder starts successfully
retained MQTT state is rebuilt/replayed from PostgreSQL
reader/client can resolve representative Images
```

A failed postflight must leave the application stopped or otherwise protected from writes until the operator chooses rollback or repair.

## Scope

### Local Windows tooling

Provide permanent complete-dataset backup/restore entry points for the supported local modes while sharing common implementation wherever practical.

They must load committed mode configuration followed by `local.env`, use the existing effective-dataset pair validation, and key the backup namespace from the effective dataset rather than the mode name.

Likely locations include:

```text
scripts/windows/common/
scripts/windows/development-infrastructure/
scripts/windows/local-docker-build/
scripts/windows/local-published-smoke/
```

Prefer thin mode wrappers around one common PowerShell implementation rather than three divergent copies of complex snapshot/restore logic.

### Production / Playbooks

Add corresponding permanent production tooling to the Diaries Playbooks role and deployed production script directory, consistent with the existing:

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
restore-db-from-binary.sh
restore-db-from-sql.sh
dataset-backup-manifest.py
```

Production backup/restore must use the explicit `diaries_files_dir` pairing and existing generated `.env`/Compose runtime configuration. It must not infer a mutable Files root from a historical default.

The production rollout must exercise backup and verification non-destructively. A destructive restore must be rehearsed against a disposable/restored environment; production itself does not need to be destroyed merely to prove the script works.

### Existing database-only tooling

Do not remove or silently change the meaning of the existing database-only helpers.

Their `.dataset.json` sidecars remain useful. Documentation should make clear when to use database-only versus complete-dataset operations.

### Regression and validation

Add permanent regression checks covering at least:

- effective common dataset identity across local modes;
- isolated local defaults;
- mismatched database/Files pair rejection;
- incomplete backup rejection;
- corrupt/missing dump rejection;
- corrupt/missing Files item rejection;
- checksum mismatch rejection;
- unexpected `.image-staging` content rejection;
- interrupted backup cannot look complete;
- restore uses replacement rather than merge semantics;
- restore does not start writers after failed postflight;
- complete backup manifest round-trip validation;
- production role/rendered runtime points at the selected production Files root.

## Out of scope

Unless separately approved, this feature does not introduce:

- automatic backup scheduling;
- backup retention/pruning policy;
- off-site/cloud replication;
- encryption-at-rest for backup media;
- backup of the original read-only diary scan collection;
- backup of Docker images, source repositories or secrets;
- cross-dataset cloning/remapping as a normal restore mode;
- live/hot Files snapshots while application writers continue mutating the dataset.

Those may be separate operational features later. The first objective is a simple, trustworthy, operator-invoked coherent backup/restore path.

## Dependencies

- 0031-FEAT is complete and is the authoritative database/Files pairing contract.
- 0032-FEAT is complete and its live-script hygiene rules apply to any tooling introduced here.
- Existing Image catalogue/reconciliation behaviour from 0024/0030/0031 must remain available for preflight/postflight verification.
- 0027 does not need to be complete for the backup format itself, but any 0027-produced durable database/Files state must naturally be preserved by the complete backup once 0027 is deployed.

## Risks

The principal risks are operational rather than algorithmic:

- taking database and Files snapshots while writes continue can produce an internally inconsistent backup;
- restoring only one half recreates the storage defect prevented by 0031;
- copying Files with merge semantics can leave files that did not exist at the backed-up point in time;
- restoring stale `.image-staging` state can replay abandoned transient work;
- a partially failed restore can leave database and Files at different points in time;
- complete backups may consume materially more disk space because they contain two database representations plus the Files bytes;
- production Files are NAS-hosted, so network interruption and permissions must be detected rather than treated as successful copies.

The implementation must prefer a failed/stopped operation over a silently inconsistent dataset.

## Acceptance Criteria

- [ ] An operator can create one complete backup directory for the current effective dataset with one command.
- [ ] The directory contains a valid custom/binary database dump, a valid SQL database dump, an exact verified durable Files snapshot, and one complete-dataset manifest.
- [ ] The backup identity is based on the effective database + Files pair, including `local.env` overrides.
- [ ] A shared local `common` dataset is represented as one dataset regardless of which local mode invokes the operation.
- [ ] A partial/interrupted backup cannot be mistaken for a completed backup.
- [ ] Checksums/inventories detect changed, missing or extra durable Files in a backup.
- [ ] Unexplained `.image-staging` content blocks or explicitly suspends completion for review.
- [ ] A complete restore accepts one complete backup directory and restores the database + Files together.
- [ ] The normal complete restore uses the custom/binary dump and verifies the SQL companion without applying both.
- [ ] Restore verifies all backup components before destructive work begins.
- [ ] Restore rejects a mismatched effective database/Files target by default.
- [ ] Files restore is replace/exact semantics rather than merge semantics.
- [ ] Restore has a documented safety-backup and rollback path for partial failure.
- [ ] Failed restore/postflight does not automatically return the application to a writable state.
- [ ] Postflight proves database/Image/Files reconciliation and successful retained-state replay.
- [ ] Existing database-only backup/restore scripts remain supported and explicitly labelled database-only.
- [ ] Equivalent permanent production backup/restore tooling is deployed through Playbooks.
- [ ] A complete backup and destructive restore have been rehearsed successfully in a disposable environment.
- [ ] Production complete backup has been exercised non-destructively and verified.
- [ ] Documentation clearly explains what is and is not contained in a complete Diaries dataset backup.
- [ ] Permanent tooling follows 0032 script-directory hygiene; feature-only rehearsal/evidence tooling is archived with the change record.

## Deployment and rollback

The feature can be rolled out additively because the current database-only commands remain intact.

Do not replace operational practice with the new complete-dataset tooling until:

1. backup verification passes on representative local datasets;
2. a destructive restore rehearsal proves database + Files recovery into a disposable target;
3. production script rendering/deployment is verified;
4. a production complete backup is captured and independently verified.

If the new complete-dataset tooling is found defective before it has been relied upon for recovery, remove/disable the new entry points and continue using the existing database-only helpers plus separately managed Files snapshots. Never discard an existing verified backup merely because a newer backup format has been introduced.
