# 0024 implementation steps

## Objective

Introduce a durable, reusable `Image` catalogue for files below the configured
Diaries Files root. A supported image upload must finish with one file, one
database row and one canonical retained MQTT entity. Existing supported files
must be catalogued by an explicit, reviewable and idempotent reconciliation
process.

This feature also establishes the file-integrity boundary: generic file
operations must not delete or replace bytes owned by an Image row.

The durable relationship introduced here is:

```text
Image.relativePath -> one file below the configured Files root
```

`Image` is independent of diary chronology. It may have no references and may
eventually be reused by several ImageFragments.

## Scope boundary

0024 includes:

- the additive `image` table;
- responder Image model, persistence DTO, publish DTO and repository;
- canonical `diaries/images/{imageId}` retained topics;
- supported-image inspection and catalogue-aware upload;
- protection against generic deletion or overwrite of catalogued paths;
- a dry-run/apply reconciliation utility for existing files;
- reconciliation of the 0022 embedded-image candidate paths to Image rows;
- automated tests and a controlled production migration workflow.

0024 does **not** include:

- `fragment.image_id`;
- `AddImageFragment`, `SetFragmentImage` or `DeleteImage` RPCs;
- ImageFragment creation, conversion or deletion;
- caption/alt-text editing UI;
- diaries-client Image selection;
- diaries-web ImageFragment projection or rendering;
- transformation of legacy Fragment HTML.

Those operations remain in 0025–0028. In particular, reconciliation creates
Image rows only; it must never create or modify a Fragment or Marquee.

## Fixed design decisions

### Canonical relative paths

Create one reusable `ImagePathPolicy` and use it everywhere. Do not duplicate
path rules in `UploadFile`, `DeleteFile` and the migration utility.

The canonical persisted `relativePath` is:

- relative to the configured Files root, never to the process directory;
- Unicode-normalized to NFC;
- stored with `/` separators on Windows and Linux;
- case-preserving for display and URL construction;
- free of a leading slash, trailing slash, empty segment, `.` or `..` segment;
- never an absolute path, drive-qualified path, UNC path or URI;
- verified against the real Files-root path so a symlink/reparse-point cannot
  escape that root.

Treat case-only aliases as conflicts even on a case-sensitive filesystem. Use a
case-folded database uniqueness index and have reconciliation report any
pre-existing case collision instead of choosing one. This gives Windows
development and Linux production the same identity rules.

Do not persist a URL or absolute filesystem path. Consumers later derive a URL
from runtime configuration plus `relativePath`, encoding each path segment.

### Supported image detection

The persisted MIME type describes the bytes, not merely the request header or
filename extension. Introduce a focused `ImageMetadataInspector` which:

1. identifies JPEG, PNG, GIF and WebP from file signatures/content;
2. extracts positive width and height without trusting client values;
3. computes or accepts the already-computed lowercase SHA-256 checksum;
4. rejects corrupt/truncated content which claims to be a supported image;
5. returns a controlled unsupported result for other content.

`application/octet-stream` remains compatible with the generic upload
facility. If its bytes are a supported image, catalogue them. If they are not,
retain the existing generic-file behaviour and do not create an Image row. A
request declaring a supported image MIME type whose bytes are corrupt or a
different image type is rejected.

### Image metadata

The initial retained and database shape is:

```text
id                positive bigint
version           non-negative bigint
relativePath      canonical relative path
mimeType          image/jpeg | image/png | image/gif | image/webp
originalFilename  original upload name; basename during reconciliation
width             positive integer
height            positive integer
checksum          lowercase 64-character SHA-256
caption           non-null text, initially empty
altText           non-null text, initially empty
```

The checksum is indexed for diagnostics and reuse suggestions but is not
unique: identical bytes at distinct historical paths are permitted.

### Filesystem/database failure protocol

PostgreSQL and the filesystem cannot form one atomic transaction. Use the
following explicit protocol for a new supported-image upload:

```text
decode to private same-filesystem temporary file
  -> validate size/checksum/content/dimensions
  -> canonicalize and lock target path
  -> reject if target path already has an Image row
  -> atomically promote file (preserving an uncatalogued overwrite backup)
  -> begin database transaction and insert Image
  -> commit database transaction
  -> publish retained Image topic
  -> return success
```

