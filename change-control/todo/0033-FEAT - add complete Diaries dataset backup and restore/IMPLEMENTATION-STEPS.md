# 0033-FEAT - Implementation Steps

Prepared 2026-10-05 from the completed 0031/0032 change-control records, the current Diaries local backup/restore scripts, and the current Diaries Playbooks production backup/restore tooling.

## Objective

Implement one supported **complete dataset backup and restore** path for Diaries:

```text
complete dataset
    = effective PostgreSQL dataset
    + matching mutable Files root
```

A completed backup is one self-contained directory containing both PostgreSQL backup representations, a verified Files snapshot and a manifest proving the pairing.

A completed restore consumes that directory and restores database + Files together, with strict preflight, replacement semantics for Files, rollback protection and post-restore reconciliation.

The existing database-only commands stay supported throughout this feature.

## Working rules

1. 0031's one-database/one-Files-root invariant is non-negotiable.
2. Always resolve effective configuration after `local.env`; never label a local backup from the launch-mode default alone.
3. Quiesce every writer which can reach the selected dataset before taking a coherent backup or applying a restore.
4. Keep PostgreSQL available while dumps are taken; stopping the whole stack indiscriminately is not sufficient if it also stops the database.
5. A complete backup is not valid until all components and verification metadata are complete.
6. Build under a temporary/incomplete directory and promote only after validation.
7. The PostgreSQL custom/binary dump is the normal restore source. The SQL dump is a second representation, not a second restore pass.
8. Restore Files exactly; do not merge them into the current root.
9. Inspect `.image-staging`; do not blindly propagate or restore unexplained transient state.
10. MQTT retained state is regenerated/replayed and is not part of backup media.
11. The shared original diary scan tree is read-only source content and is outside this feature's complete-dataset boundary.
12. Prefer common implementations with thin mode-specific wrappers.
13. Production restore must be rehearsed in a disposable environment before any production recovery procedure depends on it.
14. Any feature-only rehearsal scripts belong under 0033 evidence/tooling, not permanent live script directories, in accordance with 0032.

---

## Step 1 — Freeze the existing database-only tooling and effective dataset contract

Capture the current supported behaviour before adding complete-dataset commands.

Document and regression-freeze:

```text
local database-only binary backup
local database-only SQL backup
local binary restore
local SQL restore
.dataset.json sidecars
production equivalents in Playbooks
```

For each local mode and production, record:

```text
how effective database identity is resolved
how effective Files identity is resolved
backup directory naming
which service/container performs pg_dump/pg_restore
how responder/application writers are currently stopped during restore
manifest helper used
```

Explicitly prove the normal shared local configuration is one effective `common` dataset when `local.env` selects both common database and common Files root.

Add/extend permanent tests so 0033 cannot accidentally change the existing database-only semantics while building the new layer.

**Evidence:** current command inventory, effective dataset examples, current manifest examples, regression output.

**Complete when:** the pre-0033 database-only behaviour and 0031 pairing contract are frozen by repeatable checks.

---

## Step 2 — Define and validate the complete-backup directory and manifest contract

Implement the format contract before writing live data-copy orchestration.

Freeze a common logical layout such as:

```text
<dataset-backup-root>/
└── <logical-dataset>/
    └── <timestamp>/
        ├── dataset-manifest.json
        ├── database/
        │   ├── diaries.dump
        │   └── diaries.sql
        ├── files/
        └── verification/
            ├── database.sha256
            ├── files.sha256
            └── inventory.json
```

Define:

- timestamp/backup ID rules;
- supported manifest schema/version;
- required component names;
- relative-path-only references inside the manifest;
- database format/size/hash fields;
- Files selector/root identity and inventory fields;
- Image row count and durable file count;
- source/runtime identity;
- writer-quiescence record;
- staging disposition;
- completion status;
- compatibility rules for future schema versions.

Decide the incomplete-work convention. Prefer either:

```text
.<backup-id>.partial/
```

or another unambiguously non-restorable temporary name, followed by same-filesystem promotion to the final directory only after successful verification.

Add a standalone manifest validator which can reject:

```text
missing components
absolute/escaping component paths
unsupported schema
completeDatasetBackup != true
wrong backupType
missing/invalid hashes
invalid dataset identity
status != complete
```

**Evidence:** schema/design note, example manifest, validator unit/regression results.

**Complete when:** a synthetic complete backup can round-trip through manifest generation and validation without performing a real database/Files backup.

---

## Step 3 — Implement the common local complete-dataset backup engine

Add a permanent common PowerShell implementation and thin wrappers for the supported local modes, rather than copying substantial logic into three `.bat` files.

Expected permanent entry points are conceptually:

```text
scripts/windows/<mode>/backup-dataset.bat
scripts/windows/common/backup-dataset.ps1
```

The exact names may be refined, but the operator command should be obvious and behaviour-oriented.

The backup engine must:

1. load/accept the mode environment followed by `local.env`;
2. invoke the existing dataset-pair validation;
3. resolve `DIARIES_DATASET_NAME`, effective database data and effective Files root;
4. derive the complete-backup namespace from the effective dataset;
5. identify the database container/service and current responder/writer state;
6. refuse to continue if the selected Files root is unavailable;
7. inspect `.image-staging` and stop for unexplained staged content;
8. quiesce all writers for the selected pair while keeping PostgreSQL available;
9. create the custom/binary dump;
10. create the plain SQL dump while the dataset remains quiesced;
11. copy the durable Files tree to the temporary backup directory;
12. preserve required path/file attributes for later restore;
13. retain the prior application-running state so it can be restored only after a successful/clean backup finalisation;
14. leave a clear failed/incomplete artifact rather than falsely promoting partial output.

Where multiple local modes share `common`, invoking the backup from any of them must create one `common` dataset backup, not mode-specific duplicates.

**Evidence:** static tests, focused helper tests, successful isolated/default and shared-common dry/preflight output, controlled failure cases.

**Complete when:** a local complete backup captures both database formats and Files bytes under one incomplete backup workspace with writers demonstrably quiesced.

---

## Step 4 — Add complete backup verification and atomic promotion

Turn the captured workspace into a trustworthy backup artifact.

Generate and verify:

```text
SHA-256 of diaries.dump
SHA-256 of diaries.sql
complete relative-path/SHA-256 Files inventory
file count
total Files bytes
Image row count
catalogued-file/reconciliation count where available
```

Validate the custom dump using PostgreSQL tooling (`pg_restore --list` or equivalent) and perform a safe syntax/readability check of the SQL dump appropriate to its format.

Compare the source durable Files inventory with the captured Files snapshot while writers remain quiesced. Any missing, extra or hash-different durable file fails completion.

Write `dataset-manifest.json` only from verified facts. The manifest must refer to backup-relative component paths, not machine-specific backup paths.

Run the manifest validator against the completed candidate. Only then promote the temporary directory to the final `<timestamp>`/backup-ID directory.

The final output must clearly report:

```text
Operation: COMPLETE DATASET backup
logical dataset
database identity
Files identity
final backup directory
binary dump
SQL dump
file count/bytes
manifest
verification result
```

Add regression tests proving an interrupted or corrupt candidate cannot be selected as a valid complete backup.

**Evidence:** successful backup transcript, final manifest, inventories, intentional corruption/failure test results.

**Complete when:** one command creates a self-contained, independently verifiable local complete backup directory which cannot be confused with a partial backup.

---

## Step 5 — Implement complete restore preflight, safety backup and Files staging

Implement a common restore engine with thin local-mode wrappers, conceptually:

```text
scripts/windows/<mode>/restore-dataset.bat
scripts/windows/common/restore-dataset.ps1
```

The restore input is a complete backup directory.

Before destructive work, it must:

1. resolve/validate the current effective target database + Files pair;
2. locate and validate `dataset-manifest.json`;
3. require `backupType=complete-dataset`, `completeDatasetBackup=true` and completed status;
4. verify both database artifacts and every recorded checksum/inventory;
5. validate the custom dump with PostgreSQL tooling;
6. verify the target dataset/Files identity matches the manifest by default;
7. reject ordinary database-only `.dataset.json` manifests as complete restore inputs;
8. inspect current target staging/transient state;
9. calculate/check required temporary/rollback space as far as practical;
10. require explicit destructive confirmation;
11. quiesce all writers for the target pair;
12. create a pre-restore complete safety backup by default, or require an explicit exceptional override with prominent evidence;
13. stage the selected backup's Files into a temporary sibling/working location and reverify its inventory before altering the live Files root.

Do not yet replace the live database/Files in this step.

**Evidence:** preflight output, mismatch/corruption rejection tests, staged Files inventory, safety-backup proof.

**Complete when:** a restore can reach a fully verified, writer-quiesced, rollback-protected state with the replacement Files tree staged, without having changed the live dataset yet.

---

## Step 6 — Apply database + Files restore as one controlled operation

Complete the destructive restore path.

The normal database source is:

```text
database/diaries.dump
```

Use the proven current custom-format database restore mechanics. Do not apply `diaries.sql` after the custom dump.

The Files transition must use replacement/exact semantics. Prefer staging plus directory rename/swap where the filesystem supports it. If the NAS/filesystem requires a different mechanism, it must still guarantee that files absent from the backup do not survive merely because they existed in the current target.

Maintain explicit rollback state for both halves until postflight succeeds. If either database or Files application fails:

- do not restart/re-enable writers;
- report which half changed;
- preserve enough information to restore the pre-restore safety backup;
- provide a documented rollback command/path.

Do not restore stale `.image-staging` payloads. Recreate only the normal empty/runtime staging structure required by the responder.

**Evidence:** disposable restore transcript, before/after database identity, before/after Files inventory, intentional apply-failure test where practical.

**Complete when:** a disposable target can be replaced from one complete backup and no pre-restore extra Files remain in the restored durable tree.

---

## Step 7 — Add post-restore reconciliation, retained replay and failure-safe restart

Before returning the application to service, run a deterministic postflight.

Verify at least:

