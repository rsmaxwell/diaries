# 0031-FEAT - Isolate mutable Files storage by database environment

## Type

Feature

## Status

Complete

## Completed Date

2026-10-03

## Priority

High

## Opened

2026-09-28

## Implementation progress

- **Step 1 complete — 2026-10-01:** the effective pre-change topology is frozen under [`evidence/Step 1`](evidence/Step%201/README.md). The three local modes are one common database dataset when `local.env` selects `./data/database/common`; they intentionally share one Files tree. Production is a separate database dataset but currently shares that same mutable physical Files root, which is the cross-dataset defect this feature will remove. No runtime data or configuration was changed by Step 1.
- **Step 2 complete — 2026-10-01:** the final dataset-to-Files-root map and configuration contract are frozen under [`evidence/Step 2`](evidence/Step%202/README.md). Production keeps `files`; isolated local defaults use `files-development-infrastructure`, `files-local-docker-build`, and `files-local-published-smoke`; and the normal intentionally shared local dataset uses `files-development-common` together with `DIARIES_DB_DATA_DIR=./data/database/common`. The approved selectors are `DIARIES_FILES_DIR` locally/runtime and `diaries_files_dir` in Playbooks. No runtime configuration or storage was changed by Step 2.
- **Step 3 complete — 2026-10-01:** all three committed local mode environments now define an explicit `DIARIES_FILES_DIR`; `local.env.example` demonstrates the paired common override; and both local Docker responder mounts select `/data/files` from `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`. The Compose expressions use required-variable interpolation so an entirely missing selector fails during configuration rather than falling back to `files`. A repeatable static validation is in `scripts/windows/validation/verify-0031-step3.py`. The ignored real `local.env` is intentionally not committed and must contain `DIARIES_FILES_DIR=files-development-common` whenever it selects `DIARIES_DB_DATA_DIR=./data/database/common`. No NAS directory has been created or copied yet.
- **Step 4 complete — 2026-10-02:** direct Windows development now uses `scripts/windows/development-infrastructure/prepare-responder-config.bat` plus its PowerShell JSON helper to load `development-infrastructure.env` followed by `local.env`, require both dataset selectors, and generate an ignored `build/development-infrastructure/responder.effective.json` from the developer-owned base config with only `diaries.files` replaced. `run-responder.bat` and `migration0024ImageCatalogue.bat` consume the same generated config. `UploadFile` now keeps its public URL rooted at `/files` independently of the physical Files directory, with a regression test using `files-development-common`. The first Windows runtime-verifier run confirmed the expected common database and `files-development-common` paths, then exposed a verifier-only quoting defect where `^|` reached PowerShell literally; that verifier is corrected and the static checker now guards the pipeline syntax. The corrected workstation runtime verifier then passed on 2026-10-02 (`runtime-verification-success-20261002-070435.txt`), proving the effective common database/Files pair and the stable public `/files/...` contract. No NAS files or database rows were changed by Step 4.
- **Step 5 complete — 2026-10-03:** the production Diaries Ansible role now requires an explicit `diaries_files_dir`, renders it as `DIARIES_FILES_DIR`, selects the mutable `/data/files` mount from `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`, and validates both rendered files. There is deliberately no role default, so missing or invalid selectors fail before deployment. The external production inventory was subsequently configured with `diaries_files_dir: files`, and Step 14 proved the rendered/deployed production selector and `/data/files` mount non-destructively on `pluto`. Source verification is recorded under [`evidence/Step 5`](evidence/Step%205/README.md), with deployed-runtime proof under [`evidence/Step 14`](evidence/Step%2014/README.md).
- **Step 6 complete — 2026-10-02:** a shared Windows preflight validates the effective database/Files pair before any of the three local launch paths or the direct responder/reconciliation configuration path can use it. It rejects one-sided `local.env` overrides, rejects the production `files` root in local modes, and rejects crossed combinations for the four frozen 0031 database leaves (`development-infrastructure`, `local-docker-build`, `local-published-smoke`, and `common`). Portable regression checks prove distinct isolated defaults, the deliberately shared common pair, both local Docker mount contracts, the shared diary-scan path, and the stable `/files/...` public URL. The Playbooks role also has a repository-level production storage-isolation test and verifies the rendered shared `/diaries` scan mount. Two earlier Windows runs exposed and drove fixes for a PowerShell interpolation defect and a verifier-only expected-error handling defect. The final Windows workstation rerun passed all six positive isolated/common cases and all four intentional mismatch rejection cases, ending with `PASS: 0031-FEAT Step 6 Windows dataset-pair regression checks`. The exact successful output and the earlier regression history are retained under [`evidence/Step 6`](evidence/Step%206/README.md). The Step 6 completion criterion is therefore satisfied: the accidental storage re-sharing/mismatched-override cases are covered by repeatable regression guards and verified on the supported Windows launch tooling.
- **Step 7 complete — 2026-10-02:** local and production database backup/restore helpers now distinguish `DATABASE-ONLY` operations from a complete recoverable Diaries dataset, derive backup identity from the effective database dataset, report the matching Files selector/root, write a `.dataset.json` pairing sidecar for new backups, and reject sidecar-backed restores when the recorded database/Files pair does not match the current effective pair. The normal shared local override therefore uses one `common` backup namespace regardless of launch mode. Legacy dumps remain usable only with an explicit warning that the matching Files tree must be verified manually. Portable Diaries and Playbooks regression checks pass and production shell helpers pass syntax validation. The actual Files snapshot is deliberately deferred to Step 8; Step 7 closes the semantics/pairing problem without claiming that Files bytes have already been backed up. Evidence is retained under [`evidence/Step 7`](evidence/Step%207/README.md).
- **Step 8 complete — 2026-10-02:** local and production mutable responder writes were frozen; the effective local `common` database and production database were backed up; and the old shared `files` tree was copied to the dedicated rollback snapshot. The source and snapshot SHA-256 inventories matched exactly (90 files, 100032776 bytes), and the one `.image-staging` item was retained for rollback but explicitly marked for later review rather than blind propagation. Evidence and close-out are retained under [`evidence/Step 8`](evidence/Step%208/README.md). Both responder write paths remain intentionally frozen for Step 9.
- **Step 9 complete — 2026-10-02:** the effective local `common` database and production database were each reconciled read-only against the frozen pre-split shared `files` tree. Both runs found 85 Image rows, 85 matching physical files, 0 missing files, 0 untracked supported images, 0 metadata/checksum conflicts and 0 reconciliation conflict rows. Both also found the same four unsupported `Thumbs.db` files and the same zero-byte `.image-staging/catalogue.lock`; those entries have explicit reviewed dispositions as non-application/transient state and require no database or source-tree repair. The script-level `REVIEW REQUIRED` gate is therefore resolved by review, and Step 10 may begin while both responder write paths remain frozen. Evidence and close-out are retained under [`evidence/Step 9`](evidence/Step%209/README.md).
- **Step 10 complete — 2026-10-02:** the frozen shared source still matched the Step 8 SHA-256 baseline exactly (90 files, 100032776 bytes), and the normal local `common` dataset was seeded to exactly one candidate root, `files-development-common`. The approved seed contained 89 files / 100032776 bytes; the reviewed zero-byte `.image-staging/catalogue.lock` was deliberately excluded; the complete temporary-target SHA-256 inventory matched the approved source seed; and the create/write/read/delete permission probe passed. Source and target ACL captures were reviewed and are equivalent, so the new root is not more broadly writable than the old shared root. The old `files` source and Step 8 rollback snapshot remain retained, and both responder write paths remain frozen for Step 11. Evidence and close-out are under [`evidence/Step 10`](evidence/Step%2010/README.md).
- **Step 11 complete — 2026-10-02:** all three local modes were repointed and verified against the intended common durable pair `./data/database/common` + `files-development-common`. Direct Windows development resolved its generated responder configuration to the selected Files root; both Docker modes rendered the matching PostgreSQL host data directory and bound the selected NAS subpath to stable `/data/files`; the original `/data/diaries` scan tree remained shared/read-only; and `/files/...` plus `/diaries/...` returned HTTP 200. The authoritative successful captures are `development-infrastructure-20261002-170911`, `local-docker-build-20261002-172734`, and `local-published-smoke-20261002-172947`. The final cross-mode comparison passed and wrote `STEP11-RUNTIME-SUMMARY.json`. Verification was non-destructive and explicitly confirmed no upload/delete/rename operations. Evidence and close-out are retained under [`evidence/Step 11`](evidence/Step%2011/README.md).
- **Step 12 complete — 2026-10-02:** both independent post-split durable database/Files pairs were reconciled read-only against their Step 9 pre-split baselines. The local common pair `./data/database/common` + `files-development-common` passed in `local-common-20261002-182452`; the production pair retained `DIARIES_FILES_DIR=files` and passed in `production-20261002-184656`. Both 0024 dry-run reconciliations completed successfully and the Step 12 semantic comparisons reported `PASS`, with no catalogue/File drift introduced by the storage split. No Image rows or physical files were mutated. Step 12 is therefore closed and Step 13 controlled cross-dataset lifecycle testing may begin while the production write freeze remains in force until the Step 13 procedure explicitly requires otherwise. Evidence and close-out are retained under [`evidence/Step 12`](evidence/Step%2012/README.md).
- **Step 13 complete — 2026-10-03:** the controlled cross-dataset lifecycle proof passed end-to-end. `development-infrastructure` uploaded Image 88 into the normal common pair; `local-docker-build` independently observed the same database row, retained Image, physical bytes and `/files/...` URL because it intentionally consumes that same durable pair; the supported `deleteImage` path then removed the local row, retained state and physical file. Production BEFORE (`production-before-20261002-203216`) and AFTER (`production-after-20261003-083327`) controls matched byte-for-byte for both the deterministic Image-row capture and complete production `/data/files` SHA-256 inventory. Step 13 also closed the retained-snapshot >10,000-message runtime blocker and local-Docker CIFS staging-permission mismatch. See [`evidence/Step 13`](evidence/Step%2013/README.md) and [`CLOSE-OUT.md`](evidence/Step%2013/CLOSE-OUT.md).
- **Step 14 complete — 2026-10-03:** the explicit production configuration was deployed and activated non-destructively. Preflight `preflight-20261003-090612` passed with responder writes still frozen. The production role validated `DIARIES_FILES_DIR=files`, the selected `/data/files` mount, `max_inflight_messages 20`, and interim `max_queued_messages 0`. Because the post-preflight Ansible copy run was idempotent (`changed=0`), activation was performed through the installed systemd unit on `pluto`; all five Diaries containers became healthy and shared Nginx validation passed. Postflight `postflight-20261003-091828` then proved retained-tree synchronisation, unchanged production/non-production durable controls, stable `/files` serving, and a fresh Step 12 production reconciliation (`production-20261003-091922`) that still matched the Step 9 semantic baseline. The helper ended `PASS: Step 14 production deployment is healthy and non-destructive.` See [`evidence/Step 14`](evidence/Step%2014/README.md) and [`CLOSE-OUT.md`](evidence/Step%2014/CLOSE-OUT.md).
- **Step 15 complete — 2026-10-03:** the dataset/Files pairing invariant is now documented as normal architecture and operating practice outside the 0031 implementation material. The top-level README and architecture describe effective configuration, isolated defaults, the intentional common-local pair, shared read-only diary scans, environment-neutral `/files/...`/`Image.relativePath`, matched backup/restore and re-sharing hazards. The responder README and `local.env.example` document leaf-selector/direct-Windows semantics; a new `scripts/windows/README.md` gives local operator procedures; and the Playbooks role plus production script README document `diaries_files_dir` and matched production recovery. Static review evidence is under [`evidence/Step 15`](evidence/Step%2015/README.md).
- **Step 16 complete — 2026-10-03:** the exact corrected release candidate passed the full cross-repository regression in `final-regression-20261003-104658`: all accumulated Diaries 0031 gates passed, all production Playbooks validators passed remotely on `mango`, the full Java responder/web suite ended `BUILD SUCCESSFUL`, and the Angular production build passed. The preserved Step 8 common database backup was also restored into disposable PostgreSQL and reconciled read-only against `files-development-common` in `restore-rehearsal-20261003-104511`; Gradle ended `BUILD SUCCESSFUL` and the rehearsal reported `PASS: Step 16 disposable common-dataset restore/reconciliation rehearsal succeeded.` The final acceptance matrix has no pending row, rollback remains matched-pair/no-auto-merge, and 0031 is closed. See [`evidence/Step 16`](evidence/Step%2016/README.md).

