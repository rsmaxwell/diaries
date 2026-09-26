# 0030-FEAT - Allow deletion of catalogued Images

## Type

Feature

## Status

To do

## Priority

Medium

## Opened

2026-09-25

## Summary

Add an explicit supported operation for deleting an unreferenced catalogued `Image`, and expose it in `diaries-client` from the Files dialog as a right-click **Delete image** action.

This operation is deliberately separate from generic `DeleteFile`. The generic file operation must continue to reject paths owned by the Image catalogue.

The first implementation is intentionally small. It does not yet check whether an Image is referenced by an `ImageFragment`; that reference-aware guard becomes mandatory before ImageFragment authoring is enabled. The existing 0025 ImageFragment responder work remains responsible for introducing that reference-integrity rule.

## Background

0024 introduced the reusable persistent Image catalogue and established these invariants:

- supported uploaded images are represented both by bytes under the configured Files root and by a PostgreSQL `Image` row;
- Image metadata is retained at `diaries/images/{imageId}`;
- generic `DeleteFile` cannot delete a catalogue-owned file;
- generic upload cannot silently overwrite a catalogue-owned file;
- filesystem/database/MQTT state must not silently diverge.

During the 0024 production closure tests it became clear that there is currently no normal UI operation for deleting a catalogued Image. Attempting to use generic `DeleteFile` is correctly rejected by design.

A dedicated Image lifecycle operation is therefore required.

## User-visible behaviour

In the Files dialog:

1. right-click an image file;
2. choose **Delete image**;
3. confirm the operation;
4. the client sends an authenticated `deleteImage` RPC;
5. on success, the current file list refreshes and the deleted image disappears.

The confirmation should identify the filename, for example:

```text
Delete image "img2221.jpg"?

This removes the image from the Image catalogue and deletes the stored file.

Cancel    Delete
```

For this first version, no ImageFragment reference check is required because ImageFragment persistence/authoring is not yet enabled in production.

## Core design decision

Do **not** weaken or bypass `DeleteFile`.

The existing generic delete guard is correct and must remain:

```text
generic DeleteFile
    + catalogue-owned path
        -> reject with conflict
```

Introduce a dedicated semantic operation instead:

```text
deleteImage
    -> locate Image catalogue row
    -> coordinate physical-file and database removal
    -> publish retained MQTT tombstone
```

This keeps file ownership explicit and prevents future callers from bypassing Image lifecycle rules.

## RPC contract

Add an authenticated responder RPC named:

```text
deleteImage
```

Initial request shape:

```json
{
  "subdir": "diary-1830/images",
  "name": "img2221.jpg"
}
```

The responder, not the client, resolves the canonical catalogue path and identifies the corresponding Image row.

The caller must be an active user with `EDITOR` or stronger authorization.

### Success

A successful response should return status `200` and enough information for diagnostics/tests, preferably:

```json
{
  "id": 85,
  "relativePath": "diary-1830/images/img2221.jpg",
  "deleted": true
}
```

The exact payload may follow existing responder conventions, but it must be stable enough for compatibility tests.

### Errors

At minimum:

- `400` for malformed path/name input;
- `401/403` according to existing authentication/authorization conventions;
- `404` when no catalogued Image owns the requested path;
- `409` for lifecycle conflicts introduced later, including a referenced Image;
- `500` for unrecoverable filesystem/database coordination failures.

Do not report success if the responder has lost track of a partial failure.

## Responder scope

### New handler

Add:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteImage.java
```

Responsibilities:

- validate and authorize the request;
- resolve the path through `ImagePathPolicy`;
- delegate coordinated deletion to `ImageCatalogueService`;
- publish/return controlled errors using existing handler conventions.

Register the new handler in:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java
```

### Image catalogue service

Extend:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueService.java
```

with a focused delete operation.

The service owns the multi-resource lifecycle semantics rather than scattering them through the RPC handler.

Use the same Image catalogue critical section/locking strategy already used by upload/reconciliation so upload, deletion and catalogue changes cannot race on the same path.

### Repository

Use/extend:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/ImageRepository.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/ImageRepositoryImpl.java
```

The current repository already has path lookup and deletion support; only expose/add operations required by the service rather than duplicating JPA queries in the handler.

### Retained MQTT

After the durable database deletion succeeds, remove the retained Image state by publishing the existing Image tombstone operation through:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/ImagePublishDTO.java
```

to:

```text
diaries/images/{imageId}
```

The retained message must be a tombstone/zero-length retained payload using the established 0024 convention.

## Filesystem/database failure protocol

PostgreSQL and the NAS filesystem cannot participate in one atomic transaction. Image deletion must therefore use an explicit recoverable protocol.

Preferred sequence:

```text
acquire catalogue/path lock
    -> locate Image row by canonical relative path
    -> verify physical file state
    -> atomically move physical file to private same-filesystem staging backup
    -> delete Image row in database transaction
    -> commit transaction
    -> publish retained MQTT tombstone
    -> remove staged backup
    -> return success
```

If the database transaction fails:

```text
rollback DB
    -> move staged file back to original path
    -> return failure
