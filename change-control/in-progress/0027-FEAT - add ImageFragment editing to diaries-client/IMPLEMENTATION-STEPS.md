# 0027-FEAT - add ImageFragment editing to diaries-client

## IMPLEMENTATION-STEPS

**Status:** In progress  
**Primary repository:** `rsmaxwell/diaries-client`  
**Responder dependency:** `rsmaxwell/diaries-responder` 0025 ImageFragment persistence/RPC  
**Reader dependency:** 0026 ImageFragment-capable reader must be deployed and verified before production authoring is enabled.

## 1. Purpose

Add first-class ImageFragment authoring to `diaries-client` while preserving the existing MARQUEE Fragment workflow.

The feature must allow an editor to:

- create an `IMAGE` Fragment on the current diary day;
- select a catalogued Image for a new ImageFragment;
- inspect the Image currently referenced by an ImageFragment;
- attach, replace or clear that Image reference;
- continue editing the Fragment's transcription text, date and sequence using the existing Fragment editor;
- reorder IMAGE and MARQUEE Fragments together in the common day chronology;
- delete an ImageFragment without deleting the reusable Image catalogue entry or physical file;
- receive useful feedback when ImageFragment authoring is disabled by the responder or when a request is rejected.

The implementation must keep the client and responder contracts aligned. In particular, it must preserve the responder's `updateFragment` Image-selection semantics:

- `imageId` **omitted**: preserve the existing Image reference;
- `imageId: <positive id>`: attach or replace the Image reference;
- `imageId: null`: explicitly clear the Image reference.

This distinction is critical. Ordinary text/date/sequence edits and day-view reordering must continue to omit `imageId` unless the user explicitly changes the Image selection.

## 2. Current baseline and relevant existing behaviour

The current client already contains part of the required foundation:

- `Fragment` has `type?: 'MARQUEE' | 'IMAGE'` and `imageId?: number | null`.
- `effectiveFragmentType()` and `isMarqueeFragment()` already protect legacy/null-type MARQUEE compatibility.
- MARQUEE-only controls are disabled for explicit IMAGE Fragments.
- `TextPanelComponent` edits Fragment text/date through `updateFragment$()` and is not intrinsically MARQUEE-only.
- `DayviewComponent` already reorders all Fragments through the common `updateFragment` RPC.
- `deleteFragment` already has responder semantics appropriate for IMAGE Fragments: delete the Fragment only, leaving the reusable Image row/file/topic intact.
- the Files dialog already supports Image upload, listing and guarded Image deletion.
- the responder already implements `addImageFragment`, IMAGE-aware `updateFragment`, mixed Fragment locking/normalisation/deletion, and reference-aware `deleteImage`.
- the responder has the authoritative `imageFragmentWritesEnabled` authoring gate. Missing/false disables ImageFragment creation and Image-reference mutation with HTTP-style RPC status 403.

The main client gaps are therefore typed Image catalogue consumption, Image selection UI, an `addImageFragment` RPC wrapper, deliberate Image-reference update semantics, and regression/e2e coverage.

The implementation should be based on the latest available source. The GitHub baseline inspected while preparing this plan was approximately:

- `diaries-client`: `e18da846fe4d395f5714e1d85bd6d70f1f1db437`
- `diaries-responder`: `b7c1a3d5967888b4980935b90d561ebad2814a83`

If a newer local/source-bundle version is available when implementation starts, treat that newer source as authoritative and re-run Step 1 against it.

---

# Implementation sequence

## Step 1 - Freeze the client/responder ImageFragment contract and current regression baseline

**Implementation status (2026-10-03):** Contract/evidence freeze implemented. The full Angular unit-test command is recorded but could not execute in the implementation sandbox because npm dependencies are not bundled and network access is unavailable; a focused serializer smoke passes and the existing responder contract tests are captured in evidence.

Before changing UI behaviour, capture the exact current contract between `diaries-client` and `diaries-responder`.

### Work

1. Record the current `Fragment` retained payload shape, especially:
   - `id`
   - `pageId`
   - `type`
   - `imageId`
   - `marqueeId`
   - date/sequence/version/text
   - edit-lock fields.