## Summary

Separate the mutable Diaries `files` tree between database environments/datasets so that an Image upload, replacement or deletion in one environment cannot make another environment inconsistent.

The PostgreSQL database and mutable Files root must be treated as one logical dataset. A responder may use a Files root only when that Files root belongs to the same dataset as the database to which the responder is connected.

The read-only original diary content under `diaries` is not affected by this rule and may continue to be shared between environments.

## Problem

Development and production currently use separate PostgreSQL data, but the mutable image/file storage can resolve to the same physical NAS `files` directory.

That was tolerable while Files were effectively read-only. It is no longer safe now that the Image catalogue supports lifecycle operations such as upload and deletion.

For example:

```text
Development database                    Production database
        |                                      |
        |                                      |
        +---------------+  +-------------------+
                        |  |
                        v  v
                  shared NAS /files
```

If development deletes a catalogued Image:

```text
development Image row       -> deleted
shared physical file        -> deleted
production Image row        -> still present
```

Production is then inconsistent: its database and retained Image catalogue can refer to a physical file that no longer exists.

The reverse is equally dangerous. Production activity must not alter the physical bytes expected by a development database.

## Implementation evidence

At feature opening and through Step 2, the local Docker compositions mounted the mutable Files tree using:

```text
${DIARIES_NAS_CONTENT_PATH}/files -> /data/files
```

