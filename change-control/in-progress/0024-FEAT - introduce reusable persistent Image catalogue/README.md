# 0024-FEAT - Introduce reusable persistent Image catalogue

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-09-07

## Summary

Introduce `Image` as a durable, reusable metadata entity backed by files beneath the configured Diaries Files root. Extend the existing upload infrastructure so successfully uploaded supported images are represented in PostgreSQL and retained MQTT state. Reconcile any existing uploaded image files into the catalogue without creating ImageFragments.

## Background

`UploadFile` already provides a substantial secure file-upload implementation including path normalization, size limit, supported image MIME types, SHA-256 verification and atomic promotion. `ListFiles` and the Angular file dialog already provide browsing infrastructure.

What is missing is a durable semantic object that can be referenced by ID from ImageFragments.

## Target Image Model

```text
Image
  id
  relativePath
  mimeType
  originalFilename
  width
  height
  checksum
  caption
  altText
```

An Image exists independently of Fragment usage and may have zero references.

## Expected Behaviour

- successful supported image upload produces both the file and one Image entity;
- Image metadata is persisted transactionally/consistently with upload outcome;
- Image is retained at `diaries/images/{imageId}`;
- Image metadata contains normalized relative path, content type, dimensions and checksum;
- existing uploaded image files can be imported/reconciled idempotently;
- upload/catalogue does not create any Fragment;
- duplicate/conflicting path handling is explicit;
- consumers can subscribe to a stable Image catalogue by ID.
- a file represented by an Image row cannot be deleted through generic `DeleteFile`;
- a catalogued image file cannot be silently overwritten through `UploadFile`.

## Scope

### Database / Responder Model

Add:

```text
model/Image.java
dto/ImageDBDTO.java
dto/ImagePublishDTO.java
repository/ImageRepository.java
repositoryImpl/ImageRepositoryImpl.java
```

Register `Image` in `GetEntityManager`.

Implemented Phase 2 path uniqueness (PostgreSQL 18, deterministic Unicode collation):

```text
UNIQUE INDEX ON image (lower(relative_path COLLATE pg_catalog.pg_unicode_fast))
```

Checksum may be indexed but should not necessarily be unique because intentional duplicate bytes at different historical paths may be legitimate.

### Upload Integration

Refactor `UploadFile` so the final successful image result can create/update catalogue metadata without duplicating its path/hash logic.

Because the current handler permits `application/octet-stream`, detect whether the resulting file is actually a supported image before creating an Image entity. Do not catalogue arbitrary non-image files as Image.

Read width/height using existing `MyImageUtilities` or a new focused helper. Persist the SHA-256 already computed by upload where possible.

If database Image creation fails after file promotion, implement compensation (remove the newly written file when safe) or redesign the transaction boundary so the caller never receives success for a file that lacks the required Image entity.

### MQTT

Add canonical retained topic:

```text
diaries/images/{id}
```

Extend responder database replay to publish all Image entities.

### Existing File Reconciliation

Create an explicit idempotent command/script/handler suitable for controlled migration. Required features:

```text
dry-run
configured files root
recursive scan
supported image detection
relative-path normalization
width/height extraction
SHA-256 calculation
create missing Image rows
skip already catalogued rows
report conflicts/unreadable/unsupported files
optional publish/replay verification
```

Do not create ImageFragments.

The reconciliation report must cross-reference, where possible, the unique embedded image paths inventoried by 0022. It does not decide whether a Fragment becomes IMAGE or remains MARQUEE; it records whether each candidate path resolves to exactly one Image, no Image, or an ambiguity for the reviewed migration in 0028.

### Immediate File-Integrity Boundary

Catalogue introduction changes file ownership semantics. In the same release:

- `DeleteFile` must normalize the requested path and reject deletion if an Image row owns that path;
- `UploadFile` must reject an overwrite when the target path is already catalogued;
- path comparison must use the same canonical relative-path rules as Image uniqueness;
- rejected operations must return a clear conflict response and leave the file, database and retained topic unchanged;
- directories containing catalogued files must not be recursively deleted through a generic operation.

This feature may initially require catalogued files to be deleted only by an administrator-controlled migration/reconciliation process. A public `DeleteImage` operation is completed in 0025 before any ImageFragment references can be created.

### Client / Web

No authoring/rendering required yet, but add model/decoder capability if useful for test tooling. Production visible behaviour may remain unchanged.

## Detailed Implementation Steps