If validation or promotion fails, remove only the private temporary file. If
database insertion/commit fails after promotion, remove the newly promoted file
and restore an earlier uncatalogued file from its backup. If restoration fails,
return an internal error and log both paths for administrator recovery; never
claim success.

Publish only after the database commit. A publish failure does not reverse the
durable database/file result; report it clearly and rely on normal responder
reconciliation/restart to repair retained state. A process crash between file
promotion and database commit can leave an uncatalogued file, which the 0024
reconciliation utility must detect and safely repair.

Use an atomic no-replace promotion plus a target-path critical section so two
concurrent uploads cannot both compensate against the same file. The database
unique index is the final authority for cross-process conflicts.

## Phase 1 — baseline and evidence

- [x] Confirm 0022 is deployed and 0023 consumer changes are complete.
- [ ] Record the responder/client/web versions used as the 0024 baseline.
- [ ] Back up the development database used for implementation tests.
- [ ] Take a read-only inventory of the actual Files root:
  - total regular files and directories;
  - supported image candidates by detected type;
  - unsupported files;
  - unreadable files;
  - symlinks/reparse points;
  - case-folded path collisions.
- [ ] Freeze the 0022 candidate inventory/review evidence which will be supplied
      to 0024 reconciliation, recording filenames and SHA-256 hashes.
- [ ] Capture current `UploadFile`, `ListFiles` and `DeleteFile` response shapes
      so additive compatibility can be tested.
- [ ] Run the existing responder tests and build before changing code and record
      any pre-existing failures separately.

## Phase 2 — additive database migration

Create this directory beneath the 0024 change record:

```text
migration/
  001-preflight.sql
  002-add-image-catalogue.sql
  003-postflight.sql
  README.md
```

### 2.1 Preflight

`001-preflight.sql` must be read-only and report:

- database name/server/schema and execution timestamp;
- whether an `image` table or similarly named objects already exist;
- current diary/page/fragment/marquee counts;
- current fragment ownership/type anomaly counts from 0022;
- transaction isolation and current application user;
- sufficient privileges to create the table, sequence, indexes and constraints.

Fail the apply workflow if an unexpected partial Image schema exists. Do not
let Hibernate silently create or alter the production table.

### 2.2 Schema

`002-add-image-catalogue.sql` should create an additive table equivalent to:

```sql
CREATE TABLE image (
    id                BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
    version           BIGINT NOT NULL DEFAULT 0 CHECK (version >= 0),
    relative_path     TEXT NOT NULL,
    mime_type         VARCHAR(127) NOT NULL,
    original_filename TEXT NOT NULL,
    width             INTEGER NOT NULL CHECK (width > 0),
    height            INTEGER NOT NULL CHECK (height > 0),
    checksum          CHAR(64) NOT NULL,
    caption           TEXT NOT NULL DEFAULT '',
    alt_text          TEXT NOT NULL DEFAULT ''
);
```

Add named checks restricting MIME values and lowercase hexadecimal checksum
shape. Add a unique index on the agreed case-folded path identity, for example
`lower(relative_path)`, and a non-unique checksum index. Retain the original
case in `relative_path`.

The script must be rerunnable safely: an already-correct schema is accepted,
while a partial or incompatible schema causes an explicit failure rather than
being silently reshaped.

### 2.3 Postflight

`003-postflight.sql` must verify exact columns, types, defaults, nullability,
constraints and indexes; confirm the table is initially empty; and repeat the
0022 Fragment integrity counts to prove this feature did not alter chronology.

Document exact development and production commands, backup prerequisites,
expected output, rollback-by-database-restore, and evidence filenames in
`migration/README.md`.

## Phase 3 — responder Image domain and repository

Add:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/
  model/Image.java
  dto/ImageDBDTO.java
  dto/ImagePublishDTO.java
  repository/ImageRepository.java
  repositoryImpl/ImageRepositoryImpl.java
