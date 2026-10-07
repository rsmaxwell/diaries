# 0027-FEAT - Add ImageFragment editing to diaries-client

## Type

Feature

## Status

Complete — Steps 1–16 are complete. Development regression, cross-component verification and the deliberate production rollout passed; durable documentation is updated and the feature is closed.

## Priority

High

## Opened

2026-09-08

## Summary

Add first-class IMAGE Fragment creation and editing to `diaries-client` after the read-only web application can render the new type. Keep the existing `+` workflow for MARQUEE and introduce an explicit IMAGE action which selects one reusable catalogued Image.

## Preconditions and Enablement

- 0022–0025 are deployed.
- The 0026 web reader has been deployed and verified against a controlled IMAGE fixture.
- Image catalogue replay and reference-aware deletion are working.

The IMAGE creation control must be feature-gated or withheld from production until these conditions are satisfied. Merely having the 0025 RPC available is not authorisation to expose authoring.


## 0026 Reader Handoff — 2026-10-01

The 0026 reader prerequisite is now satisfied. The exact candidate was regression-tested with controlled mixed MARQUEE/IMAGE fixtures and deployed/verified on production target `pluto`:

```text
Git commit: e5aa410bcf83e73f83bf81cb5aee9571ccba2755
reader:      rsmaxwell/diaries-web:0.0.9-build-7
responder:   rsmaxwell/diaries-responder:0.0.9-build-82
client:      rsmaxwell/diaries-client:0.0.9-build-74
filesPath:   files
web MQTT:    read-only diaries/images/+; RPC denied
```

At 0026 production close-out, `imageFragmentWritesEnabled=false` and production contained zero IMAGE Fragment rows. 0026 therefore authorises **reader readiness only**; it does not authorise IMAGE creation. 0027 must retain its own feature gate/rollout decision, verify client behavior against the deployed reader, and enable production authoring only through its separately approved deployment. Once the first production IMAGE Fragment exists, the web reader must not be rolled back below 0026.

Authoritative reader evidence is in `../../complete/0026-FEAT - render ImageFragments in diaries-web/evidence/Step 15/`, with the final handoff in `evidence/Step 16/` of that completed feature.

## Step 1 — Client/responder contract and regression baseline

Step 1 freezes the pre-authoring client/responder contract before any IMAGE editing UI is introduced. The evidence is stored under `evidence/Step 1/`.

The frozen rule that later implementation must preserve is:

```text
updateFragment imageId omitted      -> preserve the existing Image reference
updateFragment imageId=<positive id> -> attach/replace the Image reference
updateFragment imageId=null         -> explicitly clear the Image reference
```

The current client ordinary-update serializer deliberately omits `imageId`; a characterization test now guards that existing behaviour for IMAGE Fragments. The responder's existing gate tests are also identified in the Step 1 evidence, including the live integration case proving that with `imageFragmentWritesEnabled=false`, Image-reference mutations are rejected while ordinary IMAGE text updates remain allowed.

The source and contract evidence was captured from `diaries-sources-20261003-190733.zip`. Full Angular test execution could not be reproduced in the implementation sandbox because the source bundle intentionally contains no `node_modules` and external package downloads are unavailable; the exact failed dependency/bootstrap attempts are retained in the Step 1 evidence rather than being reported as a successful test run.

## Step 2 — ImageFragment authoring UX and invariants

Step 2 freezes the client-side authoring behaviour before any IMAGE controls or RPC wiring are added. The authoritative design record is in `evidence/Step 2/`.

The first authoring release will keep MARQUEE and IMAGE creation visibly separate:

```text
Add fragment with default marquee  -> existing MARQUEE workflow, unchanged
Add Image Fragment                 -> choose one catalogued Image, then create IMAGE
Select/replace Image               -> IMAGE only; changes the Image reference
Clear Image                        -> IMAGE only; confirmed imageId=null mutation
Delete selected fragment           -> either Fragment type; does not delete Image
Delete Image                       -> separate catalogue operation; responder guards references
```

