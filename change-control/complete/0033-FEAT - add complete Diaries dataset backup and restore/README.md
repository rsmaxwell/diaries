# 0033-FEAT - Add complete Diaries dataset backup and restore

## Type

Feature

## Status

Complete

## Priority

High

## Opened

2026-10-05

## Progress

- **Step 1 complete — 2026-10-07:** the pre-0033 database-only backup/restore behaviour and the 0031 effective database/Files pairing contract are frozen under [`evidence/Step 1`](evidence/Step%201/README.md). The permanent local and production regressions now protect command naming, effective dataset resolution, database-only sidecar semantics, restore pairing guards and the existing writer-quiescence behaviour. The normal shared local override is explicitly proven to be one `common` dataset when `./data/database/common` is paired with `files-development-common`. Step 1 changes source regression/documentation only; it does not mutate database or Files content or deploy production changes.
- **Step 2 complete — 2026-10-07:** the complete-backup media contract is frozen under [`evidence/Step 2`](evidence/Step%202/README.md). Complete backups use schema-2 `dataset-manifest.json`, UTC `YYYYMMDD-HHmmssZ` IDs, `.<backup-id>.partial` non-restorable workspaces, fixed database/Files/verification component names and relative-only component references. The permanent local and production `complete-dataset-manifest.py` helpers are byte-identical and the synthetic regressions prove generation/validation plus rejection of unsupported schemas, incomplete semantics, unsafe paths, missing/invalid hashes, missing components and changed Files bytes. Step 2 performs no live PostgreSQL/Files capture or restore and does not deploy production changes.
- **Step 3 complete — 2026-10-07:** the common PowerShell capture engine and thin wrappers are proven by both permanent regression and a real Windows/Docker/NAS capture of the shared `common` dataset. The runtime capture kept PostgreSQL running, proved all possible responder writers stopped, accepted only the expected zero-byte `.image-staging/catalogue.lock`, created custom + SQL dumps, and copied 89 durable Files / 95.39 MB with zero failures into `.20261007-105033Z.partial`. See [`evidence/Step 3`](evidence/Step%203/README.md).
- **Step 4 complete — 2026-10-07:** local complete-backup verification and atomic promotion are proven by permanent regression and by successful real finalisation of the Step-3 `common` candidate `20261007-105033Z`. The finaliser validated the custom dump with `pg_restore --list`, verified the SQL dump, proved all 89 durable Files / 100032776 bytes exactly matched the still-quiesced source by path/size/SHA-256, generated and validated the schema-2 manifest as a partial candidate, atomically promoted the directory to `data/dataset-backups/common/20261007-105033Z`, independently validated the completed backup and restored the prior writer state. The first runtime attempt safely remained `.partial` when Windows JSON argument quoting failed; the corrected Base64 handoff then completed without recapture. See [`evidence/Step 4`](evidence/Step%204/README.md).
- **Step 5 complete — 2026-10-07:** real Windows/Docker/NAS preflight and preparation against `20261007-105033Z` validated the complete source media and current `common` target, kept all writers quiesced, created and independently validated mandatory safety backup `20261007-114623Z`, staged and reverified all 89 Files / 100032776 bytes, and left both live durable halves unchanged. The first prepare rehearsal exposed a PowerShell stdout/state plumbing defect in `safetyBackup.directory`; the permanent correction derives the path independently, and the already-prepared state was repaired and verified as `prepared-awaiting-step6` with the safety backup marked `verified=true`. See [`evidence/Step 5`](evidence/Step%205/README.md).
- **Step 6 complete — 2026-10-07:** real Windows/Docker/NAS apply of `20261007-105033Z` revalidated the source and safety media, changed PostgreSQL OID `16385` -> `32842` while retaining 85 Image rows, atomically replaced the live Files tree with the exact 89-file / 100032776-byte snapshot, recreated only fresh runtime `.image-staging`, retained safety backup `20261007-114623Z` plus the original Files rollback sibling, and ended `applied-awaiting-step7` with all writers stopped. See [`evidence/Step 6`](evidence/Step%206/README.md).
- **Step 7 complete — 2026-10-07:** permanent regression plus the real Windows/Docker/NAS postflight prove restore acceptance beyond `pg_restore`. The successful retry revalidated both complete backups, proved the live 89-file / 100032776-byte Files tree exactly matched the selected backup, reconciled 85 Image rows to 85 catalogued files with only four reviewed legacy `Thumbs.db` files untracked, built and started the temporary responder probe, confirmed `synchronise: ok`, read representative retained MARQUEE + IMAGE payloads, and verified representative `/files` Image bytes. Because no responder had been running before restore, all responders correctly remained stopped afterwards. Safety backup `20261007-114623Z` and the pre-restore Files tree remain retained as evidence; automatic rollback is closed after acceptance. See [`evidence/Step 7`](evidence/Step%207/README.md).
- **Step 8 complete — 2026-10-07:** permanent production complete-dataset tooling is deployed through Playbooks and proven on `pluto`. The final Playbooks regressions pass after permanent Python-cache exclusion and host-snapshot ownership/staging hardening; corrected Ansible check/apply runs completed with `failed=0`; production preflight resolved `docker-volume:diaries-db-data / diaries`, Files selector `files`, Docker NAS volume `diaries_nas-photo`, the running responder and benign staging state without mutation. The first real backup failed closed and remained `.partial` when restrictive root/NAS metadata made the host Files snapshot unreadable; after the permanent ownership-normalisation correction was deployed, backup `20261007-145013Z` successfully captured both PostgreSQL dump formats plus 89 durable Files / 100032776 bytes, verified exact path/size/SHA-256 equality, validated schema-2 media before and after atomic promotion, restored the prior responder-running state, and the responder subsequently reported healthy. Existing database-only helpers remain unchanged. See [`evidence/Step 8`](evidence/Step%208/README.md).
- **Step 9 complete — 2026-10-07:** the full destructive rehearsal passed on the dedicated `0033-step9-rehearsal` local-docker-build database/Files pair. The successful `runtime-20261007-182222Z` run created and independently validated complete backup `20261007-182222Z` (schema 2; 89 durable Files / 100032776 bytes), exercised all ten required negative/fail-safe cases, created mandatory safety backup `20261007-182712Z`, applied the complete restore through the permanent Step 5–7 commands, proved the intentionally failed postflight kept the writer stopped, then completed accepted postflight with `synchronise: ok`, retained MARQUEE + IMAGE payload verification and representative `/files` byte verification. The database+Files fingerprint returned exactly to the pre-backup baseline, the safety backup itself passed restore preflight, client + reader service returned HTTP 200, only the previously-running `local-docker-build` responder was restored, and temporary host settings plus `local.env` were restored. See [`evidence/Step 9`](evidence/Step%209/README.md).
- **Step 10 complete — 2026-10-07:** the already-successful Step-8 rollout and production backup `20261007-145013Z` are accepted as the non-destructive production exercise required for close-out, avoiding a needless second production writer-quiescence window. Local and production operating documentation now records when to use database-only versus complete-dataset backup, media layout/boundary, effective identity, downtime/failure state, independent verification, phased restore, mandatory safety backup, exact Files replacement, rollback and staging policy. The final script inventory classifies every 0033 live script as permanent operational or permanent regression tooling and confirms the Step-9 rehearsal harness is evidence-only. All acceptance criteria are satisfied; 0033 is closed and moved to `change-control/complete`. See [`evidence/Step 10`](evidence/Step%2010/README.md).

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

