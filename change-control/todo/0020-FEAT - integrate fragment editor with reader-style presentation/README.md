# 0020-FEAT - Integrate fragment editor with reader-style presentation

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-04

## Stage

5 of 6

## Summary

Bring the main fragment editing screen into the same reader-style visual language as `diaries-web` and the newly restyled Angular reader views, while preserving the complete image/transcription editing workflow.

The fragment editor remains an editor: its controls, locking states, marquee operations, split layout and text editing affordances must remain explicit. The goal is visual integration, not removal of editor functionality.

## Background

The fragment component currently consists of a shared `pageheader`, a dynamically built `layout-container`, and a `pagefooter`. The principal split is between `app-image-viewer` and `app-text-panel`, each taking approximately half the available width.

The desired visual relationship to `diaries-web` is closest to its source layout: source image on one side and diary/transcription content on the other, with paper/surface colours, restrained borders, reader typography and a selected marquee. The Angular editor additionally supports creating/editing/deleting marquees, text editing, files and locking.

Recent work has also established that only the selected fragment's marquee should be shown. This must remain intact.

## Expected Behaviour

After this stage:

- the split image/transcription editor looks like a working/editor version of the `diaries-web` source view;
- image and text panes use coherent paper/surface/line treatment rather than unrelated application panels;
- transcription display/edit typography matches the reader style where compatible with Quill editing;
- selected marquee remains visually clear and is the only marquee shown when that is the current intended behaviour;
- edit controls remain distinctly UI-like using sans-serif typography;
- locking, save/edit state and navigation remain obvious;
- pane resizing/layout behaviour remains stable;
- pan/zoom or image interaction behaviour is not moved to the server.

## Scope

### Diaries Client

Primary components include:

```text
src/app/fragment/fragment.component.*
src/app/fragment/image-viewer/image-viewer.component.*
src/app/fragment/text-panel/text-panel.component.*
src/app/headers/pageheader/*
src/app/headers/pagefooter/*
```

Also inspect nested marquee/image canvas components and Quill editor styles used by `text-panel`.

### Layout

Keep the two-column desktop layout. Use `diaries-web .source-layout` as a visual reference but do not blindly apply `position: sticky` if it conflicts with the editor's internal image pan/zoom/canvas mechanics.

Use clear but light pane separation. Avoid Material elevation/shadows unless they convey active editor state.

The layout should support a future narrow-screen stacked mode, but the full responsive pass belongs to 0021.

### Image Viewer

Restyle the image background/border to resemble the source-image treatment in `diaries-web` (`#e9e4da`-like neutral backing, thin line). Preserve client-side image interaction.

Do not implement pan/zoom on the responder. Pan/zoom, marquee transform and direct manipulation belong in the Angular/browser side because they are view interactions. Server/responder responsibility remains source file delivery and persistence of actual marquee data when edits are committed.

Selected marquee styling should harmonise with the brown accent/focus colours while remaining clearly visible on varied page images.

### Text Panel

Use reader typography for transcription content in read mode. In edit mode, retain Quill usability and selection/caret clarity. Controls and editor toolbars remain sans-serif.

Do not sacrifice editing ergonomics merely to imitate static HTML. Ensure long lines continue to wrap correctly in both read and edit states.

### Locking and State

Visual states should clearly distinguish, where the current application exposes them:

- unlocked/read-only;
- locked by current user/editable;
- locked/unavailable;
- save/update in progress;
- error state.

Do not change the lock RPC contract.

### Diaries Responder / MQTT / Database

No intended change. Regression validation must still include lock acquisition/release and marquee/text update flows because markup/component-lifecycle changes can accidentally affect them.

## Detailed Implementation Steps

- [ ] Complete stages 0016-0019.
- [ ] Capture screenshots and interaction notes for current fragment editing, including marquee, lock and navigation states.
- [ ] Restyle the overall fragment workspace using shared paper/surface/line tokens.
- [ ] Restyle image viewer border/background without changing coordinate calculations.
- [ ] Verify CSS transforms, canvas/SVG sizing and pointer coordinate calculations are unaffected by padding/border changes; use wrapper elements if needed so geometry stays stable.
- [ ] Keep only the selected marquee visible according to the existing intended behaviour.
- [ ] Restyle selected marquee using a high-visibility accent that remains compatible with hover/focus/edit handles.
- [ ] Restyle text panel read mode with reader typography.
- [ ] Restyle Quill edit mode carefully so caret, selection, toolbar and formatting remain usable.
- [ ] Keep editor controls and metadata in system sans-serif.
- [ ] Harmonise lock/status indicators with the shared design system.
- [ ] Restyle empty/no-image/error/loading states.
- [ ] Verify pageheader and pagefooter from 0017 still fit naturally around the editor.
- [ ] Run lock, edit, save, marquee create/edit/delete, file-dialog and navigation workflows.
- [ ] Run production build and focused unit tests.

## Geometry Safety Requirement

CSS changes around the image viewer are potentially more than cosmetic if pointer coordinates are calculated relative to an element's bounding box. Any new padding, border, transform or wrapper must be tested against marquee creation and edit handles. Prefer applying decorative styling to an outer wrapper while leaving the coordinate-bearing element's geometry unchanged.

## Non-Goals

- No responder-side pan/zoom implementation.
- No new image format or image-serving endpoint.
- No lock protocol redesign.
- No marquee persistence redesign.
- No Quill storage-format migration.

## Acceptance Criteria

- [ ] Fragment editor clearly belongs to the same visual family as `diaries-web` and the restyled Angular reader.
- [ ] Image/text split remains functional.
- [ ] Pan/zoom/image interactions remain client-side and behave as before.
- [ ] Marquee geometry remains accurate after styling changes.
- [ ] Only the selected marquee is visible where that is the intended application behaviour.
- [ ] Text read/edit modes remain readable and usable.
- [ ] Long-line wrapping remains fixed.
- [ ] Lock acquisition, lock release and edit state remain correct.
- [ ] Text save/update works.
- [ ] Marquee create/edit/delete works.
- [ ] Back/up/forward navigation works.
- [ ] Relevant tests and production build pass.

## Validation

Perform an end-to-end editor session:

1. open a fragment;
2. confirm selected marquee display;
3. pan/zoom or otherwise manipulate the image using existing controls;
4. acquire any required lock;
5. edit transcription and save;
6. edit a marquee and save;
7. release/navigate away;
8. return/refresh and confirm persisted and retained state;
9. inspect browser console and responder log for RPC errors or duplicate actions.

Repeat at a second browser size to catch coordinate/layout issues.

## Dependencies

- 0016 through 0019.

## Deployment and Rollback Notes

No schema migration. Because image geometry and editing workflows are sensitive, deployment should use the normal client smoke test and retain the prior client image for rapid rollback.

## Completion Summary

To be completed when implemented.

## Completed Date

To be completed.