```

If restoration fails, log both paths and return an internal error. Never claim successful deletion.

If retained tombstone publication fails after the database commit, do not recreate the database row merely to match stale broker state. Report/log the publication failure and rely on controlled retained-state replay/reconciliation to restore broker truth from PostgreSQL.

The implementation must be idempotent enough that a repeated request after a completed deletion returns a controlled not-found result rather than corrupting adjacent state.

## Client scope

### RPC service

Extend:

```text
diaries-client/src/app/mqtt/rpc.service.ts
```

with an authenticated wrapper, for example:

```typescript
deleteImage$(subdir: string, name: string)
```

Use the same authorized RPC path as the existing file operations. Do not put Image deletion logic into the component.

### Files dialog

Update:

```text
diaries-client/src/app/files-list-dialog/files-list-dialog.component.ts
diaries-client/src/app/files-list-dialog/files-list-dialog.component.html
diaries-client/src/app/files-list-dialog/files-list-dialog.component.scss
```

Add a right-click context menu to file/image entries.

Initial menu:

```text
Delete image
```

Behaviour:

- prevent the browser's default context menu for the file card;
- identify the current directory/subdirectory and filename;
- show a confirmation dialog;
- call `deleteImage$`;
- display a controlled error if deletion fails;
- refresh the current directory listing after success;
- keep the Files dialog open.

Prefer Angular Material/CDK menu/dialog facilities already available to the client over a custom absolute-positioned DOM implementation.

### Initial eligibility rule

For this first version, the client may expose **Delete image** only for filenames which look like supported image files (`jpg/jpeg/png/gif/webp`) or for file entries carrying Image catalogue metadata if that metadata is already available.

The responder remains authoritative. It must reject a path which is not actually represented by an Image row.

Do not make UI eligibility a security or integrity boundary.

## Tests

### Responder

Add focused tests for:

```text
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/handlers/DeleteImageTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueServiceTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/ImageWiringIntegrationTest.java
```

Cover at least:

- authorized successful deletion;
- unauthorized caller;
- non-catalogued path;
- invalid/path-traversal input;
- canonical path/case handling;
- physical file moved to staging before DB deletion;
- DB failure restores staged file;
- successful DB deletion publishes retained tombstone;
- MQTT publication failure is surfaced/logged without recreating deleted durable state;
- concurrent upload/delete of the same path is serialized;
- generic `DeleteFile` still rejects catalogue-owned paths.

### Client

Extend:

```text
diaries-client/src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts
diaries-client/src/app/mqtt/file-rpc-compatibility.spec.ts
diaries-client/src/app/testing/file-rpc-baseline.fixture.ts
```

Cover at least:

- right-click on eligible image exposes **Delete image**;
- cancel performs no RPC;
- confirm calls `deleteImage` with the expected `subdir` and `name`;
- success refreshes the current listing;
- failure leaves the dialog open and reports the error;
- wire contract for `deleteImage` is fixed by compatibility tests.

## Out of scope

This feature deliberately does **not** include:

- ImageFragment creation or editing;
- checking whether an Image is referenced by an ImageFragment;
- cascading Fragment deletion or mutation;
- deleting arbitrary non-catalogued files;
- directory deletion;
- bulk Image deletion;
- recycle bin/undelete;
- Image replacement;
- caption/alt-text editing;
- HTTP bulk-image upload redesign.

Before ImageFragment authoring is enabled, the later responder ImageFragment feature must extend `deleteImage` so a referenced Image is rejected with `409 Conflict`.

## Expected changed files

Likely responder changes:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/
  Responder.java
  handlers/DeleteImage.java
  repository/ImageRepository.java
  repositoryImpl/ImageRepositoryImpl.java        # only if new repository method required
  utilities/ImageCatalogueService.java

diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/
  handlers/DeleteImageTest.java
  utilities/ImageCatalogueServiceTest.java
  ImageWiringIntegrationTest.java
```

Likely client changes:

```text
diaries-client/src/app/files-list-dialog/
  files-list-dialog.component.ts
  files-list-dialog.component.html
  files-list-dialog.component.scss
  files-list-dialog.compatibility.spec.ts

diaries-client/src/app/mqtt/
  rpc.service.ts
  file-rpc-compatibility.spec.ts

diaries-client/src/app/testing/
  file-rpc-baseline.fixture.ts
```

The final implementation should minimize this list where existing helpers already provide the required behaviour.

## Acceptance criteria

- [ ] A user with `EDITOR` or stronger authorization can right-click a catalogued image in the Files dialog and choose **Delete image**.
- [ ] The user is asked for confirmation before deletion.
- [ ] Cancelling leaves filesystem, database and retained MQTT state unchanged.
- [ ] Confirming an unreferenced catalogued Image removes its physical file.
- [ ] The corresponding PostgreSQL `Image` row is removed.
- [ ] `diaries/images/{imageId}` is removed with a retained MQTT tombstone.
- [ ] The Files dialog refreshes and the image disappears without closing the dialog.
- [ ] A non-catalogued path is rejected by `deleteImage`.
- [ ] Invalid/path-traversal input is rejected.
- [ ] Generic `DeleteFile` still rejects catalogue-owned files.
- [ ] Database failure after staging restores the original file.
- [ ] The operation does not report success when filesystem/database state is uncertain.
- [ ] Client/responder compatibility tests cover the new RPC.
- [ ] Existing file upload/list/delete behaviour remains compatible.
- [ ] Responder and client test suites pass.

## Dependencies

Requires 0024 to be complete and deployed.

This feature must complete before any later production workflow relies on users being able to remove unused catalogue Images.

The already-defined ImageFragment persistence feature must add reference-aware deletion before ImageFragment authoring is enabled; at that point `deleteImage` must reject an Image referenced by any Fragment.

## Deployment and rollback

The responder capability may be deployed before the client UI because it is additive.

Recommended deployment order:

1. deploy responder with `deleteImage`;
2. verify RPC tests and one controlled production deletion;
3. deploy client UI;
4. verify right-click, cancel, successful deletion and list refresh.

Rollback before any production deletion is a normal application-image rollback.

After a successful production deletion, rollback must not attempt to resurrect the deleted Image automatically. Restoration of deleted content, if required, is a data/file backup operation rather than an application rollback.