Step 2 freezes schema version 2 with these required identities and completion facts:

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

The authoritative field structure, path rules, inventory format and compatibility policy are recorded in [`evidence/Step 2/README.md`](evidence/Step%202/README.md), with a complete generated example in [`complete-dataset-manifest.example.json`](evidence/Step%202/complete-dataset-manifest.example.json). Required schema-2 fields/components cannot be renamed or weakened without a new schema version; compatible additive fields are permitted. Restore must validate a supported schema before making any destructive change.

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

- [x] An operator can create one complete backup directory for the current effective dataset with one command.
- [x] The directory contains a valid custom/binary database dump, a valid SQL database dump, an exact verified durable Files snapshot, and one complete-dataset manifest.
- [x] The backup identity is based on the effective database + Files pair, including `local.env` overrides.
- [x] A shared local `common` dataset is represented as one dataset regardless of which local mode invokes the operation.
- [x] A partial/interrupted backup cannot be mistaken for a completed backup.
- [x] Checksums/inventories detect changed, missing or extra durable Files in a backup.
- [x] Unexplained `.image-staging` content blocks or explicitly suspends completion for review.
- [x] A complete restore accepts one complete backup directory and restores the database + Files together.
- [x] The normal complete restore uses the custom/binary dump and verifies the SQL companion without applying both.
- [x] Restore verifies all backup components before destructive work begins.
- [x] Restore rejects a mismatched effective database/Files target by default.
- [x] Files restore is replace/exact semantics rather than merge semantics.
- [x] Restore has a documented safety-backup and rollback path for partial failure.
- [x] Failed restore/postflight does not automatically return the application to a writable state.
- [x] Postflight proves database/Image/Files reconciliation and successful retained-state replay.
- [x] Existing database-only backup/restore scripts remain supported and explicitly labelled database-only.
- [x] Equivalent permanent production backup/restore tooling is deployed through Playbooks.
- [x] A complete backup and destructive restore have been rehearsed successfully in a disposable environment.
- [x] Production complete backup has been exercised non-destructively and verified.
- [x] Documentation clearly explains what is and is not contained in a complete Diaries dataset backup.
- [x] Permanent tooling follows 0032 script-directory hygiene; feature-only rehearsal/evidence tooling is archived with the change record.

## Deployment and rollback

The feature can be rolled out additively because the current database-only commands remain intact.

Do not replace operational practice with the new complete-dataset tooling until:

1. backup verification passes on representative local datasets;
2. a destructive restore rehearsal proves database + Files recovery into a disposable target;
3. production script rendering/deployment is verified;
4. a production complete backup is captured and independently verified.

If the new complete-dataset tooling is found defective before it has been relied upon for recovery, remove/disable the new entry points and continue using the existing database-only helpers plus separately managed Files snapshots. Never discard an existing verified backup merely because a newer backup format has been introduced.
