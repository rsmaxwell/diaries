# 0019-FEAT - Redesign day view as a diary reader

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-09-04

## Stage

4 of 6

## Summary

Redesign `dayview` so a day's transcription reads like a document in `diaries-web`, while retaining fragment navigation and same-date drag-and-drop resequencing.

This is the stage where the visual similarity between `diaries-client` and `diaries-web` should become most obvious.

## Background

The current day view renders fragments inside a Material card and `mat-table`, with ID, sequence and text columns. Quill HTML is displayed read-only inside table cells. Recent changes added safer wrapping for long lines and embedded content.

`diaries-web` renders a day as a centred readable column with a date heading and fragments separated by thin rules. Selected fragments use a restrained accent rule rather than a heavy selection background. This is better suited to diary transcription than a data table.

The client-specific complication is that day-view fragments are also reorderable and are navigation targets into the fragment editor. That behaviour must remain intact.

## Expected Behaviour

After this stage:

- the formatted day/date is presented as a reader heading, not a small bordered badge;
- transcription is centred in a readable column (approximately the same visual width as `diaries-web .diary-day`);
- each fragment reads as a passage separated by a thin line/surface treatment;
- fragment ID/sequence are secondary metadata or omitted from the main reading flow if not needed;
- long lines, URLs and embedded images remain contained;
- clicking a fragment still opens/navigates to that fragment;
- drag-and-drop resequencing remains available;
- the view remains clear during `reorderInFlight` and invalid-date states.

## Scope

### Diaries Client

Primary files:

```text
src/app/dayview/dayview.component.html
src/app/dayview/dayview.component.scss
src/app/dayview/dayview.component.ts
src/app/dayview/dayview.component.spec.ts
```

Strongly consider replacing the Material table markup with semantic fragment article/list markup because the content is document-oriented rather than columnar. Angular CDK drag/drop can operate on non-table elements. However, make this change only if the existing reorder implementation can be preserved cleanly.

A target structure could conceptually resemble:

```text
day reader
  date heading
  fragment
    optional metadata / drag affordance
    Quill viewer content
  fragment
  fragment
```

Do not copy `diaries-web` HTML mechanically. Use Angular semantics and existing component state.

### Typography and Content

Use serif typography and approximately `1.6` line height for actual diary transcription, but preserve Quill formatting such as emphasis, lists and paragraph breaks. Keep controls/metadata in system sans-serif.

Preserve the existing long-line rules. The key requirement is that normal prose should break at sensible spaces/hyphens, while pathological unbroken strings or URLs must not force horizontal overflow. Images should remain `max-width: 100%`.

### Selection and Navigation

If day view exposes the currently selected fragment, use an accent-left-rule or similarly restrained treatment inspired by `diaries-web .fragment.is-selected`. Do not use a selection colour that makes transcription difficult to read.

The whole fragment can remain clickable if this does not conflict with drag operation. Cursor treatment should make the interaction understandable.

### Resequencing Safety

This stage must not undo the recent protections around `reorderInFlight`, locking or same-date normalisation. Verify that presentation changes do not create duplicate click/drop events.

### Diaries Responder / MQTT / Database

No intentional change. Because resequencing is involved, validation should still inspect browser and responder logs to confirm the existing mutation contract is unchanged.

## Detailed Implementation Steps

- [x] Complete stages 0016-0018.
- [x] Record current day-view behaviour for click navigation and drag/drop before changing markup.
- [x] Replace or visually neutralise the Material table structure so transcription becomes a document flow.
- [x] Create a constrained readable column with responsive side margins.
- [x] Restyle the date as the day's primary heading.
- [x] Style fragments using surface, line and accent tokens.
- [x] Decide how ID and sequence metadata should be exposed without distracting from reading; preserve information if it is operationally useful.
- [x] Retain the Quill viewer wrapper required for existing Quill HTML styles.
- [x] Preserve safe HTML handling via the existing pipe.
- [x] Preserve long-line wrapping and embedded-image containment.
- [x] Preserve `cdkDropListDisabled="reorderInFlight"` or equivalent protection.
- [x] Provide clear drag placeholder/active feedback without turning the reader into a table UI.
- [x] Make invalid date state accessible using more than colour alone; do not rely only on a red background.
- [x] Verify empty/no-date-selected state fits the new design.
- [x] Update focused tests for rendered fragment content, navigation and drop behaviour.
- [x] Run production build.

