# 0023 implementation plan

## Execution status — 2026-09-11

The source implementation in phases 2–5 is complete and covered by automated
tests. The retained-contract fixtures cover typed MARQUEE, migration-window
legacy/null fields, explicit IMAGE, unknown fields and invalid known values.
Phase 6 automated tests and builds are complete as recorded below. The phase 1
deployed-state capture, retained MQTT broker integration (no broker was started
for this change), runtime smoke tests, deployment and production evidence remain
release activities and are intentionally not claimed here.

## Objective

Make `Fragment.pageId` and `Fragment.type`, introduced by 0022, the consumer-side
source of truth in `diaries-client` and `diaries-web`. Preserve the current
MARQUEE editing and reading behaviour, retain the compatibility `marqueeId`
field, and prepare both consumers for IMAGE fragments without implementing IMAGE
authoring or first-class IMAGE rendering in this feature.

The central relationship after this change is:

```text
Fragment.pageId -> Page.diaryId -> Diary
```

For a MARQUEE fragment, its Marquee is optional relationship data used for
annotation and controls. It is no longer the means by which the fragment's Page
or Diary is discovered.

## Boundaries and compatibility rules

1. `pageId` is authoritative when resolving a Fragment to a Page. Do not replace
   a supplied `fragment.pageId` with `marquee.pageId`.
2. A Marquee associated with a MARQUEE Fragment is valid only when its
   `fragmentId` equals the Fragment ID. Its `pageId` must also agree with the
   Fragment's authoritative `pageId`; disagreement is a diagnostic state.
3. `marqueeId` remains in retained Fragment payloads and update RPCs during the
   compatibility period. This feature does not remove it from either contract.
4. The production migration can contain `type=null` and `pageId=null` legacy
   rows. Consumer models must therefore accept missing or null values during the
   migration window instead of failing an entire retained-state replay.
5. A missing `type` is treated conservatively as legacy MARQUEE behaviour for
   compatibility. This fallback must be isolated in one helper and documented
   for removal in 0029; it must not turn an explicit `IMAGE` into a MARQUEE.
6. A missing or invalid `pageId` is reported as unresolved. It must not be
   guessed from date, sequence, selected route, or Marquee ownership.
7. An explicit `IMAGE` value must be decoded safely but must not expose Marquee
   creation/edit/delete controls. First-class Image lookup and rendering remain
   part of 0026/0027.
8. Unknown additional JSON fields remain harmless. Invalid known relationship
   values must produce controlled diagnostics or validation failures without
   silently changing ownership.
9. Date ordering remains date, then numeric sequence, then Fragment ID where an
   ID tie-break is required. Page ordering remains date, sequence, then ID.
10. The responder and database are not changed by 0023 unless a consumer test
    reveals an actual 0022 contract defect. Any such defect is recorded before
    widening scope.

## Phase 1 — capture the 0022 contract and baseline

- [ ] Record representative retained Fragment payloads from the deployed 0022
      responder for:
  - a healthy `type=MARQUEE` Fragment with `pageId` and `marqueeId`;
  - a MARQUEE Fragment with an authoritative Page but no available Marquee;
  - a legacy row with null/absent `type`;
  - a row with null/absent `pageId`;
  - an embedded-image legacy Fragment that must continue to render as legacy
    HTML during this feature.
- [ ] Record the current client and web behaviour for a healthy MARQUEE fragment,
      including route, selected marquee, source image, transcription, and day
      ordering.
- [ ] Add the new 0022 fields to retained-contract fixtures before changing
      projection logic. Keep a separate legacy fixture with omitted fields.
- [ ] Run the existing client test/build and `:diaries-web:test`/build to establish
      the pre-change baseline.

## Phase 2 — update the diaries-client model

### Model and compatibility helper

- [ ] In `diaries-client/src/app/model/fragment.ts`, add a shared
      `FragmentType` definition containing `MARQUEE` and `IMAGE`.
- [ ] Add migration-safe Fragment fields:

  ```typescript
  pageId: number | null;
  type: FragmentType | null;
  imageId?: number | null;
  ```

  If omitted properties must be distinguished from explicit null during the
  rolling window, make the raw properties optional and normalize them at the
  model boundary.
- [ ] Add small helpers such as `effectiveFragmentType(fragment)`,
      `isMarqueeFragment(fragment)`, and `hasAuthoritativePage(fragment)` so
      null compatibility behaviour is defined once rather than repeated in
      components.
- [ ] Keep `UpdateFragmentRequest` limited to the responder's existing update RPC
      fields. Confirm that adding projection fields to `Fragment` does not
      accidentally change the MQTT RPC payload.
- [ ] Update all client test factories and fixtures to include realistic
      `pageId` and `type` values.