Normal IMAGE creation will select a catalogued Image before `addImageFragment` is sent. Cancelling the chooser creates nothing. The responder still permits an IMAGE Fragment with `imageId=null`; the editor reaches that state deliberately through the confirmed **Clear Image** action rather than through the normal creation path.

The frozen cross-type invariants are:

```text
IMAGE   -> no Marquee; zero or one catalogued Image reference
MARQUEE -> no Image reference; existing Marquee rules remain unchanged
```

`Fragment.type` and `Fragment.pageId` are immutable after creation. Image chooser browsing does not hold a Fragment lock. For replacement/clear, the client revalidates the selected Fragment after the chooser/confirmation, then obtains the existing Fragment edit lock before sending the explicit Image-reference mutation. The responder remains authoritative for authentication, authoring-gate state, lock ownership, optimistic version checks and Image existence.

No production TypeScript/HTML behaviour is changed by Step 2.

## Step 3 — First-class retained Image model and lookup

Step 3 adds the client-side retained Image foundation without exposing any ImageFragment authoring controls yet. The production client now has a metadata-only `CatalogueImage` model matching the responder's retained `ImagePublishDTO`, and `ModelContext` can resolve `diaries/images/<id>` through the existing reference-counted `LiveObjectService`.

`selectedImage$` derives only from an explicit `type: 'IMAGE'` Fragment with a positive `imageId`. It emits `null` for MARQUEE/legacy-null-type Fragments, unattached IMAGE Fragments, unresolved references and retained Image tombstones. When an IMAGE Fragment switches to a different Image ID, the old Image is cleared immediately while the new retained topic is being resolved; ordinary Fragment updates with the same `imageId` do not cause an unnecessary Image re-subscription.

A shared `buildCatalogueImageUrl()` helper now constructs presentation URLs from runtime `baseUrl`, configured `files` root and `CatalogueImage.relativePath`, encoding individual path segments. The retained MQTT model remains metadata-only: no file bytes, Blob/base64 payload or persisted absolute presentation URL is introduced.

Focused Step 3 evidence covers retained replay, live metadata update, tombstone handling, unresolved-reference clearing, Image-ID switching and URL construction. The full Angular suite could not execute in the implementation sandbox because the source bundle contains no `node_modules` and the offline npm cache still lacks `zone.js`; this limitation and the successful focused checks are recorded under `evidence/Step 3/`.

## Step 4 — Typed Files/Image catalogue contracts

Step 4 promotes catalogue identity from compatibility-only/additive JSON into explicit client types. `FileEntry` can now carry optional `imageId` and `CatalogueImage` metadata, while `uploadFile$` returns a dedicated `UploadFileResponse` matching the responder's additive upload contract. Generic directory/file entries remain valid when no catalogue fields are present.

The Files dialog now supports an explicit `selectionMode: 'catalogue-image'`. In that mode only a non-directory entry with a positive persisted `imageId` is selectable. Successful catalogue selection returns the URL/name plus the database Image ID and optional metadata/relative path; uncatalogued files remain visible but are visually dimmed and marked `aria-disabled`, and clicking them cannot attach a filename or URL as Fragment identity. Historical `{select: true}` callers still receive exactly `{url, name}`.

Implementation inspection found that `uploadFile` already returned catalogue identity but production `listFiles` still emitted only filesystem metadata. The responder has therefore been aligned additively: catalogued files are enriched with `imageId` and nested `ImagePublishDTO`, while directories and uncatalogued files retain the previous payload shape. This keeps client and responder behaviour consistent and means future ImageFragment authoring never has to infer Image identity from a path.

Focused strict TypeScript/model and static source checks pass. Full Angular/Karma execution remains unavailable because the source bundle contains no installed dependencies, and the responder Gradle test cannot bootstrap because Gradle 9.6.1 is not cached and external downloads are unavailable. The exact attempts are retained under `evidence/Step 4/`.

## Step 5 — Explicit AddImageFragment client RPC

Step 5 adds creation transport only; it does not yet expose an authoring button. `AddImageFragmentRequest` is deliberately separate from the existing MARQUEE `AddFragmentRequest` and contains only `pageId`, date, sequence, text and optional `imageId`. Fragment `id`, `type` and `marqueeId` remain responder-authoritative.