2. Record the responder `addImageFragment` request/reply contract.
3. Record the existing `updateFragment` request produced by `UpdateFragmentRequest.fromFragment()`.
4. Confirm that the current client does **not** send `imageId` during ordinary updates.
5. Capture the current Files RPC additive Image metadata already exercised by the 0024/0030 compatibility tests.
6. Run the existing client unit tests and record a clean baseline before changes.
7. Record the responder authoring-gate behaviour for:
   - `addImageFragment` while disabled;
   - changing `imageId` while disabled;
   - ordinary IMAGE text/date/sequence edits while disabled.

### Acceptance criteria

- Existing tests are green or any pre-existing failures are recorded.
- The wire-level preserve/set/clear rules for `imageId` are documented.
- No implementation work proceeds on an assumed or guessed RPC shape.

### Evidence

Store the baseline test output and representative request/reply JSON under the 0027 evidence directory.

---

## Step 2 - Freeze the ImageFragment authoring UX and invariants

**Status: COMPLETE — 2026-10-03.** The authoring workflow, action boundaries, locking boundaries and cross-type invariants are frozen in `evidence/Step 2/`. This step deliberately changes no production UI or RPC behaviour; implementation begins in later steps.

Define the intended editor behaviour before wiring buttons directly into existing components.

### Recommended initial UX

Use explicit ImageFragment actions rather than overloading the existing **Add fragment with default marquee** action.

The first release should provide:

1. **Add Image Fragment**
   - enabled when a page and a current Fragment/day context are selected;
   - opens the existing Files dialog in Image-selection mode at the diary's Image directory;
   - only a catalogued Image may be selected;
   - after selection, creates a new IMAGE Fragment immediately after the selected Fragment in the common sequence.

2. **Select/replace Image**
   - enabled only for a selected IMAGE Fragment;
   - opens the Files dialog in Image-selection mode;
   - selecting the currently attached Image is a no-op;
   - selecting another catalogued Image performs an IMAGE-reference mutation.

3. **Clear Image**
   - enabled only for a selected IMAGE Fragment with a non-null `imageId`;
   - requires an explicit confirmation because it deliberately creates an unattached ImageFragment;
   - clears the reference with `imageId: null` but does not delete the Image.

4. Existing Fragment actions continue to behave as today:
   - MARQUEE Add creates a MARQUEE Fragment with its default marquee;
   - Delete Fragment deletes either Fragment type;
   - Image deletion remains a separate catalogue operation.

### Invariants

- An IMAGE Fragment never gains a Marquee through the client.
- A MARQUEE Fragment never gains an `imageId` through the client.
- Fragment `type` and `pageId` are immutable after creation.
- Image selection does not change Fragment text/date/sequence unless the user also edits them through their normal controls.
- Selection/cancellation does not hold a Fragment edit lock while the user browses the Image catalogue.
- The responder remains authoritative for permissions, version checks, lock ownership, Image existence and the authoring gate.

### Acceptance criteria

- The UX and invariants are documented before implementation.
- Existing MARQUEE workflows remain clearly separate and unchanged.

---

## Step 3 - Add a first-class client Image model and retained Image lookup

**Status: COMPLETE — 2026-10-03.** `CatalogueImage`, retained `diaries/images/<id>` lookup, reactive `selectedImage$`, tombstone/unresolved-reference clearing and the shared static-file URL helper are implemented with focused regression coverage. Full Angular execution remains environment-blocked because dependencies are not present in the source bundle; focused TypeScript/helper validation is captured in `evidence/Step 3/`.

The client currently carries `imageId` on Fragment but has no first-class retained Image model in `ModelContext`.

### Work

1. Add a client `Image`/`CatalogueImage` interface matching the responder's retained `diaries/images/<id>` metadata projection:
   - `id`
   - `version`
   - `relativePath`
   - `mimeType`
   - `originalFilename`
   - `width`
   - `height`
   - `checksum`
   - `caption`
   - `altText`.
2. Add `ModelContext.getLiveImage$(id)` using `diaries/images/<id>` and the existing `LiveObjectService`.
3. Add a derived `selectedImage$` which:
   - emits the retained Image for an IMAGE Fragment with a positive `imageId`;
   - emits `null` for MARQUEE Fragments, unattached IMAGE Fragments, tombstoned Images or unresolved references.
4. Ensure subscriptions are share-replayed/cached consistently with existing live Page/Diary/Fragment access.
5. Add URL construction through one shared helper using the configured static Files root and `Image.relativePath`; do not duplicate ad-hoc URL concatenation in several components.