in both:

```text
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
```

Step 3 replaced the two local mutable mounts with the explicit required `DIARIES_FILES_DIR` selector. Step 5 now applies the same explicit selector contract to the production Diaries Ansible role. The generated production `.env` contains `DIARIES_FILES_DIR={{ diaries_files_dir }}`, and `roles/diaries/templates/compose.yaml.j2` uses `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR} -> /data/files`. The production inventory must explicitly supply `diaries_files_dir: files`; the role has no fallback to the old production path.

The responder documentation also records that local modes can address the same physical NAS Files tree.

This feature changes that assumption. Sharing mutable Files is valid only when the corresponding modes intentionally use the same database dataset.

## Core invariant

The required invariant is:

```text
one database dataset <-> one mutable Files root
```

More precisely:

```text
Database identity A + Files root A = valid
Database identity B + Files root B = valid
Database identity A + Files root B = configuration error
```

Two runtime modes may intentionally share the same Files root only when they intentionally share the same database dataset and are therefore two ways of accessing the same logical data.

Retained MQTT state is not part of the durable pair because it can be rebuilt from the database. It must nevertheless be environment-specific during normal operation so that retained state from one database does not shadow another.

## Storage model

### Shared read-only source material

The existing original diary-page content may remain shared:

```text
.../diaries-content/diaries
```