The optional Image reference preserves the responder wire contract exactly: a positive ID is serialized when supplied, an explicit `null` is retained, and an omitted `imageId` is absent from the JSON request. `RpcService.addImageFragment$()` sends function `addImageFragment` through the existing authorised RPC path and returns the committed payload as `ImageFragment` (`type: 'IMAGE'`, `marqueeId: null`). The existing `addFragment$()` MARQUEE wire shape is covered by the same focused regression spec and is unchanged.

Focused model serialization and TypeScript source parsing pass. The Angular/Karma command cannot execute in the implementation sandbox because the supplied source bundle has no installed Angular CLI/dependencies (`ng: not found`); the exact attempt is retained under `evidence/Step 5/`.

## Step 6 — Explicit tri-state Image-reference updates

Step 6 separates ordinary Fragment editing from deliberate Image-reference authoring. The existing `RpcService.updateFragment$()` path remains the preserve path and continues to serialize through `UpdateFragmentRequest.fromFragment()`, which has no `imageId` field. Text/date/sequence edits and day-view reordering of IMAGE Fragments therefore cannot accidentally trigger the responder authoring gate.

A new `UpdateImageFragmentRequest` and `RpcService.updateImageFragment$()` provide the only typed client path that emits `imageId` during `updateFragment`:

```text
preserve -> updateFragment$()              -> imageId key omitted
set       -> updateImageFragment$(..., 91)  -> imageId: 91
clear     -> updateImageFragment$(..., null)-> imageId: null
```

The deliberate mutation request accepts only an explicit IMAGE Fragment with `marqueeId: null`; a MARQUEE-shaped Fragment is rejected before an RPC is sent. Replacement IDs must be positive integers. Neither `pageId` nor `type` is present in either update request, so the client cannot use these APIs to change immutable Fragment ownership/type.

Regression coverage now ties the ordinary preserve path to both existing callers: `TextPanelComponent` saves and `DayviewComponent` reorder continue to call `updateFragment$()`, while focused RPC tests verify the wire request omits `imageId`. Separate RPC tests verify positive-ID replacement and explicit-null clear. The responder's existing `UpdateFragmentImageTest` confirms the matching server rules, including that the disabled authoring gate allows omission/preservation but rejects actual Image-reference changes.

Focused TypeScript serialization and parse checks pass. Full Angular execution remains unavailable because the supplied source bundle has no `node_modules`/Angular CLI, and the focused responder Gradle test cannot bootstrap because Gradle 9.6.1 is not cached and external downloads are unavailable. Exact attempts are retained under `evidence/Step 6/`.

## Step 7 — Add Image Fragment workflow

Step 7 exposes the first IMAGE creation workflow while preserving the existing MARQUEE `+` action unchanged. The page header now has a separately labelled **Add Image Fragment** control. It is enabled only when the selected diary, page and Fragment provide an authoritative page/day chronology context.

Creation opens the Files dialog at `/<diary>/images` with `selectionMode: 'catalogue-image'`, so only entries carrying a positive persisted Image ID can be chosen. The chooser is opened before any mutation and no Fragment lock is acquired because there is no existing Fragment to edit. Cancelling closes the workflow without an RPC or selection change.

After Image selection, the workspace rereads the live diary/page/Fragment context. If the active Fragment, owning Page or day changed while the chooser was open, creation is aborted. Otherwise the client computes the new sequence using the same gap algorithm as existing MARQUEE creation and sends one `addImageFragment` request containing the active page/date, empty initial text and the chosen `imageId`. The common sequence calculation is now a shared helper used by both creation paths, so IMAGE does not gain a separate chronology.

On success the returned IMAGE Fragment becomes selected, Marquee selection is cleared, and navigation uses the returned authoritative `pageId`; retained MQTT state remains the live list/state source. A responder 403 is surfaced as **ImageFragment authoring is disabled in this environment.** Ambiguous 500/timeout failures are not retried and instead instruct the user to refresh before trying again because `addImageFragment` is not idempotent.