### Acceptance criteria

- Selecting an ImageFragment causes the corresponding retained Image metadata to become available reactively.
- A retained Image tombstone results in `selectedImage$` becoming null rather than leaving stale UI state.
- No Image bytes are transported over MQTT.

---

## Step 4 - Promote Files/Image catalogue metadata to typed client contracts

**Status: COMPLETE — 2026-10-03.** File/list/upload catalogue metadata is now typed in the client; the Files dialog has an explicit `catalogue-image` selection mode which only returns positive persisted Image IDs; and the responder `listFiles` payload is additively enriched with `imageId`/Image metadata for catalogued files. Generic browsing/delete behaviour is preserved. Focused model/static checks pass; full Angular and Gradle execution remain environment-blocked and are recorded in `evidence/Step 4/`.

The Files dialog already encounters additive catalogue fields in compatibility tests, but the production TypeScript interfaces do not expose them.

### Work

1. Extend `FileEntry` with optional catalogue information without breaking generic files/directories, for example:
   - `imageId?: number | null`
   - `image?: CatalogueImage | null` where returned by the responder.
2. Extend upload/list response typings for the additive Image fields already returned by the responder.
3. Extend `FileSelection` so a selection can return:
   - URL
   - filename
   - `imageId`
   - optional Image metadata/relative path.
4. In Image-selection mode, permit selection only for entries with a positive catalogue `imageId`.
5. Leave the Files dialog's normal browse and delete modes backward-compatible.
6. Give uncatalogued/non-Image files a clear disabled/non-selectable state rather than allowing the user to select a file path that cannot be attached to a Fragment.

### Acceptance criteria

- Existing Files compatibility tests continue to pass.
- Generic file browsing still works.
- ImageFragment authoring can obtain a persisted Image ID without deriving identity from a filename or URL.

---

## Step 5 - Add explicit `addImageFragment` client request and RPC support

**Status: COMPLETE — 2026-10-03.** The client now has a dedicated `AddImageFragmentRequest`, an `ImageFragment` reply type and `RpcService.addImageFragment$()` using the responder's `addImageFragment` function. The request preserves omitted versus explicit-null `imageId` JSON semantics, exposes no caller-controlled Fragment identity fields, and uses the existing authorised RPC/error path. Focused TypeScript/serialization checks pass; full Angular execution remains unavailable because dependencies are not installed in the supplied source bundle, and that test attempt is recorded in `evidence/Step 5/`.

Do not overload the existing `AddFragmentRequest`, because `addFragment` and `addImageFragment` deliberately create different Fragment identities.

### Work

1. Add `AddImageFragmentRequest` to the Fragment model with the responder contract:
   - `pageId`
   - `year`
   - `month`
   - `day`
   - `sequence`
   - `text`
   - optional `imageId`.
2. Add `RpcService.addImageFragment$()` using function `addImageFragment`.
3. Deserialize the reply as the committed `Fragment` payload.
4. Do not send caller-controlled `type`, `marqueeId` or Fragment `id`.
5. Add focused RPC serialization tests.
6. Verify 400/401/403/500 errors propagate through the existing `RpcError` mechanism.

### Acceptance criteria

- A focused test proves the client sends exactly the required `addImageFragment` fields.
- A successful reply is typed as an IMAGE Fragment with `marqueeId: null`.
- Existing `addFragment$()` is unchanged.

---

## Step 6 - Make `updateFragment` Image mutation explicit and tri-state

**Status: COMPLETE — 2026-10-03.** Ordinary updates continue to omit `imageId`; deliberate IMAGE reference changes use the separate `UpdateImageFragmentRequest` / `RpcService.updateImageFragment$()` path. Focused serialization and source checks pass; full Angular and responder test execution are environment-blocked and recorded under `evidence/Step 6/`.

This is the most important compatibility step.

The current `UpdateFragmentRequest.fromFragment()` is appropriate for ordinary edits because it omits `imageId`. Do not replace it with a serializer that automatically includes every `Fragment` property.

### Work

1. Preserve an update path for ordinary Fragment edits that **omits** `imageId`.
2. Add an explicit Image-selection mutation API, for example one of:
   - `updateImageFragment$(fragment, imageId: number | null)`, or
   - an `UpdateFragmentRequest` factory accepting a discriminated mutation such as `preserve | set | clear`.