It is mounted read-only by Docker and is not owned by the Image catalogue lifecycle.

### Dataset-specific mutable Files

Mutable catalogued files must use distinct physical roots. A suitable initial layout is:

```text
.../diaries-content/diaries                         shared read-only diary scans

.../diaries-content/files                           production mutable Files
.../diaries-content/files-development-infrastructure development mutable Files
.../diaries-content/files-local-docker-build         local-docker-build mutable Files
.../diaries-content/files-local-published-smoke      local-published-smoke mutable Files
```

Step 2 freezes these directory names as the approved committed-default roots. It also defines `files-development-common` for the intentionally shared local dataset selected by the normal `local.env` override.

The existing production `.../files` path will remain where it is. This minimizes production migration risk. New non-production roots will be created by copying the existing tree and then reconciling each copy against its corresponding database before destructive Image lifecycle testing.

If two local modes are deliberately configured to use the same PostgreSQL data directory/database, they should also be configured to use the same mutable Files root. Do not share one without the other.

## Configuration design

Do not encode environment names in responder Java code.

Continue to present the responder with the normal runtime path:

```text
/data/files
```

inside Docker. Select the physical backing root at deployment/configuration level.

Step 2 freezes one explicit mutable Files **leaf-directory selector**:

```text
DIARIES_FILES_DIR
```

Its value is the directory name beneath `DIARIES_NAS_CONTENT_PATH`, for example:

```text
files
files-development-infrastructure
files-local-docker-build
files-local-published-smoke
files-development-common
```

