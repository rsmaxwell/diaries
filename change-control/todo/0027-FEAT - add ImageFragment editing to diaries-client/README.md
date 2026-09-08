# 0027-FEAT - Add ImageFragment editing to diaries-client

## Type

Feature

## Status

To do

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

## Detailed Implementation Steps

- [ ] Add Image TypeScript model and retained Image cache/service.
- [ ] Add tests for Image replay, update and tombstone handling.
- [ ] Extend Fragment and RPC request models with type/pageId/imageId.
- [ ] Add `AddImageFragment` and image reassignment RPC methods.
- [ ] Add a clearly labelled, accessible IMAGE creation control.
- [ ] Add deployment feature gating for IMAGE creation.
- [ ] Generalize Fragment workspace initialization so IMAGE does not require a Marquee.
- [ ] Hide all selected overlays and marquee controls for IMAGE.
- [ ] Render the selected Image, caption and missing/incomplete state.
- [ ] Adapt the chooser to return a catalogued Image ID.
- [ ] Require the Fragment lock for Image replacement/removal.
- [ ] Ensure delete does not invoke `DeleteMarquee` for IMAGE.
- [ ] Test reuse of one Image from multiple IMAGE Fragments.
- [ ] Test mixed-type navigation, locking and sequence reorder.
- [ ] Test that invalid cross-type mutations are rejected and surfaced.
- [ ] Run Angular tests and production build.

## Acceptance Criteria

- [ ] Existing `+` retains MARQUEE semantics.
- [ ] IMAGE creation is unavailable until the reader deployment prerequisite is enabled.
- [ ] A user can create an IMAGE Fragment referencing zero or one Image as allowed by 0025.
- [ ] A user can select or replace one catalogued Image by ID.
- [ ] A user cannot attach multiple Images to one Fragment.
- [ ] IMAGE never creates or edits a Marquee.
- [ ] MARQUEE cannot select an Image.
- [ ] One Image can be reused by multiple IMAGE Fragments.
- [ ] Locks, date/text editing and sequence ordering work for both types.
- [ ] Runtime configuration, not persisted absolute URLs, determines Image URLs.
- [ ] Existing MARQUEE editing is not regressed.
- [ ] Angular tests and production build pass.

## Dependencies

Requires 0022–0026. Production enablement specifically requires evidence that the deployed 0026 web reader renders IMAGE, missing-Image and mixed chronology states.

## Deployment and Rollback

Deploy with creation disabled, smoke-test retained Image selection, then enable creation. After the first production IMAGE Fragment exists, rolling back the authoring client is possible, but rolling back the web reader below 0026 is not. Disabling authoring does not remove already-created IMAGE rows.