3. Ensure the resulting wire requests are exactly:
   - preserve: no `imageId` key;
   - set/replace: positive numeric `imageId`;
   - clear: JSON `imageId: null`.
4. Continue sending the full required Fragment edit fields: id/version/date/sequence/text.
5. Do not permit the client API to change `type` or `pageId` after creation.
6. Add tests proving:
   - TextPanel save omits `imageId` for IMAGE Fragments.
   - Day-view reorder omits `imageId` for IMAGE Fragments.
   - attach/replace includes a positive ID.
   - clear includes explicit null.

### Acceptance criteria

- Ordinary IMAGE edits remain allowed when the responder authoring gate is off.
- Only deliberate Image-reference actions are interpreted as Image authoring mutations.
- MARQUEE Fragment requests cannot accidentally contain a non-null `imageId`.

---

## Step 7 - Implement Add ImageFragment workflow

**Status: COMPLETE — 2026-10-03.** A distinct accessible Add Image Fragment action now opens the Files dialog in `catalogue-image` mode at the selected diary Image directory, revalidates page/day context after selection, inserts through the shared Fragment sequence-gap rule, sends exactly one `addImageFragment` RPC, clears Marquee selection and navigates to the returned owning page. Cancellation sends no RPC; responder 403 and ambiguous failures have explicit handling. Focused helper/static validation passes; full Angular execution remains environment-blocked because dependencies are absent and is recorded under `evidence/Step 7/`.

Add the creation workflow after Steps 3-6 have stable types and RPCs.

### Work

1. Add a distinct **Add Image Fragment** control to the page header/editor workspace.
2. Enable it only when enough chronology context exists to create a valid Fragment.
3. Prefer inserting after the currently selected Fragment using the existing sequence-gap calculation rather than inventing a second Image-only chronology.
4. Open the Files dialog at `<diary>/images` in catalogue-selection mode.
5. Do not acquire a Fragment lock while the dialog is open; creation has no existing Fragment to lock.
6. On selection, call `addImageFragment$()`.
7. On success:
   - select the returned Fragment;
   - clear Marquee selection;
   - navigate to the returned Fragment on its owning page;
   - rely on retained MQTT state as the live source of truth.
8. On cancellation, perform no RPC.
9. On 403, show a specific message such as "ImageFragment authoring is disabled in this environment" rather than a generic failure.
10. Do not automatically retry ambiguous creation failures because `addImageFragment` is not idempotent.

### Acceptance criteria

- A catalogued Image can be used to create an IMAGE Fragment.
- The new Fragment appears in the common day chronology through retained MQTT state.
- No Marquee is created.
- Cancellation produces no state change.

---

## Step 8 - Implement ImageFragment Image-reference editing

**Status: COMPLETE — 2026-10-03.** The editor now renders retained Image metadata/preview for selected IMAGE Fragments, supports catalogue-based select/replace and confirmed clear, opens the chooser/confirmation before locking, waits for the newly retained locked Fragment before using its current version, sends only the explicit tri-state Image mutation, avoids a second unlock after successful update, and uses the failed-edit unlock fallback on rejected/stale updates. Unresolved/tombstoned Image metadata remains repairable through Select/replace. Focused source/model validation passes; Angular/Karma execution remains environment-blocked because dependencies are absent and is recorded under `evidence/Step 8/`.

Add the attach/replace/clear workflow for an existing IMAGE Fragment.

### Work

1. Show the currently resolved Image metadata for the selected ImageFragment, preferably including:
   - filename/relative path;
   - thumbnail/preview;
   - Image ID;
   - caption/alt text where useful.
2. Provide **Select/replace Image**.
3. Open the Files dialog before taking the Fragment lock.
4. After the user chooses an Image:
   - verify the same Fragment is still selected/live;
   - if the Image ID is unchanged, exit without locking or RPC;
   - acquire the Fragment edit lock;
   - use the latest live Fragment/version available after locking;
   - send the explicit `imageId` mutation.