Focused helper compilation/execution and static source checks pass. Full Angular/Karma execution remains unavailable because the supplied cumulative source has no installed Angular CLI/dependencies (`ng: not found`); the exact attempt is retained under `evidence/Step 7/`.

## Step 8 — Image-reference editing

Step 8 adds first-class editing of the reusable Image reference for an existing IMAGE Fragment. A dedicated workspace panel appears only for a valid `type: IMAGE`, `marqueeId: null` Fragment. It shows the retained catalogue Image ID, relative path, original filename, caption/alt text and a static-files preview derived from runtime configuration. If the Fragment still references an Image ID but the retained Image metadata is absent/tombstoned, the panel shows an explicit unresolved state while keeping **Select/replace Image** available for repair.

**Select/replace Image** opens the existing Files dialog in `catalogue-image` mode before taking a Fragment lock. Cancellation and choosing the already-current Image perform no lock and no RPC. After selection, the client revalidates the same Fragment/Page context, acquires the normal edit lock, waits for the responder's newly retained locked Fragment state, and sends `updateImageFragment$()` using that current Fragment/version. If the retained value already matches the requested Image after locking, the otherwise-unused lock is released without an update.

**Clear Image** requires explicit confirmation before taking the lock and then follows the same post-lock retained-state/update flow with `imageId: null`. The confirmation states that the Fragment remains and the reusable Image stays in the catalogue. Neither replace nor clear invokes Image deletion.

Successful `updateFragment` is allowed to clear its own responder lock and the client deliberately sends no extra unlock or optimistic local Fragment/Image mutation. Any failed/stale/authoring-gate mutation invokes `unlockFragmentAfterFailedEdit`; retained Fragment and Image topics remain the presentation source of truth. The workflow also waits up to five seconds for the newly published retained lock state rather than reusing a possibly stale pre-lock cached Fragment.

Focused model execution, TypeScript parsing and static client/responder contract checks pass. Full Angular/Karma execution remains unavailable because the supplied cumulative source contains no installed Angular CLI/dependencies (`ng: not found`); the exact command/output is retained under `evidence/Step 8/`.

## Step 9 — Type-neutral text/date/sequence editing and locking

Step 9 verifies that explicit IMAGE Fragments use the existing generic Fragment editor and ordering lifecycle rather than a parallel editing path. IMAGE body and date saves continue through `updateFragment$()` / `UpdateFragmentRequest.fromFragment()`, so `imageId` is omitted from the MQTT request and the responder preserves the existing Image reference. Date-picker cancellation releases the normal Fragment lock, and day-view reorder continues to mix MARQUEE and IMAGE entries in the same chronology.

The verification exposed and fixes an existing asynchronous save race: when Fragment A was saved and the user selected Fragment B before the RPC completed, A's success callback could clear B's local lock and A's failure callback could restore A into the editor. Save completion is now bound to the initiating Fragment ID. Selection/destruction does not race an in-flight save with an independent unlock; success only mirrors the unlock locally if the saved Fragment is still selected, while failure rolls back only that same selection and calls `unlockFragmentAfterFailedEdit()` for the original Fragment ID.

Lock acquisition is also destruction-aware. If a body/date lock completes after the editor has switched Fragment or been destroyed, the late lock is immediately released. Regression coverage exercises IMAGE text/date edits, lock acquisition/cancellation, MARQUEE↔IMAGE switching while a lock/save is in flight, failed-save cleanup, mixed chronology reorder and retained normalised version/Image state.

The responder's existing gate and integration tests remain the server-side proof that `imageFragmentWritesEnabled=false` still permits ordinary IMAGE updates with omitted `imageId`, while deliberate Image-reference mutations remain blocked. Static/model/parser checks pass. The Angular/Karma and responder Gradle runs remain unavailable in this sandbox because the required local dependencies/distribution are absent; the exact attempts are retained under `evidence/Step 9/`.

## Expected User Workflows

### MARQUEE Fragment

```text
LHS: Page image and editable selected marquee
RHS: fragment date and text
```

### IMAGE Fragment

