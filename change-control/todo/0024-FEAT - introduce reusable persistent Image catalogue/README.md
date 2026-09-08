# 0024-FEAT - Introduce reusable persistent Image catalogue

## Type

Feature

## Status

To do

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

Recommended uniqueness:

```text
UNIQUE(relative_path)
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

- [ ] Design the Image table and explicit migration SQL.
- [ ] Add Image JPA model, repository and DTOs.
- [ ] Register Image entity with the responder EntityManager factory.
- [ ] Add `ImagePublishDTO` and retained-state contract test.
- [ ] Refactor UploadFile around a reusable resolved-upload result containing relativePath, mimeType, size/checksum and Path.
- [ ] Detect supported images from file content/type and extract dimensions.
- [ ] Create Image metadata on successful image upload.
- [ ] Return `imageId` and Image metadata from successful image uploads while preserving existing useful response fields where compatibility requires.
- [ ] Implement compensation for partial failure.
- [ ] Extend database replay to include Image topics.
- [ ] Implement dry-run/reconciliation utility for pre-existing uploads.
- [ ] Test reconciliation twice to prove idempotency.
- [ ] Run reconciliation against a copy of the actual Files directory and record counts/conflicts.
- [ ] Cross-reference reconciled Images with the 0022 embedded-image candidate inventory.
- [ ] Make generic `DeleteFile` reject catalogued paths and directories containing them.
- [ ] Make upload reject silent overwrite of a catalogued path.
- [ ] Add path-alias, separator, case-policy and traversal tests for both guards.
- [ ] Add Image catalogue lookup/listing mechanism needed by the future client chooser, preferably retained-topic driven rather than a second database-shaped API.

## Acceptance Criteria

- [ ] Image upload creates exactly one matching Image row/topic.
- [ ] The Image URL can be derived from `relativePath` and configuration.
- [ ] No absolute deployment URL is persisted.
- [ ] Existing uploaded supported images can be imported without duplicate rows on rerun.
- [ ] Non-image files are not incorrectly catalogued.
- [ ] No ImageFragment is created by upload/reconciliation.
- [ ] Retained replay after restart reconstructs the same Image catalogue.
- [ ] Tests cover path, checksum, MIME, dimensions and failure compensation.
- [ ] Generic file operations cannot delete or silently replace catalogued image bytes.
- [ ] Reconciliation records whether every 0022 candidate path is matched, missing, external or ambiguous.

## Dependencies

0022 is required for the overall target model; 0023 is recommended before ImageFragments are authored. This feature itself does not require `fragment.imageId` yet.

## Deployment and Rollback

Additive database/table/topic change. Back up database and Files root before production reconciliation. Rollback does not delete uploaded files automatically; restore database if catalogue migration must be undone. Do not roll back to a responder that permits unrestricted generic deletion while retaining an Image catalogue unless the catalogue is treated as read-only and operational access to deletion is disabled.