```text
expected database is present and queryable
Image row count matches manifest
restored Files inventory matches manifest exactly
Image catalogue reconciliation has no unexplained missing/untracked/conflicting file
/files URL mapping still targets the selected mutable Files root
responder starts successfully
retained database-backed topic tree is rebuilt/replayed
representative MARQUEE and IMAGE content is readable
```

Where a count is not sufficient to prove identity, use the existing reconciliation/checksum tooling rather than relying only on totals.

Application writer state may be restored to its prior state only after postflight succeeds. On postflight failure the safe default is stopped/non-writable with a clear rollback instruction.

Add permanent regression coverage for failure-state behaviour.

**Evidence:** postflight report, MQTT/replay evidence, reconciliation output, HTTP/static Files verification, failed-postflight test.

**Complete when:** restore success is defined by database + Files + responder/replay reconciliation, not merely by `pg_restore` exit status.

---

## Step 8 — Add production complete-dataset tooling through Playbooks

Implement Linux/production equivalents in the Diaries Ansible role, preferably sharing a common Python helper for manifest/inventory logic where that reduces Windows/Linux schema drift.

Expected operational commands are conceptually:

```text
backup-dataset.sh
restore-dataset.sh
```

alongside the existing database-only helpers.

Production tooling must:

- derive identity from the deployed `.env` and explicit `DIARIES_FILES_DIR` generated from `diaries_files_dir`;
- preserve the existing production `files` pairing unless deliberately reconfigured;
- quiesce the responder/application service but keep PostgreSQL available during capture/restore;
- handle NAS Files copy/read/write failures explicitly;
- write complete backup artifacts outside the live mutable Files tree;
- use the same manifest schema and restore safety semantics as local tooling;
- remain idempotently deployed/cleaned according to the 0032 managed script-directory policy.

Update Playbooks tests to validate script deployment, executable permissions, manifest schema compatibility and explicit Files-root selection.

Do not perform a destructive production restore as part of routine rollout.

**Evidence:** Playbooks test results, Ansible check/apply output, deployed script inventory, rendered configuration proof.

**Complete when:** production has the same supported complete-backup format and restore semantics as local tooling, deployed by Ansible without weakening the existing database-only commands.

---

## Step 9 — Run full disposable backup/restore rehearsal

Use a disposable environment containing representative Diaries state, including:

```text
MARQUEE Fragments
IMAGE Fragments
reused Image references
multiple durable Files
nested Files paths where supported
known catalogue metadata/checksums
```

Record a pre-backup fingerprint including database entity counts/selected row identities and complete Files SHA-256 inventory.

Then:

1. create a complete backup;
2. independently validate it;
3. deliberately mutate the disposable database;
4. deliberately add/change/delete Files in the disposable target;
5. perform the complete restore;
6. prove the database returns to the backup state;
7. prove the Files tree returns exactly to the backup state, including removal of post-backup extra files;
8. restart/replay responder state;
9. verify client/reader/static-file behaviour;
10. prove the pre-restore safety backup is itself valid/usable.

Also exercise negative cases:

```text
missing dump
modified dump
missing Files item
modified Files item
extra item inside backup snapshot
invalid manifest
mismatched target dataset
unexpected staging payload
interrupted backup
failed postflight
```

**Evidence:** full rehearsal package under `evidence/Step 9/`, with commands, manifests, before/after fingerprints and pass/fail summary.

**Complete when:** destructive recovery from one backup directory is repeatable and restores both halves exactly in a disposable environment.

---

## Step 10 — Roll out production backup, update operating documentation and close 0033

Deploy the final production tooling through the normal Diaries Playbooks path.

Run a **non-destructive production complete backup** with a controlled writer-quiescence window, then independently verify:

```text
manifest valid
binary dump valid
SQL dump present/valid
Files inventory complete
all hashes match
production database/Files identity correct
application successfully returned to service
post-backup health/read checks green
```

Do not restore over production merely to prove the restore script. The Step 9 destructive rehearsal is the restore proof unless an actual recovery event later requires production restoration.

Update normal operating documentation, including:

```text
when to use database-only backup
when to use complete-dataset backup
backup directory layout
how effective dataset identity is chosen
writer-quiescence/downtime expectation
how to verify a backup
how to perform a complete restore
pre-restore safety backup behaviour
rollback procedure
staging policy
what is deliberately not included
```

Review every new script according to 0032:

```text
KEEP-OPERATIONAL
KEEP-REGRESSION
ARCHIVE/REMOVE feature-only tooling
```

Move 0033 to `complete` only when the acceptance criteria in `README.md` are evidenced and no feature-only rehearsal tooling remains in live script directories.

**Evidence:** production backup verification, documentation diff, final script inventory/classification, close-out summary.

**Complete when:** complete-dataset backup is a supported production operation, complete restore is proven in rehearsal, documentation is current, and 0033 can be closed without weakening 0031/0032 invariants.

---

## Recommended implementation order

Implement the steps in order. In particular:

```text
Do not implement destructive restore before the backup artifact/validator is stable.
Do not roll production tooling out before disposable restore rehearsal is green.
Do not claim complete backup support while database and Files are still captured independently without shared verification.
```

The feature is intentionally additive: if work must pause after any early step, the existing database-only backup/restore tooling remains the supported baseline.
