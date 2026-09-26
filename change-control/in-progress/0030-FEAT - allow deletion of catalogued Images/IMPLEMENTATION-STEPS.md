# 0030-FEAT - Implementation Steps

## Objective

Implement a small explicit Image-deletion workflow without weakening the 0024 generic-file protections.

The implementation should be delivered in independently verifiable steps. Each step should keep the client/responder contract coherent and leave the repository buildable.

## Step 1 — Freeze the existing 0024 delete guard

Before adding `deleteImage`:

- run the existing responder tests proving `DeleteFile` rejects a catalogue-owned path;
- record the existing `deleteFile` request/response compatibility shape;
- add or retain an explicit regression assertion that `DeleteFile` is **not** a supported way to delete an Image.

Result:

```text
catalogued path + generic DeleteFile -> 409/conflict
```

This behaviour must survive every later step.

## Step 2 — Define the `deleteImage` RPC contract

Add a compatibility fixture for:

```json
{
  "function": "deleteImage",
  "args": {
    "subdir": "diary-1830/images",
    "name": "img2221.jpg"
  }
}
```

Define:

- required fields;
- authorization level;
- path validation;
- success payload;
- not-found/conflict/error status conventions.

Do not implement ImageFragment reference rules yet.

## Step 3 — Add repository/service deletion primitives

Extend `ImageRepository` only where required to support:

- lookup by canonical relative path;
- deletion by Image id/entity.

Keep canonical path identity in the existing repository/path-policy layer.

Add an `ImageCatalogueService` delete method which:

1. takes a canonical relative path;
2. serializes against upload/reconciliation;
3. finds the corresponding Image;
4. performs the recoverable filesystem/database protocol;
5. returns enough information to publish the tombstone.

Add unit tests around the service before exposing it through RPC.

## Step 4 — Implement recoverable physical-file deletion

Use a private same-filesystem staging location under the existing image staging area.

For a successful operation:

```text
original file
  -> atomic move to delete backup
  -> database delete/commit
  -> retained tombstone
  -> remove backup
```

Test:

- file exists;
- file missing unexpectedly;
- staging move failure;
- DB delete/commit failure;
- restore succeeds;
- restore fails and produces an explicit hard error;
- cleanup failure is logged and remains recoverable.

Do not permanently delete the only file copy before the database transaction is known to have committed.

## Step 5 — Add and register `DeleteImage` handler

Create:

```text
handlers/DeleteImage.java
```

The handler should:

- parse `subdir` and `name`;
- enforce `EDITOR` or stronger authorization;
- canonicalize through `ImagePathPolicy`;
- call `ImageCatalogueService`;
- publish the retained Image tombstone after durable deletion;
- map expected failures to stable RPC statuses.

Register it in `Responder.java`.

Add handler tests and wiring integration coverage.

## Step 6 — Add client RPC wrapper

Add `deleteImage$()` to `RpcService`.

Requirements:

- use the authenticated RPC mechanism;
- do not duplicate access-token handling;
- preserve existing timeout/error conventions for this small control operation;
- add file-RPC compatibility coverage.

No UI change yet.

## Step 7 — Add Files-dialog context menu

Add a right-click context menu to file cards.

Initial behaviour:

```text
right-click eligible image
    -> Delete image
```

Use Angular Material/CDK components where already practical.

Do not show the action for directories.

For the initial implementation, image-extension filtering is acceptable as a UI affordance, but responder catalogue lookup remains authoritative.

Add component tests for menu visibility and event handling.

## Step 8 — Add confirmation and operation flow

When **Delete image** is selected:

1. show a confirmation dialog;
2. on cancel, do nothing;
3. on confirm, call `deleteImage$`;
4. disable/restrain duplicate submission while the request is active;
5. on success, refresh the current directory;
6. on failure, show the controlled error and leave the dialog usable.

The user should not need to close and reopen the Files dialog.

## Step 9 — End-to-end development verification

Create a disposable uploaded image and verify:

```text
before:
  file exists
  Image row exists
  retained diaries/images/<id> exists

delete via Files dialog

after:
  file absent
  Image row absent
  retained topic absent
  Files dialog refreshed
```

Then verify:

- cancelling deletion leaves all three layers unchanged;
- trying generic `DeleteFile` against another catalogued Image still fails;
- deleting a non-catalogued image-looking file through `deleteImage` is rejected;
- upload of a new image to the deleted path behaves according to normal 0024 rules.

## Step 10 — Failure-path verification

Exercise controlled test doubles/integration fixtures for:

- DB failure after staging;
- MQTT tombstone publication failure;
- concurrent upload/delete of the same path;
- duplicate delete request;
- responder restart after completed deletion.

Verify that no test ends with an unreported split-brain state.

## Step 11 — Production deployment

Deploy responder first, then client.

Before the first production deletion:

- take/confirm the normal database and Files-root backup;
- record responder/client versions;
- choose a disposable test Image.

Run one controlled production deletion and preserve evidence of:

- pre-delete file, DB row and retained topic;
- UI confirmation;
- successful response;
- post-delete file absence;
- DB row absence;
- retained topic tombstone/absence;
- refreshed client file list.

## Step 12 — Close-out

Update the change record with:

- exact changed files;
- test/build results;
- production evidence;
- any deviations from the proposed failure protocol;
- known limitations.

Explicitly record that ImageFragment reference protection is deferred to the ImageFragment responder feature and must be implemented before production ImageFragment authoring is enabled.

Move the change-control directory to `complete` only when all acceptance criteria in `README.md` are satisfied.