## Non-Goals

- Do not change how fragment text is stored.
- Do not modify Quill document content to achieve the visual style.
- Do not change reorder RPC payloads or locking semantics.
- Do not redesign the full fragment editor yet.

## Acceptance Criteria

- [x] Day view visually reads like `diaries-web` rather than a data table.
- [x] Date is prominent and correctly formatted.
- [x] Fragment text uses readable reader typography and spacing.
- [x] Normal prose wraps at natural boundaries.
- [x] Very long unbroken strings/URLs cannot overflow the reader column.
- [x] Embedded images remain within the content width.
- [x] Clicking a fragment still navigates to the same fragment editor route/state.
- [x] Drag-and-drop resequencing retains its existing locking and update behavior.
- [x] Reorder-in-flight protection remains effective.
- [x] Invalid date state is understandable without relying solely on colour.
- [x] Relevant focused tests and the production build pass.

## Validation

### Automated Tests and Build

Focused component tests passed all 8 tests:

```text
node node_modules/@angular/cli/bin/ng.js test --watch=false \
  --include="src/app/dayview/dayview.component.spec.ts"
```

The tests cover formatted and invalid dates, the no-date state, Quill paragraphs/lists/inline formatting, long URLs, embedded-image containment, fragment navigation, accessible drag handles, top-to-bottom resequencing, lock refusal, update rollback/unlock and duplicate-drop protection while a reorder is in flight.

The production build passed:

```text
node node_modules/@angular/cli/bin/ng.js build --configuration production
```

The build retains the existing `quill-delta` and `buffer` CommonJS warnings. The complete Karma suite compiled and ran 39 tests: 32 passed and 7 failed. All seven failures are the previously documented TestBed setup defects in unrelated specs, caused by missing `HttpClient` or `ActivatedRoute` providers.

### Browser and Integration Verification

A clean development build was served at `http://127.0.0.1:4201/`. Opening a fragment route correctly enforced authentication and redirected the available browser session to sign-in without a build-error overlay. The day reader itself could not be reached because no authenticated responder-backed session was available.

Still verify with a running responder and representative diary data:

1. multiple fragments on the same date at desktop and narrow widths;
2. first-to-last and last-to-first drag operations;
3. click navigation after a reorder;
4. canonical order after refresh or reconnect;
5. browser console, responder log and retained topic tree for duplicate or unexpected reorder activity.

## Dependencies

- 0016 design foundation.
- 0017 shell/common controls.
- 0018 diary/page browsing.

## Deployment and Rollback Notes

Client-only intended. No data migration. Because the view contains a mutation interaction, do not mark complete until reorder has been tested against the responder and persisted/retained result.

## Completion Summary

The source implementation is complete. The Material card/table was replaced with a semantic diary-day section and ordered fragment articles in a responsive 48rem reading column. The formatted date is now the primary serif heading, transcription uses reader typography at 1.6 line height, and fragment IDs and positions remain available as quiet metadata. Dynamically inserted Quill content keeps its existing safe-HTML path while deep-scoped containment rules handle long strings, preformatted content and embedded images.

Navigation and reordering are separate controls: each fragment article remains keyboard-focusable and navigates through the existing marquee/page lookup, while a labelled drag handle drives the unchanged lock/update flow. Reorder-in-flight state disables the drop list and handles and announces that the order is being saved. Invalid dates now include an explicit alert message and icon in addition to visual decoration.

Focused tests and the production build pass. The change remains in progress until drag persistence, retained-state convergence and the authenticated visual layout are verified against a running responder.

## Completed Date

Not complete.