Change Docker mounts from:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/files
```

to:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

`DIARIES_NAS_CONTENT_PATH` continues to identify the common content root used for both the selected mutable Files child and the shared read-only `diaries` child. Using a leaf selector also lets direct Windows development apply the same effective value to `diaries.files` beneath its configured responder root.

The mutable Files selector must be explicit rather than silently falling back to `files`. A missing value must fail deployment/startup configuration instead of accidentally returning an isolated database to the production/shared mutable directory.

For the direct Windows development responder, keep the developer-owned `%USERPROFILE%\.diaries\responder.json` as the base configuration. Step 4 generates an ignored effective copy under `build/development-infrastructure/` after loading `development-infrastructure.env` and then `local.env`. Only `diaries.files` is replaced, using the effective `DIARIES_FILES_DIR`; `diaries.root`, `diaries.diaries`, credentials and unrelated settings remain those from the developer-owned base.

For the normal shared local dataset, `local.env` therefore selects the pair:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

and direct Windows development resolves the mutable Files root as `diaries.root/files-development-common` while continuing to serve it publicly under `/files/...`.

No persisted `Image.relativePath` value should contain an environment prefix. `relativePath` remains relative to the configured Files root, so the same logical Image catalogue can be restored into another dataset-specific Files root when deliberately cloning/restoring an environment.

## Production Ansible design

Extend the Diaries role with the Step 2 approved variable:

```yaml
diaries_files_dir: files
```

and render it into `.env` as:

```text
DIARIES_FILES_DIR=files
```

Update:

```text
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
```

The production host variables must explicitly identify the production Files directory selector. Combined with `DIARIES_NAS_CONTENT_PATH`, this resolves to the existing production `.../diaries-content/files` root.

Add an Ansible assertion/preflight where practical so the required mutable Files path cannot be omitted.

Do not copy development Files into production as part of normal deployment.

## Local-mode design

Update:

```text
config/environments/local-docker-build.env
config/environments/local-published-smoke.env
```

and any mode-specific setup/documentation so each local database dataset has an explicit corresponding Files root.

`development-infrastructure` runs the responder directly on Windows and therefore also needs its developer responder configuration/documentation updated to point at the development Files root.

If `local.env` deliberately overrides database storage so multiple local modes share one database dataset, the Files-root override must follow the same grouping.

Document this as a pair, for example:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Never configure only one half of that pair as shared.

Step 3 implements this local environment/Compose contract. Direct Windows responder consumption of the effective selector is deliberately deferred to Step 4.

## Backup and restore rule

Database backup/restore and mutable Files backup/restore are related but remain distinct operations. Step 7 makes that distinction executable rather than relying only on operator memory.

The existing `backup-db-*` and `restore-db-*` scripts are explicitly **database-only**. They never claim to include or restore mutable Files bytes. Before operating, local scripts load the committed mode environment followed by `local.env`, validate the paired selectors, and derive backup identity from the **effective** `DIARIES_DB_DATA_DIR`. Consequently, when all three local launch modes use:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

they all address one backup namespace:

```text
data/database-backups/common/
  diaries-common-<timestamp>.dump
  diaries-common-<timestamp>.dump.dataset.json