```text
LHS: Page context with no selected marquee
RHS: fragment date and text
     selected Image preview
     select/change Image action
```

The accepted invariant is:

```text
MARQUEE Fragment -> optional Marquee, no Image
IMAGE Fragment   -> optional Image, no Marquee
```

A Fragment never selects multiple Images. One Image may be reused by several IMAGE Fragments.

## Models and Retained State

Complete the Angular models for:

```text
Fragment.pageId
Fragment.type
Fragment.imageId
Image
```

Subscribe to retained Image entities by ID. URL presentation must derive from runtime configuration and `Image.relativePath`; never persist or send an editor-origin absolute URL as fragment state.

## Creation

Keep the current `+` action as MARQUEE creation. Add a separately labelled IMAGE creation action.

`AddImageFragment` uses:

```text
pageId
year/month/day
sequence
text
imageId optional according to 0025
```

If the UI permits creation before Image selection, show an explicit incomplete state and do not confuse it with a successfully illustrated entry. Prefer selecting the Image within the creation flow so ordinary production creation is complete atomically from the user's perspective.

## Editing and Locking

- use the existing Fragment lock for date, text and Image selection changes;
- hide/disable marquee geometry controls for IMAGE;
- prevent changing Fragment type through an ordinary update;
- do not create/delete a Marquee while editing IMAGE;
- changing `imageId` references an existing Image and does not delete either Image;
- deleting IMAGE deletes only the Fragment;
- ordering remains entirely `Fragment.sequence`.

## Image Chooser

Reuse the existing files-dialog presentation where helpful, but selection returns an Image ID and metadata, not a raw path or URL.

The chooser must:

- show only catalogued supported Images;
- expose original filename, caption and a useful thumbnail;
- distinguish a reused Image from a duplicate upload;
- handle retained additions/tombstones while open;
- provide an accessible selection state;
- reject directories and uncatalogued files as Fragment references.

## Step 10 mixed navigation/deletion status

Step 10 is complete at source/regression level. The day reader keeps one `Fragment.sequence` chronology and visibly identifies MARQUEE versus IMAGE entries. Navigation uses the Fragment's authoritative `pageId`; Marquee selection is derived centrally by `ModelContext`, so MARQUEE entries resolve their matching retained Marquee while IMAGE entries resolve to no Marquee. Deleting an IMAGE Fragment uses `deleteFragment` only; the reusable Image catalogue row/file is retained and the UI states that explicitly. Image catalogue deletion remains separately guarded by the responder and returns 409 while any Fragment reference exists.

## Step 11 action-state/accessibility/error-handling status

Step 11 is complete at source/regression level. A workspace-scoped `ImageFragmentActionStateService` now derives selected-IMAGE, attached-Image, valid-Add-context and in-flight state for the header, Image-reference panel and workflow handlers. Add/select/clear authoring actions are mutually exclusive while a workflow is active, so duplicate clicks cannot open a second chooser or send overlapping ImageFragment mutations.

The new authoring controls expose explicit disabled/busy state, labels and titles. Catalogue selection gives valid Image entries an explicit accessible selection name, removes uncatalogued visible-only files from the tab order, supports Space activation, and opens with first-tabbable autofocus plus focus restoration.

ImageFragment create/reference-edit errors now distinguish 400 invalid/stale data, 401 authentication expiry, 403 responder authoring-gate denial, 409 lock/conflict and 500/timeout unconfirmed outcomes. In particular, 401 no longer shares the 403 deployment-gate message. Failed reference edits never patch `imageId` optimistically; retained Fragment/Image topics remain authoritative. No responder production change is required. Evidence is under `evidence/Step 11/`.

## Step 12 focused regression status

Step 12 is complete. The final normal-development-tree Angular/Karma run on 2026-10-04 built successfully, launched Chrome Headless and finished with **222/222 tests passing** (`TOTAL: 222 SUCCESS`). The preceding compile/runtime failures were isolated to test typing/fixture-observation defects and were corrected without production-code changes. Final evidence is under `evidence/Step 12/`, including `development-angular-test-green-20261004-001033.txt`.