5. On successful update, do not send an additional unlock: successful `updateFragment` clears the lock on the responder.
6. On failure, invoke the existing failed-edit unlock fallback because 400/403/409 responses may leave the lock in place.
7. Implement **Clear Image** with confirmation and the same lock/update/error flow, sending explicit null.
8. If the referenced Image has disappeared/tombstoned, show the unresolved state but still allow the user to select a replacement.

### Acceptance criteria

- Attach, replace and clear all work against the responder contract.
- A stale version or wrong lock owner does not overwrite another editor's changes.
- The UI updates from retained Fragment/Image state rather than permanently trusting an optimistic local mutation.

---

## Step 9 - Verify type-neutral text/date/sequence editing and locking

**Status: COMPLETE — 2026-10-03.** IMAGE body/date editing and mixed sequence ordering are verified on the ordinary Fragment update path, preserving `imageId` by omission. Step 9 also fixes the save/selection race so late save completion cannot mutate a newly selected Fragment, and adds destruction/switch guards so late lock acquisition is released rather than leaked. Focused model/static/parser checks pass; Angular and Gradle execution remain environment-blocked and are recorded in `evidence/Step 9/`.

Image selection is only one part of ImageFragment editing. Existing Fragment editing must work unchanged for IMAGE Fragments.

### Work

1. Exercise `TextPanelComponent` with explicit IMAGE Fragments.
2. Verify body editing acquires and releases the existing Fragment lock correctly.
3. Verify date changes work and preserve `imageId`.
4. Verify day-view drag/reorder works across mixed MARQUEE and IMAGE entries and preserves Image references.
5. Verify normalisation results arrive through retained MQTT state with the correct version/image relationship.
6. Add regression coverage for switching between MARQUEE and IMAGE Fragments while an edit/lock is in flight.
7. Ensure MARQUEE-specific operations remain blocked for IMAGE Fragments.

### Acceptance criteria

- Text/date/sequence editing works for both Fragment types.
- The responder authoring gate may be false and ordinary IMAGE text/date/sequence edits still succeed.
- No lock is leaked when navigating away, cancelling, or handling an RPC failure.

---

## Step 10 - Complete mixed Fragment navigation, day-view presentation and deletion behaviour

**Status: COMPLETE — 2026-10-03.** The day reader now presents MARQUEE and IMAGE Fragments in one sequence-sorted chronology with explicit type/Image-reference metadata; IMAGE navigation is verified to use retained `pageId` and clear Marquee selection; and IMAGE deletion is verified to call only `deleteFragment`, retaining the catalogue Image/file. The Files dialog now explains referenced-Image 409 conflicts distinctly, while existing responder integration coverage proves Image deletion stays blocked until the final Fragment reference is removed. Focused static/parser checks pass; Angular and Gradle execution remain environment-blocked and are recorded in `evidence/Step 10/`.

The editor should make the two Fragment types understandable without splitting the chronology.

### Work

1. Update the day view to visibly distinguish IMAGE from MARQUEE Fragments without creating separate lists.
2. Keep one ordered sequence for all Fragment types.
3. For IMAGE entries, optionally show a compact linked-Image indicator/thumbnail sourced from retained Image metadata.
4. Confirm `goToFragment()` continues to use the Fragment's authoritative `pageId`.
5. Confirm selecting an IMAGE Fragment clears Marquee selection and never guesses a Marquee.
6. Test the existing Delete Fragment action with IMAGE Fragments.
7. Make deletion semantics explicit in UI/help text where needed:
   - deleting the ImageFragment removes the Fragment only;
   - it does not delete the reusable Image catalogue row/file.
8. Verify Image catalogue deletion continues to return 409 while any Fragment references the Image and succeeds only after references are cleared/deleted.

### Acceptance criteria

- Mixed days remain chronologically ordered and navigable.
- IMAGE Fragment deletion cannot accidentally delete the Image itself.
- Reference-aware Image deletion remains enforced end to end.

---

## Step 11 - Finish action-state, accessibility and error handling

**Status: COMPLETE — 2026-10-03.** ImageFragment authoring now uses one shared derived action-state service for IMAGE selection, attached-Image state, Add-context validity and in-flight mutation state. Duplicate Add/select/clear workflows are suppressed before a second dialog/RPC can start; new controls expose deterministic disabled/busy state, accessible labels/titles and polite status text; catalogue selection removes unselectable files from the tab order, supports Space selection and restores focus; and 400/401/403/409/500/timeout outcomes have distinct messages with 401 authentication explicitly separated from the 403 authoring gate. Failed mutations still leave retained MQTT Fragment/Image state as the only committed UI truth. Focused static, parser and executable message-mapping checks pass; Angular execution remains environment-blocked and is recorded in `evidence/Step 11/`.