```

They do not create three mode-labelled backups of the same durable dataset. Isolated defaults similarly use `development-infrastructure`, `local-docker-build`, or `local-published-smoke` as the effective database leaf.

Each new database backup receives a `.dataset.json` sidecar recording at least:

```text
backupType = database-only
completeDatasetBackup = false
logical/effective database dataset identity
database backup filename, format and timestamp
effective DIARIES_FILES_DIR
resolved physical Files root
application/source identity
Image row count / catalogued-file count
filesSnapshot = null
```

A sidecar-backed restore must match the current effective database + Files pair. A mismatch is rejected before the database is dropped. Older backups without a Step-7 sidecar remain restorable, but the scripts emit an explicit warning that the operator must verify the matching Files root manually.

Production applies the same semantics. Its database identity is the production Docker database volume, and its sidecar records the production `DIARIES_FILES_DIR` plus resolved NAS Files root.

For any backup intended to be a **complete recoverable Diaries dataset**, preserve together:

```text
PostgreSQL database backup
matching mutable Files root snapshot/copy
Step-7 dataset/path identity manifest
application/source identity
optional reconciliation/checksum inventory
```

The Step-7 database sidecar is intentionally not a Files snapshot. Step 8 takes and verifies the actual pre-migration Files snapshot while writes are frozen, then records the matching database + Files artifacts as one recovery unit. Restoring a database snapshot alone is never described as a complete dataset restore.

A database-only development reset remains permitted only when the operator deliberately accepts that Files reconciliation may be required before Image lifecycle testing.

## Migration strategy

The migration must be conservative because the currently shared Files tree may already have been affected independently by development and production operations.

### 1. Freeze mutable Image/File writes

Before splitting the roots, stop or otherwise prevent Image/File upload, replacement and deletion in both development and production.

### 2. Back up both durable sides

Take and verify:

```text
production database backup
development database backup
full backup/snapshot of the currently shared Files root
```

Record the current paths and relevant application versions.

### 3. Reconcile before copying

Run Image catalogue reconciliation/inventory separately against the production database and development database while both still point at the existing shared Files tree.

Record:

```text
matching Image rows/files
missing physical files
untracked physical files
checksum/metadata conflicts
```

Do not silently repair one environment using assumptions from the other.

### 4. Preserve the production path

Prefer to leave the current physical production Files tree at:

```text
.../diaries-content/files
```

This avoids an unnecessary production move.

### 5. Create the development/local Files root(s)

Create a physical copy of the current Files tree for each independent non-production database dataset.

Copy staging/hidden directories only when they are intentionally part of supported state. Do not carry abandoned temporary upload state blindly; inspect `.image-staging` and other transient content first.

### 6. Repoint non-production environments

Update direct-development and local Docker configuration to use their new Files roots.

Restart only the relevant non-production environment and confirm `/data/files` or the Windows responder path resolves to the expected physical directory.

### 7. Reconcile each new pair

For each database + Files-root pair, run the existing Image reconciliation tooling in dry-run mode first.

Do not enable destructive lifecycle testing until each environment has an explainable reconciliation result.

### 8. Verify isolation deliberately

Create a disposable test Image in development and prove:

```text
development DB row appears
development retained Image topic appears
development physical file appears
production DB is unchanged
production physical Files tree is unchanged
```

Then delete that Image in development and prove the same isolation in reverse.

Perform a non-destructive production read/reconciliation check afterward.

## Guard against accidental re-sharing

Configuration review/tests should make accidental reintroduction of a shared mutable root visible.

At minimum:

- local environment templates must name their Files-root variable explicitly;
- production Ansible must require an explicit Files-root variable;
- documentation must state the database/Files pairing invariant;
- automated compose/template tests should verify `/data/files` uses `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}`, not an implicit `${DIARIES_NAS_CONTENT_PATH}/files`;
- tests should prove that changing one environment's Files-root setting does not change another environment's generated configuration.

A future enhancement may add a durable dataset identifier/marker to a Files root and validate it against configuration on responder startup. That extra guard is useful but is not required to complete this feature unless implementation experience shows path configuration alone is too easy to misuse.

## Likely implementation scope

### Diaries repository

Expected files include, subject to implementation review:

```text
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
config/environments/local-docker-build.env
config/environments/local-published-smoke.env
config/environments/local.env.example
README.md
diaries-responder/README.md
scripts/windows/development-infrastructure/*
scripts/windows/local-docker-build/*
scripts/windows/local-published-smoke/*
```

Only scripts/documentation that actually depend on Files-root identity need changing. Database backup scripts should not be mechanically modified unless they are being extended to create complete dataset backups/manifests.

The developer-owned file:

```text
%USERPROFILE%\.diaries\responder.json
```

is not committed, but its required migration must be documented and included in validation.

### Playbooks repository

Expected files include:

```text
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
roles/diaries/defaults/main.yaml or role validation tasks
roles/diaries/files/sync/scripts/backup-*/restore-* documentation or helpers as required
host/group variables outside the role that define the production NAS paths
```

The exact host-variable location is deployment-specific and should not be invented inside the role.

## Detailed implementation steps

- [x] Freeze and document the database-dataset <-> mutable-Files-root invariant.
- [x] Inventory the current development, local Docker, smoke and production database/Files mappings.
- [x] Decide the final physical NAS path names for each independent dataset.
- [x] Add explicit `DIARIES_FILES_DIR` support to both local Docker Compose files.
- [x] Remove implicit `${DIARIES_NAS_CONTENT_PATH}/files` use for mutable storage.
- [x] Add explicit per-dataset Files-root settings to local environment files/examples.
- [x] Update direct Windows development responder configuration guidance.
- [x] Add `diaries_files_dir` to the production Diaries Ansible configuration.
- [x] Render the production Files path explicitly into `.env` and Compose.
- [x] Add configuration validation/tests preventing an omitted mutable Files path.
- [x] Review database backup/restore scripts and document database + Files pairing.
- [x] Add manifest support that records the matched database + Files identity without claiming Files bytes are included; actual complete-dataset capture remains Step 8.
- [x] Take pre-migration backups of production DB, development DB and shared Files.
- [x] Run pre-split reconciliation against each database using the shared Files tree and archive evidence.
- [x] Preserve the existing production Files path unless a migration has a clear benefit.
- [x] Copy the shared Files tree to new development/local dataset roots.
- [x] Repoint each non-production mode to the appropriate new root.
- [x] Run post-split dry-run reconciliation for every database/Files pair.
- [x] Resolve any pre-existing mismatches without copying/deleting data from the other environment implicitly.
- [x] Smoke-test development Image upload and deletion and prove production remains byte-for-byte/catalogue unchanged.
- [x] Verify production Image catalogue and file serving non-destructively.
- [x] Update architecture, responder and operating documentation.
- [x] Record final path map, reconciliation evidence and rollback instructions.

## Acceptance criteria

- [x] Production and development no longer use the same physical mutable Files root.
- [x] Every independently persisted local database dataset has an explicitly assigned mutable Files root.
- [x] Modes intentionally sharing one database dataset share exactly the corresponding Files root and this is documented.
- [x] Original read-only diary scans may still be shared without duplication.
- [x] Docker responders continue to see the stable runtime path `/data/files` regardless of physical NAS location.
- [x] `Image.relativePath` remains environment-neutral and relative to the configured Files root.
- [x] Deleting an Image in development cannot remove or alter the production physical file.
- [x] Uploading/replacing an Image in development cannot alter production physical files.
- [x] Production Image lifecycle operations cannot alter non-production Files roots.
- [x] Image catalogue reconciliation is clean or has explicitly reviewed exceptions for every migrated database/Files pair.
- [x] A missing Files-root configuration fails clearly rather than silently selecting the shared production path.
- [x] Production Ansible generates the intended production Files mount from an explicit variable.
- [x] Local Docker Compose generates the intended non-production Files mount from an explicit variable.
- [x] Backup/restore documentation treats the database and Files root as a matched dataset.
- [x] Existing `/files/...` HTTP URLs and Image `relativePath` values do not change merely because the backing root is isolated.
- [x] Existing responder/client/web Image behaviour remains unchanged apart from environment isolation.

## Completion Summary

0031-FEAT was closed on 2026-10-03 after Steps 1–16 established and verified the invariant:

```text
one effective database dataset <-> one effective mutable Files root
```

The normal intentionally shared local dataset now resolves to
`./data/database/common` + `files-development-common`, while production remains
an independent database dataset using the explicit production Files selector
`files`. Committed isolated local defaults retain their own database/Files
pairs, and one-sided or crossed overrides are rejected before startup/use.

The final exact-candidate regression is
`evidence/Step 16/runtime/final-regression-20261003-104658`. It passed all
Diaries 0031 source/contract gates, all Playbooks 0031 validators remotely on
`mango`, the complete Java responder/web test suite, and the Angular production
build. The final rollback rehearsal is
`evidence/Step 16/runtime/restore-rehearsal-20261003-104511`; it restored the
preserved Step 8 `common` dump into disposable PostgreSQL and reconciled it
read-only against `files-development-common` without overwriting the live local
database.

Steps 13 and 14 remain the authoritative data-sensitive proof for local
Image lifecycle isolation from production and for the explicit, non-destructive
production configuration. Step 16 deliberately did not introduce a new
production Image mutation merely to repeat those controls.

The two Step 13 follow-ups remain outside this completed feature: revisit a
bounded complete retained-snapshot design after the current TODO work, and
separately redact signin credentials/tokens from responder MQTT-RPC diagnostic
logging. Neither changes the database/Files isolation acceptance decision.

No database rows, Image bytes, production Files bytes, or retained MQTT state
are changed by this administrative close-out.

## Dependencies

Depends on the Image catalogue/file-integrity model introduced by 0024 and the dedicated Image deletion behaviour introduced by 0030.

0025 ImageFragment work may continue using disposable test storage, but production rollout and destructive development Image lifecycle testing should not rely on a Files tree shared with production. Complete this isolation before enabling broader Image authoring under 0027.

## Out of scope

This feature does not:

- change the logical `Image.relativePath` contract;
- duplicate or relocate the read-only original diary scans unless operationally desired;
- change browser `/files/...` URLs;
- merge development and production databases;
- introduce automatic cross-environment Image synchronization;
- copy development Images into production automatically;
- make retained MQTT state durable authoritative storage.

Promotion of a deliberately selected Image/content change from development to production, if required in future, must be an explicit operation affecting both production database/catalogue state and the production Files root. It must not be achieved by sharing physical storage.

## Deployment and rollback

This feature is primarily configuration/storage isolation, but the migration touches live Image bytes and must be treated as data-sensitive.

Before production validation, preserve the existing shared Files backup and both database backups.

The preferred deployment leaves the production physical Files path unchanged and repoints development/local modes to copies. With that approach, rollback is straightforward:

1. stop the affected non-production responder;
2. restore its previous configuration if necessary;
3. do **not** delete the newly created isolated Files copy until reconciliation/evidence is complete;
4. if reverting to the old shared Files root temporarily, disable destructive Image/File operations because the original inconsistency risk immediately returns.

Rollback must never silently merge divergent development and production Files trees.
- **Step 13 runtime correction — 2026-10-02:** the local lifecycle preflight now uses the responder's established HTTP static-context contract: `GET /diaries` returning 404 proves the responder HTTP server/context is reachable; lifecycle readiness is then proved by the real MQTT RPC operation. The earlier 404 attempt made no Image mutation, and the successful frozen production BEFORE control remains valid.
- **Step 13 MQTT retained-snapshot correction — 2026-10-03:** local startup testing exposed a second overload path distinct from database publication pacing: an already-populated broker drives retained delivery after subscription. The local/test broker therefore now uses `max_queued_messages 0` with `max_inflight_messages 20`, while the responder drains non-overlapping retained branches sequentially. This is an interim correctness safeguard; after the current TODO features are complete, revisit finer subscription-space segmentation with paced successive subscriptions (or another bounded complete-snapshot protocol) before reintroducing a finite queue. The production Playbooks broker setting is not changed by the Diaries-only package and must be reviewed before production responder restart.

- **Step 13 retained-observer correction — 2026-10-03:** the real upload of the
  corrected fixture committed Image 87, but retained verification was attempted
  with the `diaries-client` MQTT identity, which is not allowed to read
  `diaries/images/+`. The harness now uses the effective responder MQTT identity
  only for retained-state observation and adds a guarded supported-RPC cleanup
  action for unrecorded disposable Step 13 uploads.


Step 13 v9 recovery hardening: Image query results are explicitly array-normalised under PowerShell StrictMode, and the guarded cleanup path can safely recognise/record a prior delete that completed before evidence capture.
- Step 13 runtime correction: local Docker CIFS mounts now synthesize `dir_mode=0700,file_mode=0600`, matching production and preserving the owner-only `.image-staging` invariant across direct-Windows and containerized local modes.
- Step 13 runtime correction: the local-Docker mode-700 permission guard now protects its shell-local `$p` from PowerShell StrictMode interpolation; the v10 failure occurred before `deleteImage`, after the CIFS mount itself had already been verified as `700`.


- Step 13 runtime correction: v12 removes the remaining inline `sh -c` permission probe because Windows PowerShell 5.1 can truncate the native-command argument before Docker receives it. Direct `docker exec stat` / `test -d` calls now verify the already-correct `700` CIFS mount without nested shell quoting.

- **Step 13 close-out — 2026-10-03:** authoritative evidence is `runtime/local-20261003-080333-8f26d1bc`, production BEFORE `/home/richard/projects/diaries/data/0031-step13/production-before-20261002-203216`, and production AFTER `/home/richard/projects/diaries/data/0031-step13/production-after-20261003-083327`. The production responder remains intentionally stopped for the Step 14 hand-off. Before restart, review/align the production Mosquitto retained-snapshot queue policy with the Step 13 interim `max_queued_messages 0` decision. After the current TODO features are complete, revisit a bounded retained-snapshot design such as finer subscription-space segmentation with paced successive subscriptions. A separate follow-up is also required to redact signin credentials/tokens from responder MQTT-RPC diagnostic logging.