### ModelContext and selection

- [ ] Audit `ModelContext` subscriptions and caches so Page membership is based
      on `fragment.pageId`, never on `marquee.pageId`.
- [ ] Preserve selected-Marquee discovery by matching
      `Marquee.fragmentId == selectedFragment.id`, but only for an effective
      MARQUEE Fragment.
- [ ] When the selected Fragment is not MARQUEE or has no matching Marquee,
      publish `selectedMarquee=null` and turn marquee edit mode off.
- [ ] Ensure a temporarily missing Marquee does not clear the selected Fragment,
      its date, or its transcription.
- [ ] Prevent a stale Marquee from a previously selected Page from being attached
      to a newly selected Fragment.
- [ ] Add focused ModelContext tests for healthy, missing, mismatched, and
      non-MARQUEE relationships, including retained events arriving in different
      orders.

### Navigation and workspace

- [ ] Change `DayviewComponent.goToFragment` to navigate through
      `fragment.pageId`, then `Page.diaryId`. Remove its current dependency on
      loading the Marquee to discover `pageId`.
- [ ] If `fragment.pageId` is absent or does not resolve, retain the visible day
      and show a controlled error rather than navigating using a guessed Page.
- [ ] After Page navigation, select a matching Marquee by Fragment ID when one is
      available. Missing Marquee is a supported state.
- [ ] In `FragmentComponent`, validate that the route Page agrees with the
      selected Fragment's `pageId`. Use the authoritative Fragment Page when
      correcting navigation; do not correct the Fragment from the route.
- [ ] Audit `ImageViewerComponent` add/delete/selection flows. New normal
      fragments remain MARQUEE fragments; existing deletion remains Fragment
      deletion even when a Marquee is absent.
- [ ] Confirm Day view selection still synchronizes in both directions:
  - selecting a day entry changes Page/Fragment and selects its Marquee if present;
  - selecting a marquee selects its Fragment and day entry.
- [ ] Add navigation tests proving that a Fragment with a valid `pageId` but no
      Marquee can still be opened.

### Type-aware controls

- [ ] Replace the page-header "has selected Marquee" assumptions with explicit
      derived capabilities:
  - create Marquee: effective MARQUEE Fragment, valid authoritative Page, no
    matching Marquee;
  - edit/delete Marquee: effective MARQUEE Fragment with a consistent matching
    Marquee;
  - IMAGE or unresolved Fragment: no Marquee controls.
- [ ] Recheck the same rules inside event handlers; disabled UI is not
      authoritative validation.
- [ ] If a MARQUEE Fragment has no Marquee, continue showing its transcription
      and present an unobtrusive unavailable/no-selection state over the source
      image.
- [ ] Add accessibility assertions for disabled control names and states.

## Phase 3 — update the diaries-web retained model

- [ ] Add a Java `FragmentType` enum containing `MARQUEE` and `IMAGE`.
- [ ] Extend `model/FragmentItem.java` with nullable `pageId`, `type`, and
      forward-compatible nullable `imageId`; retain nullable `marqueeId`.
- [ ] Put legacy-type normalization in one method rather than at each use site.
      Preserve the raw nullable type so diagnostics can distinguish explicit
      MARQUEE from compatibility fallback.
- [ ] Validate positive IDs when present. Do not reject the full replay merely
      because a known migrated legacy row has no Page/type.
- [ ] Update `fixtures/fragment.json`, `RetainedContractTest`, `TestData`, and all
      direct `FragmentItem` constructors.
- [ ] Add decoder tests for:
  - the complete 0022 MARQUEE payload;
  - missing/null migration fields;
  - explicit IMAGE with optional `imageId`;
  - unknown additional JSON fields;
  - invalid present IDs and invalid type values.

## Phase 4 — rebuild the diaries-web projection from Fragment ownership

- [ ] Rewrite the Fragment loop in `ProjectionSnapshot.build` in this order:

  ```text
  Fragment
    -> fragment.pageId
    -> Page
    -> page.diaryId
    -> Diary
    -> optional type-specific relationship
  ```

- [ ] Once Page and Diary resolve, add the Fragment to day/month/Page indexes
      even when its MARQUEE relationship is absent.
- [ ] For an effective MARQUEE Fragment, look up and attach a Marquee only after
      Page/Diary resolution. Verify both Fragment linkage and Page agreement.
- [ ] Do not attach a Marquee to an explicit IMAGE Fragment.
- [ ] Refactor `ResolvedFragment` so Marquee is explicitly optional. Reserve an
      optional Image relationship boundary for 0026 without adding an Image
      topic subscription in 0023.
- [ ] Keep `fragmentByMarqueeId` only as a compatibility/indexing convenience;
      it must not control whether a Fragment exists in chronology.