## Step 13 live verification status

Step 13 is **COMPLETE — 2026-10-05**. Development run `20261004-002349` exercised both `imageFragmentWritesEnabled=false` and `true` across the Angular editor, Java responder, MQTT RPC/status replies, retained Fragment/Image topics, PostgreSQL and physical Files state. The final reconciliation found no unresolved mismatch. The responder finished with `imageFragmentWritesEnabled=false`, the development-only browser RPC diagnostic capture was disabled, and disposable diagnostic Fragments were removed.

The live execution exposed four integration defects and each was corrected, regression-covered and reverified before closure: the root Fragment→Marquee synchronizer was being torn down by route/topic cleanup; ordinary IMAGE `updateFragment` serialized `marqueeId:null`, which mqtt-rpc rejected before handler dispatch; `DeleteFragment` could leave a date chronology gap until startup repair; and `addFragment` / `addImageFragment` could persist an unclosed insertion chronology. Relationship derivation now remains authoritative in `ModelContext`, the ordinary update request omits responder-authoritative null fields, and create/delete paths normalise affected dates transactionally and republish changed survivors. The local `diaries-client` ACL also has the required narrow read access to retained `diaries/images/+` metadata.

Final regression evidence is green: Angular/Karma completed **229/229** (`TOTAL: 229 SUCCESS`); the focused responder suite covering `FragmentLifecycleContractTest`, `AddImageFragmentTest` and `AddFragmentContractTest` completed `BUILD SUCCESSFUL`; and the redacted RPC diagnostic importer validated all five required 403/200 request/reply pairs without authentication/password values or raw transcription text. The authoritative close-out is `evidence/Step 13/FINAL-RUNTIME-CLOSEOUT.md`; `CHECKLIST.md` and `MANUAL-EVIDENCE.md` are complete. **No further Step 13 lifecycle mutation is required. Step 14 subsequently completed successfully.**

## Step 14 full regression and rollout-rehearsal status

Step 14 is **COMPLETE — 2026-10-06**. Workstation run `20261006-093834` produced the PASSED prerequisite accepted by Step 15. The integrated gate covered the full Angular suite/build, responder and reader Java regressions/builds, named ImageFragment chronology/gate/delete-guard contracts, the disposable browser-level reader verification, local Compose rendering and the production-order rehearsal while the authoring gate remained false. Step 15's guarded runner subsequently accepted this PASSED summary, so the Step 14 rollout prerequisite is closed.

## Step 15 production rollout implementation status

Step 15 is **COMPLETE — 2026-10-06**. Production run `20261006-133404` first deployed/smoke-tested with authoring disabled, then deliberately enabled the inventory gate and completed the controlled ImageFragment lifecycle. The final verified images were client `0.0.9-build-76`, responder `0.0.9-build-84` and reader `0.0.9-build-8`. Evidence records successful create, preserve edit, replace/clear/reattach, referenced-Image delete guard, full restart/replay, editor/reader/MQTT/PostgreSQL/Files agreement and cleanup of disposable Fragments while retaining the reusable Image.

Two production issues discovered during rollout were corrected non-destructively: catalogue listing required a longer client RPC timeout, and the production client ACL required narrow read access to `diaries/images/+`. Disabled-gate rollback was exercised during correction work. After successful enablement and verification, IMAGE Fragment authoring is the normal supported production state; the Playbooks role default is `true`, while `false` remains the tested rollback switch.

## Step 16 documentation and feature close-out status

Step 16 is **COMPLETE — 2026-10-07**. The durable client, architecture, responder and operating documentation now describes the MARQUEE/IMAGE distinction, retained Image topics, catalogue chooser, tri-state `imageId` semantics, deletion boundaries, authoring gate/rollback and the client components/helpers introduced by 0027. Final release/evidence inventories and acceptance mapping are stored under `evidence/Step 16/`. Feature-specific verification tooling remains under change-control evidence; permanent ImageFragment regression tooling remains under `scripts/windows/validation/`. The feature directory is moved to `change-control/complete`.

## Detailed Implementation Steps

