# 0031-FEAT - Isolate mutable Files storage by database environment

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-28

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

## Current implementation evidence

The current local Docker compositions mount the mutable Files tree using:

```text
${DIARIES_NAS_CONTENT_PATH}/files -> /data/files
```

in both:

```text
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
```

The production Diaries Ansible role currently generates the same shape in:

```text
roles/diaries/templates/compose.yaml.j2
```

using:

```text
${DIARIES_NAS_CONTENT_PATH}/files -> /data/files
```

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

The exact names may be changed during implementation, but each database dataset must map unambiguously to one Files root.

The existing production `.../files` path should preferably remain where it is. This minimizes production migration risk. New non-production roots can be created by copying the existing tree and then reconciling each copy against its corresponding database.

If two local modes are deliberately configured to use the same PostgreSQL data directory/database, they should also be configured to use the same mutable Files root. Do not share one without the other.

## Configuration design

Do not encode environment names in responder Java code.

Continue to present the responder with the normal runtime path:

```text
/data/files
```

inside Docker. Select the physical backing root at deployment/configuration level.

Introduce an explicit mutable Files path variable, for example:

```text
DIARIES_NAS_FILES_PATH
```

whose value is the complete NAS subpath for the database dataset, for example:

```text
nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files
nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files-local-docker-build
```

Change Docker mounts from:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/files
```

to:

```yaml
subpath: ${DIARIES_NAS_FILES_PATH}
```

`DIARIES_NAS_CONTENT_PATH` may continue to identify the common content root used for the read-only `diaries` mount.

The mutable Files path should be explicit rather than silently falling back to `${DIARIES_NAS_CONTENT_PATH}/files`. A missing value should fail deployment/startup configuration instead of accidentally returning to shared mutable storage.

For the direct Windows development responder, update the developer-owned `%USERPROFILE%\.diaries\responder.json` so that `diaries.root` plus `diaries.files` resolves to the development-specific Files directory while `diaries.diaries` can continue to resolve to the shared diary source tree.

For example, if the common NAS root remains the responder `root`, the direct-development configuration can keep:

```text
diaries = diaries
```

while changing:

```text
files = files-development-infrastructure
```

No persisted `Image.relativePath` value should contain an environment prefix. `relativePath` remains relative to the configured Files root, so the same logical Image catalogue can be restored into another dataset-specific Files root when deliberately cloning/restoring an environment.

## Production Ansible design

Extend the Diaries role with an explicit variable such as:

```yaml
diaries_nas_files_path: .../diaries-content/files
```

and render it into `.env` as:

```text
DIARIES_NAS_FILES_PATH=...
```

Update:

```text
roles/diaries/templates/.env.j2
roles/diaries/templates/compose.yaml.j2
```

The production host variables must explicitly identify the production Files root.

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
DIARIES_NAS_FILES_PATH=.../files-development-common
```

Never configure only one half of that pair as shared.

## Backup and restore rule

Database backup/restore and mutable Files backup/restore are now explicitly related operations.

The existing database-only scripts may remain useful, but documentation and operational scripts must make clear that restoring a database snapshot without the matching Files snapshot can create an inconsistent Image catalogue.

For any backup intended to be a complete recoverable Diaries dataset, preserve together:

```text
PostgreSQL database backup
matching mutable Files root snapshot/copy
configuration identifying that Files root
```

Where practical, add a small manifest recording at least:

```text
environment/dataset name
database backup filename/time
Files-root path
Image row count
catalogued-file count
optional inventory/checksum evidence
```

A database-only development reset is permitted only when the operator deliberately accepts that reconciliation may be required before Image lifecycle testing.

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
- automated compose/template tests should verify `/data/files` uses `DIARIES_NAS_FILES_PATH`, not `${DIARIES_NAS_CONTENT_PATH}/files`;
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

- [ ] Freeze and document the database-dataset <-> mutable-Files-root invariant.
- [ ] Inventory the current development, local Docker, smoke and production database/Files mappings.
- [ ] Decide the final physical NAS path names for each independent dataset.
- [ ] Add explicit `DIARIES_NAS_FILES_PATH` support to both local Docker Compose files.
- [ ] Remove implicit `${DIARIES_NAS_CONTENT_PATH}/files` use for mutable storage.
- [ ] Add explicit per-dataset Files-root settings to local environment files/examples.
- [ ] Update direct Windows development responder configuration guidance.
- [ ] Add `diaries_nas_files_path` (or equivalent) to the production Diaries Ansible configuration.
- [ ] Render the production Files path explicitly into `.env` and Compose.
- [ ] Add configuration validation/tests preventing an omitted mutable Files path.
- [ ] Review database backup/restore scripts and document database + Files pairing.
- [ ] Add complete-dataset backup manifest/support where useful.
- [ ] Take pre-migration backups of production DB, development DB and shared Files.
- [ ] Run pre-split reconciliation against each database using the shared Files tree and archive evidence.
- [ ] Preserve the existing production Files path unless a migration has a clear benefit.
- [ ] Copy the shared Files tree to new development/local dataset roots.
- [ ] Repoint each non-production mode to the appropriate new root.
- [ ] Run post-split dry-run reconciliation for every database/Files pair.
- [ ] Resolve any pre-existing mismatches without copying/deleting data from the other environment implicitly.
- [ ] Smoke-test development Image upload and deletion and prove production remains byte-for-byte/catalogue unchanged.
- [ ] Verify production Image catalogue and file serving non-destructively.
- [ ] Update architecture, responder and operating documentation.
- [ ] Record final path map, reconciliation evidence and rollback instructions.

## Acceptance criteria

- [ ] Production and development no longer use the same physical mutable Files root.
- [ ] Every independently persisted local database dataset has an explicitly assigned mutable Files root.
- [ ] Modes intentionally sharing one database dataset share exactly the corresponding Files root and this is documented.
- [ ] Original read-only diary scans may still be shared without duplication.
- [ ] Docker responders continue to see the stable runtime path `/data/files` regardless of physical NAS location.
- [ ] `Image.relativePath` remains environment-neutral and relative to the configured Files root.
- [ ] Deleting an Image in development cannot remove or alter the production physical file.
- [ ] Uploading/replacing an Image in development cannot alter production physical files.
- [ ] Production Image lifecycle operations cannot alter non-production Files roots.
- [ ] Image catalogue reconciliation is clean or has explicitly reviewed exceptions for every migrated database/Files pair.
- [ ] A missing Files-root configuration fails clearly rather than silently selecting the shared production path.
- [ ] Production Ansible generates the intended production Files mount from an explicit variable.
- [ ] Local Docker Compose generates the intended non-production Files mount from an explicit variable.
- [ ] Backup/restore documentation treats the database and Files root as a matched dataset.
- [ ] Existing `/files/...` HTTP URLs and Image `relativePath` values do not change merely because the backing root is isolated.
- [ ] Existing responder/client/web Image behaviour remains unchanged apart from environment isolation.

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
