# ImageFragment authoring and operations

This document records the durable developer and operator contract established by 0027-FEAT. It complements `ARCHITECTURE.md`, `diaries-client/README.md` and the responder's 0025 ImageFragment contract documentation.

## Data model and retained state

Both Fragment types share the same Page ownership, date, sequence, transcription, version and lock model.

```text
MARQUEE -> `type=MARQUEE` (or legacy null type); no catalogue Image or per-IMAGE link; optional/legacy Marquee
IMAGE   -> `type=IMAGE`; zero or one catalogue `imageId`, zero or one same-Page Marquee, optional per-Fragment `imageLinkUrl`
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

## 0051 — optional link and same-Page Marquee

An IMAGE Fragment may have zero or one source-page Marquee, independent of its optional reusable catalogue Image and optional clickable `imageLinkUrl`. The link is **per Fragment occurrence**, not a property of the shared Image. The nullable database field is `fragment.image_link_url` (`VARCHAR(4096)`); changing one occurrence's link must not change other Fragments using that Image.

Link writing uses the responder's validated IMAGE-extension mutation contract: distinguish **no link**, **explicit SET**, **explicit CLEAR** and **field omitted (preserve existing link)**. Only safe absolute HTTP/HTTPS destinations are accepted; preserve the approved path, query string and fragment without downloading the destination. Ordinary transcription/date/sequence/Image-reference edits must not erase a stored link. If an Image is cleared, its link may remain dormant until a later Image reference is restored.

Source Marquee attach/edit/remove uses ordinary Fragment/Marquee authorization, edit locking and optimistic version checking, with authoritative same-Page ownership. Preserve an existing Marquee's identity/version/geometry unless an explicit user edit changes it. Removing a Marquee does **not** delete its Fragment, catalogue Image or external link; deleting the Fragment may remove its dependent Marquee but **not** a reusable Image or physical file. The old rule that *IMAGE must not have a Marquee* is obsolete.

In the Angular Day Reader, the IMAGE header displays **`Image ID: N` immediately after Position** for a positive Image reference; a null reference displays the explicit no-Image state. The catalogue image renders **beneath the header**, before transcription text, for each fragment independent of current selection. Valid external image clicks are distinct from fragment selection and the separate **Show on source page**/Marquee highlight action. An unresolved image must not become a misleading clickable link. Legacy MARQUEE embedded HTML remains supported until reviewed 0028 conversion.

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

Production renders the original IMAGE gate from Ansible `diaries_image_fragment_writes_enabled`; the normal role default is `true`. **0051 adds the separate responder gate `imageFragmentExtensionsWritesEnabled`**, rendered from `diaries_image_fragment_extensions_writes_enabled`. The extension gate was deployed **false** with the coordinated new components and enabled in production on 21 November 2026 only after a protected rollback rehearsal, recovery checks and supported component verification.

Setting the extension gate to `false` again can stop **new extension-format writes**, but it does **not** remove existing link/Marquee records or make older binaries safe rollback targets after such a record has been written. After activation/first new-format write, recover using compatible images or a separately authorised, verified data restore. Never drop the additive schema column to imitate a rollback. The original `imageFragmentWritesEnabled=false` remains an independent stop on ordinary new IMAGE creation/reference mutation, not an undo operation.

For local operation, `true` is also the normal value. Direct development reads the developer-owned `%USERPROFILE%\.diaries\responder.json` (via the generated effective development config). `local-docker-build` and `local-published-smoke` use the external responder JSON selected by `DIARIES_RESPONDER_DOCKER_CONFIG_FILE`, normally `%USERPROFILE%\.diaries\responder.docker.json`, mounted as `/config/responder.json`. There is no environment-variable override for the gate itself. Use missing/null/false only when deliberately verifying the disabled gate or exercising rollback/emergency-stop behaviour.

The production client MQTT ACL must include read access to `diaries/images/+`; Fragment/RPC access alone is not sufficient to resolve catalogue metadata.

## 0051 production release and related features

Production feature activation was reported on **21 November 2026** with client `0.0.9-build-79`, responder `0.0.9-build-85` and public reader `0.0.9-build-9`. PostgreSQL has nullable `fragment.image_link_url` and all five containers passed post-deployment health checks. The owner subsequently confirmed the IMAGE link/optional-Marquee functional checks passed; the full Step 4 review and formal closure decision live in `change-control/in-progress/0051-FEAT - extend IMAGE fragments with links and optional marquees/evidence/Step 4/`.

0028 remains the independent, separately approved migration of legacy inline images. Its versioned reviewer must capture exact link decisions and optional Marquee identity/Page/geometry without automatically approving historical drafts. 0029's later destructive constraint and relationship cleanup **must retain valid IMAGE Marquees and links**. The 0052 Whitley Park media-location defect is a separate content correction, not a reason to change the IMAGE data contract.

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