```

### 3.1 Model and DTOs

- [ ] Make `Image` extend the existing `Base` ID/version model.
- [ ] Map every field explicitly to the SQL column name and nullability.
- [ ] Keep `relativePath` a String; do not place a platform `Path` in DTOs.
- [ ] Provide constructors between `Image`, `ImageDBDTO` and
      `ImagePublishDTO` following existing responder conventions.
- [ ] Validate canonical path, MIME, positive dimensions and checksum at the
      service boundary as well as with database constraints.
- [ ] Make caption and alt text non-null empty strings initially.
- [ ] Avoid importing `java.awt.Image`; use the Diaries model type explicitly.

`ImagePublishDTO` must publish metadata only to exactly:

```text
diaries/images/{id}
```

It must support both map publication during startup reconciliation and retained
MQTT publication/tombstoning using the existing `Publisher` QoS/retain rules.

### 3.2 Repository

`ImageRepository` must add to normal CRUD operations:

```text
Optional<ImageDBDTO> findByRelativePath(String canonicalPath)
Iterable<ImageDBDTO> findAllOrderedByRelativePath()
boolean existsAtOrBelow(String canonicalPath)
```

The last query protects both a file and a directory subtree. It must use the
same identity/case policy as the unique index and escape SQL wildcard
characters rather than interpolating an unsafe `LIKE` pattern.

Use bound parameters for all new path/checksum queries. Do not extend the
existing repository's SQL-string quoting pattern to user-controlled paths.

### 3.3 Registration and wiring

- [ ] Register `Image.class` once in `GetEntityManager`.
- [ ] Construct `ImageRepositoryImpl` in `Responder.run` and place it in
      `DiaryContext`.
- [ ] Add `DiaryContext.inflateImage` and focused transaction helpers rather
      than embedding transaction logic in handlers.
- [ ] Add repository tests for save/find/update/order, exact/case-alias lookup,
      subtree ownership and duplicate-path rejection.

## Phase 4 — retained Image catalogue

Extend `DiaryContext.loadFromDatabase()` to iterate every Image row separately
from the Diary/Page/Fragment/Marquee hierarchy and publish one canonical Image
topic per row.

Required tests:

- [ ] exact JSON field set and values for `ImagePublishDTO`;
- [ ] exactly one canonical topic per Image;
- [ ] QoS 1 and retained publication consistent with existing entities;
- [ ] tombstone behaviour;
- [ ] database replay includes orphan/unreferenced Images;
- [ ] replay is deterministic and contains no file bytes or absolute URL/path;
- [ ] empty Image catalogue leaves existing retained projection unchanged.

No consumer subscribes to `diaries/images/+` in 0024. The stable retained topic
is the catalogue/listing mechanism needed by later consumers; do not add a
second database-shaped `ListImages` RPC unless a demonstrated requirement
cannot be served by retained state.

## Phase 5 — shared path and image inspection services

Add focused, independently tested utilities, for example:

```text
utilities/ImagePathPolicy.java
utilities/ImageMetadataInspector.java
utilities/InspectedImage.java
utilities/ResolvedUpload.java
utilities/ImageCatalogueService.java
```

The exact names may follow local conventions, but responsibilities must remain
separate:

- path policy: canonical relative path and safe absolute resolution;
- inspector: byte-derived type, dimensions and checksum;
- resolved upload: immutable staged file, target, canonical metadata and size;
- catalogue service: transaction, compensation and publication orchestration.

Test path handling with `/` and `\`, redundant separators, dot segments,
absolute Windows/Unix/UNC paths, traversal, URL-looking input, Unicode, spaces,
`%`/`_`, case aliases and symlink escape attempts. Tests must run on Windows
without weakening the production Linux rules.

Test valid and corrupt samples of JPEG, PNG, GIF and WebP. Include extension and
declared-MIME mismatches, octet-stream images, octet-stream non-images, checksum
mismatch, zero/truncated dimensions and files at the configured size limit.

## Phase 6 — catalogue-aware UploadFile

Refactor `UploadFile` into orchestration around the shared services while
preserving authentication, authorization, maximum size, base64 decoding and
existing useful response fields.

### 6.1 Staging

- [ ] Resolve the Files root once through `ImagePathPolicy`.
- [ ] Decode into a private temporary file on the same filesystem as the target.
- [ ] Calculate SHA-256 during decoding and reuse it; do not read the full file
      merely to hash it again unless post-promotion verification is required.
- [ ] Inspect bytes before promotion and delete the temporary file on every
      rejected path.
- [ ] Never log uploaded bytes, access tokens or full sensitive filesystem
      configuration.

### 6.2 Conflict rules

Before changing the target:

- reject any upload whose canonical path already belongs to an Image, whether
  `overwrite` is true or false;
- reject a case/separator alias of a catalogued path;
- retain the existing conflict when a target file exists and overwrite is false;
- permit the existing overwrite behaviour only for an uncatalogued target;
- preserve and restore that uncatalogued target if later catalogue creation
  fails;
- leave file, database and retained topic unchanged for every rejected request.

### 6.3 Catalogue creation and response

For a supported image, construct metadata from the inspected file, atomically
promote it, insert exactly one Image row in a database transaction, commit, and
publish `diaries/images/{id}`.

Replace the nullable-hostile `Map.of` success payload with an explicit response
DTO if necessary. Preserve existing `name`, `subdir`, `size`, `path` and `url`
fields for the current client, and add:

```json
{
  "imageId": 123,
  "image": {
    "id": 123,
    "version": 0,
    "relativePath": "maps/baltic.jpg",
    "mimeType": "image/jpeg",
    "originalFilename": "baltic.jpg",
    "width": 1200,
    "height": 800,
    "checksum": "...",
    "caption": "",
    "altText": ""
  }
}
```

For a permitted non-image generic upload, return `imageId`/`image` as null (or
omit them only if that is explicitly captured as the compatibility contract).
The absolute `path` may remain temporarily in the RPC response for compatibility
but must never be persisted or published.

Add handler/service tests proving:

- a supported upload creates exactly one file/row/topic;
- an octet-stream supported image is catalogued;
- an octet-stream non-image is not catalogued;
- corrupt declared-image content is rejected;
- retry cannot create a duplicate Image;
- catalogued overwrite is rejected even with `overwrite=true`;
- repository failure removes the new file;
- overwrite failure restores pre-existing uncatalogued bytes;
- publish happens after commit;
- publication failure is recoverable by database replay;
- concurrent same-path uploads have one winner and do not delete its file.

## Phase 7 — protect generic DeleteFile

Refactor `DeleteFile` to use `ImagePathPolicy` and `ImageRepository` before any
filesystem mutation.

- [ ] Do not create a requested directory while processing a delete.
- [ ] Reject deletion when the exact canonical path has an Image row.
- [ ] If the target is a directory, reject deletion when any Image row is below
      that canonical prefix.
- [ ] Apply the same separator/case/symlink rules as upload and uniqueness.
- [ ] Return a clear conflict response which identifies the canonical relative
      path without leaking an absolute host path.
- [ ] Leave the file/directory, Image row and retained topic unchanged.
- [ ] Preserve the existing idempotent not-found behaviour only for genuinely
      uncatalogued paths.

Test exact file, parent directory, case alias, separator alias, SQL wildcard in
name, traversal and symlink escape. Also prove an unrelated uncatalogued file
can still be deleted and that an empty uncatalogued directory follows the
existing supported behaviour.

There is intentionally no public `DeleteImage` operation in 0024. Catalogue
removal is administrator-controlled until reference-aware deletion arrives in
0025.

## Phase 8 — existing-file reconciliation utility

Add a dedicated command, not an RPC handler, for example:

```text
com.rsmaxwell.diaries.responder.migration.migration0024.Migration0024ImageCatalogue
```

Register a Gradle `migration0024ImageCatalogue` `JavaExec` task. It should use
the normal responder configuration and require explicit parameters:

```text
-PmigrationConfig=<config-file>
-PmigrationOutput=<new-empty-output-directory>
-PmigrationMode=dry-run|apply
-Pmigration0022Candidates=<optional-frozen-0022-candidate-csv>
```

Default to `dry-run`; `apply` must be explicit. Refuse a non-empty output
directory so evidence from different runs cannot be mixed. Record the input
file hashes, resolved Files root identity, database identity, tool version,
start/end timestamps and mode in the summary.

### 8.1 Full two-way inventory

Recursively scan regular files below the Files root without following links out
of the root. Also read all existing Image rows so the report can detect both
uncatalogued files and catalogue rows whose files are absent.

Assign every observed path one explicit status such as:

```text
CREATE_MISSING
CATALOGUED_MATCH
CATALOGUED_METADATA_CONFLICT
DATABASE_ROW_MISSING_FILE
CASE_COLLISION
SYMLINK_OR_ESCAPE
UNSUPPORTED
UNREADABLE
CHANGED_DURING_SCAN
```

For an existing row, compare detected MIME, dimensions and checksum. Do not
silently update drifted metadata or replace bytes in 0024; report a conflict for
review. In apply mode create only `CREATE_MISSING` rows whose current file
fingerprint still matches the dry-run evidence.

Use one transaction for a reviewed apply batch, or deterministic bounded
batches with an explicit checkpoint protocol. A failed batch must roll back its
database inserts and produce a failure report. The utility never changes image
files.

### 8.2 Evidence files

Produce stable, sorted, machine-readable outputs:

```text
0024-summary.json
0024-file-inventory.csv
0024-create-plan.json
0024-conflicts.csv
0024-candidate-cross-reference.csv
0024-apply-results.csv          # apply mode only
0024-post-apply-verification.json
```

Sort by canonical relative path, then database ID. Do not include secrets or
absolute paths in row-level CSV data.

### 8.3 0022 candidate cross-reference

Read the frozen 0022 embedded-image candidate inventory as evidence, not as
instructions. Normalize only safe Files-root-local paths. Preserve the 0022
Fragment/candidate identity in the report and classify every candidate as:

```text
MATCHED_ONE_IMAGE
MISSING_FILE_OR_IMAGE
EXTERNAL_URL
AMBIGUOUS_PATH
INVALID_PATH
```

The report may associate a candidate with an Image ID after apply, but it must
not decide `CONVERT_TO_IMAGE`, `SPLIT_MARQUEE_AND_IMAGE` or `KEEP_LEGACY` and
must not modify Fragment HTML. Those decisions remain inputs to 0028.

### 8.4 Idempotency proof

Against a copy of the actual Files root and restored database:

1. run dry-run and review every conflict;
2. archive/hash the dry-run evidence;
3. run apply with the same inputs;
4. run dry-run again;
5. prove the second dry-run proposes zero creates;
6. run apply again and prove it creates zero rows;
7. compare row counts and metadata to the first apply;
8. start the responder and verify retained topics match database rows.

## Phase 9 — automated validation

At minimum run:

```text
gradlew.bat :diaries-responder:test
gradlew.bat :diaries-responder:build
```

Add focused tests under:

```text
src/test/java/com/rsmaxwell/diaries/responder/model/
src/test/java/com/rsmaxwell/diaries/responder/repositoryImpl/
src/test/java/com/rsmaxwell/diaries/responder/dto/
src/test/java/com/rsmaxwell/diaries/responder/handlers/
src/test/java/com/rsmaxwell/diaries/responder/utilities/
src/test/java/com/rsmaxwell/diaries/responder/migration/migration0024/
```

Use temporary directories for filesystem tests and transactions which roll back
or isolated test databases for repository tests. Never point an automated test
at the production Files root.

Also run:

- [ ] `git diff --check` in the parent and responder repositories;
- [ ] explicit SQL preflight/schema/postflight tests against a disposable
      PostgreSQL database;
- [ ] responder startup reconciliation with zero, one and multiple Images;
- [ ] retained MQTT integration tests when local Mosquitto is available;
- [ ] current diaries-client upload/list/delete regression smoke tests;
- [ ] diaries-web read regression smoke tests proving no visible chronology
      change.

## Phase 10 — local full-stack smoke test

Use a disposable Files-root copy and development database. The test dataset
should contain:

- one JPEG uploaded normally;
- one PNG uploaded as octet-stream;
- one non-image generic file;
- one supported pre-existing uncatalogued image;
- two identical images at distinct paths;
- a case/path conflict;
- a corrupt image;
- an Image row whose file is deliberately absent in the disposable dataset.

Verify:

- successful supported uploads return Image metadata and publish one topic;
- the current client still lists/previews uploaded files;
- generic non-image upload remains uncatalogued;
- overwrite and delete guards return conflict without mutation;
- restart reconstructs the same Image topic set from PostgreSQL;
- reconciliation reports all expected statuses and is idempotent;
- no Fragment/Marquee count, content, sequence, type or ownership changes;
- diaries-client and diaries-web continue their 0023 MARQUEE behaviour.

Record database counts, filesystem hashes and retained-topic counts before and
after the smoke test.

## Phase 11 — production deployment and reconciliation

### 11.1 Prepare

1. Freeze the exact responder artifact, migration SQL and reconciliation tool.
2. Run reconciliation dry-run against production read-only and resolve all
   conflicts which would make apply unsafe.
3. Record production Image/file/candidate counts and hash all evidence.
4. Schedule a writer-free maintenance window.
5. Stop the responder/client editing path or otherwise guarantee no upload or
   delete can occur during migration.
6. Take fresh binary PostgreSQL and SQL backups.
7. Back up or snapshot the Files root; database backup alone is insufficient.
8. Run and archive `001-preflight.sql`.

### 11.2 Deploy

1. Apply `002-add-image-catalogue.sql`.
2. Run and archive `003-postflight.sql`.
3. Deploy the 0024 responder containing catalogue-aware upload/delete guards.
4. Start it once with an empty catalogue and verify health plus unchanged
   Diary/Page/Fragment/Marquee retained state.
5. Stop writers again and run the reviewed reconciliation in apply mode.
6. Run the post-apply dry-run/idempotency verification.
7. Restart/resynchronise the responder so every Image row is published.
8. Compare database Image count, file matches and `diaries/images/+` retained
   topic count.
9. Repeat upload, guarded overwrite, guarded deletion, client and web smoke
   tests.
10. Re-enable normal editing only after all integrity checks pass.

Do not create an ImageFragment during 0024 verification.

## Rollback

Before reconciliation has inserted rows, roll back the responder artifact and
restore the pre-0024 database only if required. The additive empty table may
remain temporarily, but document that choice.

After reconciliation or new catalogued uploads, do **not** simply deploy an old
responder: it would permit generic deletion/overwrite without consulting the
catalogue. A safe rollback requires all of:

1. disable upload and generic deletion;
2. stop the 0024 responder;
3. preserve/snapshot the current Files root;
4. restore the matching pre-0024 database and Files-root backup, or keep the
   catalogue database with all file mutation paths administratively disabled;
5. clear only the known `diaries/images/{id}` retained topics if the database is
   rolled back and normal synchronization will not remove them;
6. deploy the previous responder;
7. verify legacy retained state and file hashes before restoring access.

Never drop the Image table or delete reconciled files as an automatic rollback
step.

## Completion evidence

Before moving 0024 to `complete`, preserve:

- all migration SQL and exact outputs;
- schema/table/index definitions and Image row counts;
- changed source and test file list;
- canonical path and case policy;
- upload compensation and publication-failure protocol;
- exact UploadFile compatibility response contract;
- responder test/build results;
- disposable full-stack smoke results;
- first dry-run, apply, second dry-run and second-apply summaries;
- conflict dispositions;
- complete 0022 candidate cross-reference with no unreported candidate;
- database row/file/retained-topic convergence counts;
- production component versions and backup identifiers;
- rollback reference and maintenance-window record;
- confirmation that no Fragment, Marquee or legacy HTML was changed and that no
  ImageFragment was created.

## Definition of done

0024 is complete only when:

- every newly uploaded supported image creates exactly one file/Image/topic;
- every Image path is canonical, portable and unique under the agreed policy;
- metadata is derived from bytes and contains no deployment URL/absolute path;
- generic file operations cannot replace or delete catalogued bytes;
- existing supported files can be catalogued idempotently;
- catalogue/file drift and conflicts are reported rather than silently repaired;
- every supplied 0022 candidate appears once in cross-reference evidence;
- retained replay reproduces the database Image catalogue after restart;
- all automated and disposable full-stack tests pass;
- production reconciliation evidence is archived;
- no ImageFragment or consumer rendering/authoring behaviour has been introduced.