- [ ] Ensure tombstones and out-of-order retained delivery rebuild the same
      deterministic result.
- [ ] Preserve immutable snapshot collections and atomic replay swap behaviour.

### Relationship diagnostics

- [ ] Replace the ambiguous `fragmentsWithoutMarquee` counter with type-aware
      diagnostics that distinguish at least:
  - Fragment has no authoritative `pageId`;
  - referenced Page is missing;
  - Page's Diary is missing;
  - effective MARQUEE Fragment has no Marquee;
  - Marquee points to another Fragment;
  - Marquee Page disagrees with Fragment Page;
  - explicit IMAGE encountered before IMAGE projection support;
  - legacy/null type compatibility fallback is in use.
- [ ] Preserve existing Page/Marquee orphan diagnostics that remain useful.
- [ ] Update the status endpoint/model tests for the revised counters.

## Phase 5 — make diaries-web rendering tolerate an optional Marquee

- [ ] Update `WebServer.fragmentView` so missing Marquee produces
      `hasMarquee=false` and zero/absent crop geometry without dereferencing
      `resolved.marquee()`.
- [ ] The month reader must still show the Fragment text, date, Page image and
      navigation when the Marquee is absent.
- [ ] Update source-page view construction and templates so an unmarked Fragment
      remains listed while no overlay is drawn for it.
- [ ] Continue sanitizing legacy embedded-image HTML and resolving its safe image
      URLs exactly as before.
- [ ] Do not implement Image catalogue lookup, IMAGE media markup, captions, or
      IMAGE navigation presentation here; those belong to 0026.
- [ ] Add WebServer rendering tests for healthy MARQUEE, missing Marquee,
      mismatched Marquee, and legacy embedded-image HTML.

## Phase 6 — tests and end-to-end verification

### Automated validation

- [x] Run all diaries-client Angular tests. (65 passed.)
- [x] Run the diaries-client production build.
- [x] Run `gradlew.bat :diaries-web:test` from the parent `diaries` project.
- [x] Run `gradlew.bat :diaries-web:build`.
- [ ] Run retained MQTT integration tests where the local Mosquitto prerequisite
      is available.
- [x] Run `git diff --check` in the parent repository and both changed
      submodules, then inspect every changed file for unrelated work.

### Runtime smoke test against the 0022 stack

- [ ] Start an appropriate full local mode with a restored 0022 production-like
      database and current responder.
- [ ] Verify a representative healthy MARQUEE Fragment in both applications:
      Page image, marquee, text, date, ordering, selection and navigation.
- [ ] Verify a valid Page-owned Fragment whose Marquee is absent:
  - it remains visible in diaries-web chronology;
  - its source Page is available without a highlighted region;
  - diaries-client retains the Fragment and disables inappropriate controls.
- [ ] Verify a legacy/null-type embedded-image Fragment still renders using the
      temporary legacy-image resolver.
- [ ] Verify an unresolved null-Page legacy row is diagnosed and is not assigned
      to an invented Page or Diary.
- [ ] In diaries-client, edit and save an ordinary MARQUEE Fragment, edit its
      marquee, navigate away/back, and refresh. Confirm the retained state and
      database state converge and Page ownership remains unchanged.
- [ ] Restart the responder and both consumers. Confirm retained replay produces
      the same fragment counts, ordering, ownership and diagnostics.

## Deployment and rollback

1. Deploy the 0022-capable responder first; this is already the required
   production baseline.
2. Deploy `diaries-web` and `diaries-client` with the 0023 consumer changes.
   They may be deployed independently because 0022 retains `marqueeId` and the
   existing RPC contract.
3. Compare startup relationship diagnostics with the recorded 0022 inventory.
   Stop if a new Page/type anomaly appears or a healthy Fragment disappears.
4. Repeat the representative production read-only smoke tests in both
   applications. Perform one controlled ordinary MARQUEE edit in the client if
   the maintenance procedure permits it.
5. Preserve versions, logs, diagnostics and smoke evidence in this change
   record.

Rollback either consumer to its previous image if necessary. Do not roll back
or remove the additive 0022 database columns. Do not enable IMAGE authoring and
do not migrate legacy embedded images to first-class IMAGE rows as part of this
feature.

## Completion evidence

Before moving 0023 to `complete`, record:

- changed files in both consumer repositories;
- the exact legacy fallback rules implemented;
- updated diagnostic names and production counts;
- Angular test and production-build results;
- diaries-web test and build results;
- MQTT/full-stack tests actually run and any unavailable tests;
- representative browser checks for healthy, missing-Marquee, legacy-image and
  unresolved-Page states;
- deployed client/web/responder versions and rollback references;
- confirmation that no IMAGE authoring or first-class IMAGE rendering was
  introduced.