- [x] Design the Image table and explicit migration SQL. See [migration/README.md](migration/README.md); applied and verified on development, with production execution reserved for Phase 11.
- [x] Add Image JPA model, repository and DTOs. Phase 3, Phase 4 retained replay and Phase 6 upload integration are implemented.
- [x] Register Image entity with the responder EntityManager factory. Phase 3.3 also wires the repository and adds Image context helpers.
- [x] Add `ImagePublishDTO` and retained-state contract test. Phase 4 includes real-broker replay, updates and tombstones.
- [x] Refactor UploadFile staging around a reusable resolved-upload result containing relativePath, mimeType, size/checksum and Path. See [6.1 evidence](evidence/phase-06-1-staging/README.md); full catalogue completion is now wired in 6.3.
- [x] Detect supported images from file content/type and extract dimensions. Phase 5 shared inspector is used by Phase 6 uploads.
- [x] Create Image metadata on successful image upload. See [6.3 evidence](evidence/phase-06-3-creation/README.md).
- [x] Return `imageId` and Image metadata from successful image uploads while preserving existing useful response fields where compatibility requires.
- [x] Implement compensation for partial failure in the Phase 5 shared service. Phase 6.3 uses it in UploadFile.
- [x] Extend database replay to include Image topics. See [Phase 4 evidence](evidence/phase-04-catalogue/README.md).
- [x] Implement dry-run/reconciliation utility for pre-existing uploads.
- [x] Test reconciliation twice to prove idempotency.
- [x] Run reconciliation against a copy of the actual Files directory and record counts/conflicts.
- [x] Cross-reference reconciled Images with the 0022 embedded-image candidate inventory.
- [x] Make generic `DeleteFile` reject catalogued paths and directories containing them. See [Phase 7 evidence](evidence/phase-07-delete/README.md).
- [x] Make upload reject silent overwrite of a catalogued path. Phase 6.2 checks ownership before staging and again under the promotion lock; see [conflict evidence](evidence/phase-06-2-conflicts/README.md).
- [x] Add path-alias, separator, case-policy and traversal tests for both guards.
- [x] Add Image catalogue lookup/listing mechanism needed by the future client chooser: canonical retained `diaries/images/{id}` topics. Consumers remain later work; no `ListImages` RPC added.

Phase 5 implementation and validation are recorded in
[shared services evidence](evidence/phase-05-services/README.md): 191 responder
tests passed, including PostgreSQL/MQTT integration, plus packaged Windows and
Linux checks. UploadFile integration is complete through 6.3; Phase 7 DeleteFile protection is implemented. Phase 8 reconciliation is implemented and proved on a copy of the actual Files root; see [evidence](evidence/phase-08-reconciliation/README.md). Phase 9 automated validation is complete: 237 responder, 50 web and 81 client tests plus 24 SQL scenarios passed, with all required builds and no skips; see [Phase 9 evidence](evidence/phase-09-validation/README.md). Phase 10 full-stack smoke testing passed with packaged applications and headless Chrome: uploads, guards, idempotent reconciliation and two restarts were verified; see [Phase 10 evidence](evidence/phase-10-smoke/README.md). Phase 11 production preparation and storage-capability verification are next. Twelve rejected images and thirteen ambiguous candidate references remain explicit data-review items. Live deployment remains later work.

## Acceptance Criteria

- [x] Image upload creates exactly one matching Image row/topic.
- [x] The Image URL can be derived from `relativePath` and configuration.
- [x] No absolute deployment URL is persisted.
- [ ] Existing uploaded supported images can be imported without duplicate rows on rerun.
- [x] Non-image files are not incorrectly catalogued.
- [ ] No ImageFragment is created by upload/reconciliation.
- [x] Retained replay after restart reconstructs the same Image catalogue.
- [x] Tests cover path, checksum, MIME, dimensions and failure compensation.
- [x] Generic file operations cannot delete or silently replace catalogued image bytes.
- [ ] Reconciliation records whether every 0022 candidate path is matched, missing, external or ambiguous.

## Dependencies

0022 is required for the overall target model; 0023 is recommended before ImageFragments are authored. This feature itself does not require `fragment.imageId` yet.

## Deployment and Rollback

Additive database/table/topic change. Back up database and Files root before production reconciliation. Rollback does not delete uploaded files automatically; restore database if catalogue migration must be undone. Do not roll back to a responder that permits unrestricted generic deletion while retaining an Image catalogue unless the catalogue is treated as read-only and operational access to deletion is disabled.
