# 0019-FEAT - Redesign day view as a diary reader

## Type

Feature

## Status

To do

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

- [ ] Complete stages 0016-0018.
- [ ] Record current day-view behaviour for click navigation and drag/drop before changing markup.
- [ ] Replace or visually neutralise the Material table structure so transcription becomes a document flow.
- [ ] Create a constrained readable column with responsive side margins.
- [ ] Restyle the date as the day's primary heading.
- [ ] Style fragments using surface, line and accent tokens.
- [ ] Decide how ID and sequence metadata should be exposed without distracting from reading; preserve information if it is operationally useful.
- [ ] Retain the Quill viewer wrapper required for existing Quill HTML styles.
- [ ] Preserve safe HTML handling via the existing pipe.
- [ ] Preserve long-line wrapping and embedded-image containment.
- [ ] Preserve `cdkDropListDisabled="reorderInFlight"` or equivalent protection.
- [ ] Provide clear drag placeholder/active feedback without turning the reader into a table UI.
- [ ] Make invalid date state accessible using more than colour alone; do not rely only on a red background.
- [ ] Verify empty/no-date-selected state fits the new design.
- [ ] Update focused tests for rendered fragment content, navigation and drop behaviour.
- [ ] Run production build.

## Non-Goals

- Do not change how fragment text is stored.
- Do not modify Quill document content to achieve the visual style.
- Do not change reorder RPC payloads or locking semantics.
- Do not redesign the full fragment editor yet.

## Acceptance Criteria

- [ ] Day view visually reads like `diaries-web` rather than a data table.
- [ ] Date is prominent and correctly formatted.
- [ ] Fragment text uses readable reader typography and spacing.
- [ ] Normal prose wraps at natural boundaries.
- [ ] Very long unbroken strings/URLs cannot overflow the reader column.
- [ ] Embedded images remain within the content width.
- [ ] Clicking a fragment still navigates to the same fragment editor route/state.
- [ ] Drag-and-drop resequencing still works.
- [ ] Reorder-in-flight protection remains effective.
- [ ] Invalid date state is understandable without relying solely on colour.
- [ ] Client tests/build pass.

## Validation

Test with at least:

- multiple fragments on the same date;
- one fragment containing a very long line/URL;
- paragraphs, lists and inline formatting;
- an embedded image if supported by stored content;
- reorder of first-to-last and last-to-first;
- click after reorder;
- refresh/reconnect to verify order remains correct.

Inspect browser console, responder log and retained topic-tree result around a reorder to ensure no behaviour changed accidentally.

## Dependencies

- 0016 design foundation.
- 0017 shell/common controls.
- 0018 diary/page browsing.

## Deployment and Rollback Notes

Client-only intended. No data migration. Because the view contains a mutation interaction, do not mark complete until reorder has been tested against the responder and persisted/retained result.

## Completion Summary

To be completed when implemented.

## Completed Date

To be completed.