Do a deliberate UI-state pass rather than leaving ImageFragment actions as raw event handlers.

### Work

1. Add derived action-state observables for:
   - selected Fragment is IMAGE;
   - selected IMAGE has an attached Image;
   - valid context for Add Image Fragment;
   - in-flight Image mutation.
2. Disable duplicate clicks while create/update is in flight.
3. Add accessible labels/titles for all new buttons.
4. Preserve keyboard navigation and focus behaviour in the Files dialog.
5. Add specific messages for common responder outcomes:
   - 400 invalid/stale data;
   - 401 authentication;
   - 403 ImageFragment authoring disabled;
   - 409 lock/conflict;
   - 500 unconfirmed/internal failure.
6. Ensure errors do not leave optimistic Image state displayed as committed truth.

### Acceptance criteria

- New controls have deterministic enabled/disabled states.
- Keyboard and screen-reader labels are covered by tests.
- 403 is clearly distinguishable from authentication failure and ordinary validation errors.

---

## Step 12 - Add focused unit and compatibility regression coverage

**Status: COMPLETE — 2026-10-04.** All 16 required Step 12 areas are mapped to executable Jasmine coverage, and the normal Windows development run completed with `TOTAL: 222 SUCCESS`. The earlier compile/runtime failures were test-fixture defects only and were corrected without production-code changes. Final evidence is under `evidence/Step 12/`, including `development-angular-test-green-20261004-001033.txt`.

Create tests before live deployment.

### Required test areas

1. `Fragment` compatibility helpers continue treating null/absent type as MARQUEE.
2. New Image model deserializes the responder retained projection.
3. `selectedImage$` follows `fragment.imageId` and retained Image tombstones.
4. Files dialog returns catalogued `imageId` and refuses uncatalogued files in Image-selection mode.
5. `addImageFragment$()` wire payload.
6. `updateFragment` preserve/set/clear wire payloads.
7. TextPanel IMAGE save omits `imageId`.
8. Day-view IMAGE reorder omits `imageId`.
9. New header controls enable/disable correctly for MARQUEE vs IMAGE.
10. Add ImageFragment success/cancel/403 paths.
11. Replace Image success/no-op/failure paths.
12. Clear Image confirmation/success/failure paths.
13. Successful update does not issue a redundant unlock.
14. Failed update performs the unlock fallback.
15. IMAGE Fragment delete leaves catalogue Image lifecycle separate.
16. Existing MARQUEE creation/edit/delete tests remain unchanged and green.

### Acceptance criteria

- The standard client test suite is green.
- Compatibility tests prove existing Files and Fragment RPCs have not changed accidentally.

---

## Step 13 - Run live MQTT/responder verification with authoring disabled and enabled

**Status: COMPLETE — 2026-10-05.** Development run `20261004-002349` completed both the gate-disabled and gate-enabled lifecycle phases and reconciled the Angular client, responder outcome/logs, MQTT RPC/status replies, retained Fragment/Image topics, PostgreSQL state and physical Files state. The live run exposed and corrected the Fragment→Marquee lifecycle regression, ordinary IMAGE `updateFragment` null-argument compatibility issue, delete-time sequence-normalisation gap and matching create-time sequence-normalisation gap. The final Angular/Karma suite is green at **229/229**, the focused responder `FragmentLifecycleContractTest` / `AddImageFragmentTest` / `AddFragmentContractTest` suite completed `BUILD SUCCESSFUL`, and the five representative redacted RPC request/reply pairs validate. Disposable diagnostic Fragments were cleaned up, the browser diagnostic capture was disabled and the responder was returned to `imageFragmentWritesEnabled=false`. Step 13 acceptance criteria are satisfied; see `evidence/Step 13/FINAL-RUNTIME-CLOSEOUT.md` and proceed to Step 14.

Use a disposable development/integration dataset before enabling anything in production.

### Phase A - gate disabled

With responder `imageFragmentWritesEnabled` missing/false, verify:

- existing IMAGE Fragments load correctly;
- IMAGE text edits succeed;
- IMAGE date edits succeed;
- mixed reorder succeeds;
- IMAGE Fragment deletion succeeds;
- Add Image Fragment returns 403;
- attach/replace/clear Image returns 403;
- the client unlocks cleanly after rejected mutations.

### Phase B - gate enabled

With `imageFragmentWritesEnabled: true`, verify:

1. upload/catalogue an Image;
2. create an ImageFragment using it;
3. reload/restart the client and verify retained state restores the relationship;
4. edit transcription text;
5. move date;
6. reorder among MARQUEE Fragments;
7. replace the Image reference;
8. confirm the first Image can be deleted only when no other Fragment references it;
9. clear the Image reference;
10. reattach an Image;
11. delete the ImageFragment;
12. verify the Image row/file/topic still exist after Fragment deletion;
13. finally delete the now-unreferenced Image through the catalogue UI.

### Evidence

Capture:

- browser console excerpts;
- responder logs;
- representative MQTT request/reply payloads, captured with the opt-in redacted Step 13 client RPC diagnostic so positive/null/omitted `imageId` wire states are explicit without storing authentication values or transcription text;
- retained `diaries/fragments/<id>` and `diaries/images/<id>` states;
- database rows before/after;
- Files tree before/after.

### Acceptance criteria

- Client, responder, retained MQTT state, database and physical Files state all agree after every lifecycle transition.

---

## Step 14 - Run full client/responder/reader regression and rollout rehearsal

**Status: IMPLEMENTED / WORKSTATION EXECUTION PENDING — 2026-10-05.** The repeatable Step 14 harness is implemented under `evidence/Step 14/`. It runs the full Angular client test/build gate, full responder and reader Java test/build gates, verifies named ImageFragment/delete-guard/restart/static-URL contracts from the generated reports, reruns the existing disposable 0026 browser/MQTT/HTTP reader verification against the current responder/web candidate, renders both local Compose modes, captures source/config hashes, and rehearses the production Playbooks order read-only with `imageFragmentWritesEnabled=false`. **The Step 13 prerequisite is closed.** Step 14 remains open until one real workstation run plus the current production-role rehearsal are green.

0027 must not be closed by testing `diaries-client` in isolation.

### Work

1. Run normal `diaries-client` tests/build.
2. Run relevant `diaries-responder` ImageFragment contract/integration tests.
3. Verify the 0026 reader correctly renders ImageFragments created/edited by the client.
4. Verify older MARQUEE-only diary content still behaves unchanged.
5. Restart responder/client to prove relationships restore from database + retained topic-tree state.
6. Verify production-like static file paths resolve Image URLs correctly.
7. Verify Image delete guard still sees references created by the client.
8. Rehearse the exact production deployment order while the responder authoring gate remains false.

### Acceptance criteria

- No regression in MARQUEE authoring.
- No mismatch between editor-created ImageFragments and the reader.
- Restart/replay reproduces the same state as before restart.

---

## Step 15 - Deploy non-destructively and enable production authoring deliberately

**Status: IMPLEMENTED / PRODUCTION EXECUTION BLOCKED UNTIL STEP 14 PASSES — 2026-10-06.** Step 15 rollout tooling is implemented under `evidence/Step 15/`, and the production Playbooks role now exposes a fail-closed boolean `diaries_image_fragment_writes_enabled` instead of hard-coding the responder JSON to false. The role defaults the value to false, validates its type, renders/validates the responder JSON, and documents the same variable as the non-destructive rollback switch. The Step 15 runner refuses to begin unless a real Step 14 `step14-final-summary.json` is `PASSED`; the current source bundle still records Step 14 workstation execution as pending, so no production deployment or gate enablement is claimed yet.

Do not enable the responder gate merely because the client build contains the new buttons.

### Recommended rollout order

1. Confirm 0025 responder deployment is already present and healthy with the gate false.
2. Confirm the 0026 ImageFragment-capable reader is deployed and verified.
3. Deploy the 0027 client with no database or Files migration.
4. Run production smoke tests while `imageFragmentWritesEnabled` is still false:
   - existing MARQUEE editing;
   - existing IMAGE viewing/text editing where applicable;
   - expected 403 for Image-reference authoring.
