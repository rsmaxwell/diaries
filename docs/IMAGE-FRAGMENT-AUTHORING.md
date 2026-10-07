# ImageFragment authoring and operations

This document records the durable developer and operator contract established by 0027-FEAT. It complements `ARCHITECTURE.md`, `diaries-client/README.md` and the responder's 0025 ImageFragment contract documentation.

## Data model and retained state

Both Fragment types share the same Page ownership, date, sequence, transcription, version and lock model.

```text
MARQUEE -> `type=MARQUEE` (or legacy null type), no Image, optional/expected Marquee
IMAGE   -> `type=IMAGE`, `marqueeId=null`, zero or one `imageId`
```

A catalogued Image is a reusable entity. Its metadata is durable in PostgreSQL and distributed as retained `diaries/images/<id>` MQTT state. Its bytes remain in the selected mutable Files root and are served through the responder/static `/files/...` route. Fragment/Image identity therefore uses the database `imageId`, never the filename or absolute URL.

## Editor workflows

The MARQUEE `+` workflow is unchanged. IMAGE creation uses a separate **Add Image Fragment** action:

1. Require a selected diary/page/day context with authoritative `Fragment.pageId`.
2. Open the existing Files dialog in catalogue-Image selection mode, normally under `<diary>/images`.
3. Allow selection only of a file entry with a positive persisted `imageId`.
4. Acquire no Fragment lock while browsing because no existing Fragment is being changed.
5. Revalidate diary/page/day context after the chooser closes.
6. Compute a position in the common Fragment sequence and issue exactly one `addImageFragment` RPC.
7. Let retained Fragment/Image state become the long-lived UI model.

For an existing IMAGE Fragment, **Select/replace Image** and **Clear Image** are deliberate relationship edits. Revalidate the current selected Fragment, acquire the normal Fragment edit lock, then send the explicit mutation. Do not infer identity from the currently displayed path or URL.

## MQTT RPC wire semantics

Ordinary Fragment updates deliberately omit relationship/identity fields that remain responder-authoritative. For the Image relationship, omission is meaningful:

```text
updateFragment without imageId -> preserve current Image reference
updateFragment imageId=123     -> attach/replace with Image 123
updateFragment imageId=null    -> clear the Image reference
```

The Angular client enforces this separation with `UpdateFragmentRequest` for ordinary editing and `UpdateImageFragmentRequest` only for explicit Image-reference authoring. Day-view mixed-type reorder also uses the ordinary preserve path.

`addImageFragment` is not idempotent. If a transport/server failure leaves creation outcome unconfirmed, refresh/reconcile retained/database state before retrying rather than blindly issuing another create.

## Retained Image lookup and URLs

`ModelContext.selectedImage$` subscribes to `diaries/images/<imageId>` only for an explicit IMAGE Fragment with a positive Image ID. Switching the Fragment's Image ID clears the previous projection while the new retained object resolves. Tombstones, unresolved references and `imageId=null` become a stable no-Image/unresolved presentation rather than being converted to another Fragment type.

The client builds the image URL at runtime from:

```text
Config.baseUrl + Config.files + CatalogueImage.relativePath
```

`relativePath` is encoded one path segment at a time. It remains independent of the development/production Files-root location.

## Deletion rules

The two delete operations have different ownership:

```text
Delete Fragment -> removes the Fragment; reusable Image survives
Delete Image    -> removes catalogue metadata/file/topic only when no Fragment references it
```

The responder is authoritative for the Image reference check. A 409/reference conflict must leave the Image row, retained topic and physical file intact. Removing the last Fragment reference does not implicitly delete the Image.

## Authoring gate

The responder configuration property is:

```json
"imageFragmentWritesEnabled": true|false
```

The gate controls only new IMAGE creation and actual `imageId` mutations. When false, those actions return 403. Existing IMAGE Fragments can still be read, locked/unlocked, edited for text/date/sequence, normalised and deleted because those operations preserve/omit `imageId`.

Production renders the property from Ansible `diaries_image_fragment_writes_enabled`. With 0027 closed, the normal role default is `true`; the compatible reader, responder and client have passed the controlled disabled-gate and enabled-gate production verification. Rollback is non-destructive: set the variable to `false`, redeploy/restart the responder, and keep existing IMAGE rows and Files data unchanged.

For local operation, `true` is also the normal value. Direct development reads the developer-owned `%USERPROFILE%\.diaries\responder.json` (via the generated effective development config). `local-docker-build` and `local-published-smoke` use the external responder JSON selected by `DIARIES_RESPONDER_DOCKER_CONFIG_FILE`, normally `%USERPROFILE%\.diaries\responder.docker.json`, mounted as `/config/responder.json`. There is no environment-variable override for the gate itself. Use missing/null/false only when deliberately verifying the disabled gate or exercising rollback/emergency-stop behaviour.

The production client MQTT ACL must include read access to `diaries/images/+`; Fragment/RPC access alone is not sufficient to resolve catalogue metadata.

## 0027 production baseline

The completed production verification on 2026-10-06 used:

```text
client:    rsmaxwell/diaries-client:0.0.9-build-76
responder: rsmaxwell/diaries-responder:0.0.9-build-84
reader:    rsmaxwell/diaries-web:0.0.9-build-8
Step 14 run: 20261006-093834 (PASSED prerequisite)
Step 15 run: 20261006-133404 (PASSED controlled rollout/lifecycle)
```

The checked-in Diaries repository head associated with the final source snapshot is `c3528b0ea135ac2773855ec524605bd3910b5db8` (`Step 15 listFiles timeout correction`). The portable source bundle does not include Step 15's run-local `begin.txt`, so the deployed image tags above remain the authoritative portable production artifact identity. The source bundle used for final documentation is `diaries-sources-20261007-085928.zip`.

Production verification covered disabled-gate MARQUEE/IMAGE smoke, catalogue listing, deliberate enablement, IMAGE create, preserve edit, Image replace/clear/reattach, referenced-Image delete rejection, full restart/replay, editor/reader/MQTT/PostgreSQL/Files agreement, disposable Fragment cleanup, and rollback to the disabled gate during correction work.

## Troubleshooting checklist

When an ImageFragment editor/reader problem crosses components, inspect these together:

```text
browser console and selected Fragment/Image state
MQTT RPC request/reply (especially omitted vs null vs positive imageId)
retained diaries/fragments/<id> and diaries/images/<id>
responder log and authoring-gate state
PostgreSQL Fragment/Image rows
static /files/... URL and physical Files entry
client/web MQTT ACL delivery
```

A successful MQTT subscription acknowledgement does not prove retained Image payload delivery when a file ACL silently denies the topic.

## Durable tooling policy

0027 feature-specific Step 13–15 capture/rehearsal tools remain with the completed change-control evidence. Permanent cross-feature ImageFragment reader/regression tooling remains under `scripts/windows/validation/` with behavior-oriented names. No 0027 step-specific helper is retained in the normal live/deployed script directories.