- [x] Add Image TypeScript model and retained Image lookup/service.
- [x] Add tests for Image replay, update and tombstone handling.
- [x] Add the explicit `AddImageFragmentRequest` creation contract and narrowed `ImageFragment` reply type.
- [x] Add `RpcService.addImageFragment$()` without changing existing MARQUEE `addFragment$()`.
- [x] Add explicit Image reassignment/clear RPC semantics.
- [x] Add a clearly labelled, accessible IMAGE creation control.
- [x] Add deployment feature gating for IMAGE creation.
- [x] Generalize Fragment workspace initialization so IMAGE does not require a Marquee.
- [x] Hide all selected overlays and marquee controls for IMAGE.
- [x] Render the selected Image, caption and missing/incomplete state.
- [x] Adapt the chooser contract to return a catalogued Image ID.
- [x] Require the Fragment lock for Image replacement/removal.
- [x] Ensure delete does not invoke `DeleteMarquee` for IMAGE.
- [x] Test reuse of one Image from multiple IMAGE Fragments.
- [x] Test mixed-type navigation, locking and sequence reorder.
- [x] Test that invalid cross-type mutations are rejected and surfaced.
- [x] Run Angular tests and production build.

## Acceptance Criteria

- [x] Existing `+` retains MARQUEE semantics.
- [x] IMAGE creation is unavailable until the reader deployment prerequisite is enabled.
- [x] A user can create an IMAGE Fragment referencing zero or one Image as allowed by 0025.
- [x] A user can select or replace one catalogued Image by ID.
- [x] A user cannot attach multiple Images to one Fragment.
- [x] IMAGE never creates or edits a Marquee.
- [x] MARQUEE cannot select an Image.
- [x] One Image can be reused by multiple IMAGE Fragments.
- [x] Locks, date/text editing and sequence ordering work for both types.
- [x] Runtime configuration, not persisted absolute URLs, determines Image URLs.
- [x] Existing MARQUEE editing is not regressed.
- [x] Angular tests and production build pass.

## Dependencies

Requires 0022–0026. Production enablement specifically requires evidence that the deployed 0026 web reader renders IMAGE, missing-Image and mixed chronology states.

## Deployment and Rollback

Deploy with creation disabled, smoke-test retained Image selection, then enable creation. After the first production IMAGE Fragment exists, rolling back the authoring client is possible, but rolling back the web reader below 0026 is not. Disabling authoring does not remove already-created IMAGE rows.



## Completion Summary

0027 adds first-class IMAGE Fragment authoring to the Angular editor while preserving the existing MARQUEE workflow and responder-authoritative invariants. The editor chooses persisted catalogue Images by ID, resolves their metadata from retained `diaries/images/<id>` topics, preserves Image relationships during ordinary edits by omitting `imageId`, and uses explicit positive/null mutations only for replace/clear actions. IMAGE Fragment deletion does not cascade to reusable Images; catalogue Image deletion remains reference-aware.

Development and production verification covered the browser client, MQTT RPC, retained Fragment/Image state, Java responder, PostgreSQL, static Files state and `diaries-web` reader together. Production verification used client `0.0.9-build-76`, responder `0.0.9-build-84` and reader `0.0.9-build-8`. The authoring gate remains a responder/Ansible control: normal post-0027 operation defaults to enabled, with `false` retained as the non-destructive rollback state.

## Git / release references

- Diaries repository checked-in source head for the final source snapshot: `c3528b0ea135ac2773855ec524605bd3910b5db8` (`Step 15 listFiles timeout correction`).
- Final documentation source bundle: `diaries-sources-20261007-085928.zip`.
- Step 14 accepted run: `20261006-093834`.
- Step 15 production run: `20261006-133404`.
- Production artifacts: `rsmaxwell/diaries-client:0.0.9-build-76`, `rsmaxwell/diaries-responder:0.0.9-build-84`, `rsmaxwell/diaries-web:0.0.9-build-8`.
- The portable source bundle does not contain the run-local Step 15 `begin.txt`; the image tags are therefore retained as the authoritative portable production artifact identity.

## Completed Date

2026-10-07