5. Capture production pre-enable retained/database/Files evidence.
6. Change the responder production JSON to:

   ```json
   "imageFragmentWritesEnabled": true
   ```

7. Restart the responder as required for the configuration change.
8. Run one controlled production ImageFragment lifecycle using a known test Image/day.
9. Verify client, reader, responder logs, MQTT retained state, database and Files tree.
10. Remove the controlled test Fragment/Image if it was created solely for verification.

### Rollback

If ImageFragment authoring shows a defect:

1. set `imageFragmentWritesEnabled` back to false;
2. restart the responder;
3. leave existing IMAGE data intact;
4. continue allowing read, text/date/sequence editing and deletion according to the responder's established gate semantics;
5. diagnose the client/responder mismatch before re-enabling authoring.

No database rollback should be required merely to disable authoring.

### Acceptance criteria

- Production authoring is enabled only after client + responder + reader compatibility is proved.
- Disabling the gate provides an immediate non-destructive authoring stop.

---

## Step 16 - Update architecture/operating documentation and close 0027

### Work

1. Update `diaries-client` README/developer documentation to describe:
   - IMAGE vs MARQUEE Fragment editing;
   - retained Image catalogue topics;
   - Image selection workflow;
   - preserve/set/clear `imageId` request semantics;
   - ImageFragment deletion vs Image deletion;
   - the responder authoring gate.
2. Document any new components/models/helpers introduced by 0027.
3. Record the exact client and responder versions/commits verified in development and production.
4. Store final test/evidence inventories under the change-control feature.
5. Generate the Step 16/final close-out record.
6. Move only durable operating tooling into live script directories; keep feature-specific verification tooling/evidence under the 0027 change-control evidence tree in line with the completed-feature tooling cleanup policy.

### Feature completion criteria

0027 can be closed when all of the following are true:

- ImageFragments can be deliberately created from a catalogued Image.
- An existing ImageFragment can attach, replace and clear its Image reference.
- Text/date/sequence edits preserve Image references unless explicitly changed.
- MARQUEE behaviour is unchanged.
- Mixed Fragment reordering works.
- Fragment locking/version rules are respected.
- Delete Fragment does not delete the reusable Image.
- Delete Image remains blocked while referenced.
- the client correctly handles the responder's disabled authoring gate.
- development live-MQTT verification is complete.
- client/responder/reader regression is complete.
- production rollout and post-enable verification are complete.
- architecture/operating documentation and evidence are complete.

---

# Expected source touch points

The exact changed-file list should be determined from the latest source at implementation time, but likely areas include:

- `src/app/model/fragment.ts`
- new Image model under `src/app/model/`
- `src/app/model/FileEntry.ts`
- `src/app/model/FileListResponse.ts` and/or upload response typings
- `src/app/model/model-context.ts`
- `src/app/mqtt/rpc.service.ts`
- `src/app/files-list-dialog/files-list-dialog.component.ts`
- `src/app/files-list-dialog/files-list-dialog.component.html`
- Files dialog tests
- `src/app/headers/pageheader/pageheader.component.ts`
- `src/app/headers/pageheader/pageheader.component.html`
- header tests
- `src/app/fragment/fragment.component.ts`
- `src/app/fragment/image-viewer/` only where the global Fragment actions still belong there
- `src/app/fragment/text-panel/` regression tests rather than unnecessary behaviour changes
- `src/app/dayview/`
- a small dedicated ImageFragment editor/summary component if this keeps Image-specific logic out of the already-large `ImageViewerComponent`
- README/developer documentation.

A dedicated ImageFragment component/service is preferable to continuing to grow `ImageViewerComponent` if the new create/select/replace/clear workflow would otherwise make that component responsible for both source-page Marquee interaction and reusable Image catalogue authoring.

# Non-goals

0027 should not:

- transport Image file bytes over MQTT;
- replace the existing HTTP/static-file path for Image transfer/display;
- change Image catalogue persistence or responder database schema;
- change Fragment type after creation;
- change Fragment page ownership after creation;
- cascade Image deletion from Fragment deletion;
- introduce a second sequence/normalisation model for IMAGE Fragments;
- weaken responder-side permissions, locking, version checks or the authoring gate;
- make filename/URL the identity of an Image when a persisted catalogue `imageId` is available;
- remove the rolling-migration MARQUEE fallback for legacy null Fragment types.
