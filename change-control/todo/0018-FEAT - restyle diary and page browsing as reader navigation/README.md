# 0018-FEAT - Restyle diary and page browsing as reader navigation

## Type

Feature

## Status

To do

## Priority

Medium

## Opened

2026-09-04

## Stage

3 of 6

## Summary

Redesign the `diaries-client` diary-list and diary-page browsing views so they look like reader navigation rather than generic Material data tables, while preserving selection, ordering and drag-and-drop capabilities.

## Background

The current `diaries.component.html` renders an outlined Material card containing a `mat-table` with `id`, `sequence` and `name` columns. `diary.component.html` follows a similar pattern for pages. Both use elevation and compact tabular presentation.

`diaries-web` instead presents diary navigation with generous whitespace, thin separators or card links, warm surfaces, serif reader titles and small sans-serif metadata. These browsing screens are therefore the best low-risk place to move the Angular client from "administrative table" toward "diary reader".

The Angular client still needs capabilities that the web reader does not, particularly drag-and-drop ordering. The visual redesign must preserve those behaviours.

## Expected Behaviour

After this stage:

- the diaries list is visually comparable to `diaries-web` card/link navigation;
- diary/page names are the primary visual information;
- IDs and sequence values, if still shown, are secondary metadata rather than dominant columns;
- diary heading treatment resembles the web reader's page heading style;
- clickable rows/cards have clear hover and keyboard focus states;
- drag-and-drop ordering remains available and understandable;
- the layout works well without horizontal table scrolling.

## Scope

### Diaries Client

Primary components:

```text
src/app/diaries/diaries.component.html
src/app/diaries/diaries.component.scss
src/app/diaries/diaries.component.ts
src/app/diary/diary.component.html
src/app/diary/diary.component.scss
src/app/diary/diary.component.ts
```

Consider whether retaining `mat-table` is still beneficial. Two acceptable implementation approaches are:

1. retain `mat-table` and make it visually list/card-like; or
2. replace table markup with semantic lists/cards using Angular CDK drag/drop directly.

Prefer the second only if it simplifies the markup without disrupting existing sorting/reordering or tests. Do not rewrite working TypeScript simply to avoid Material.

The current diary title area uses a grey inset box and Roboto. Replace this with open reader-style heading treatment, using serif typography for the diary name and muted/system typography for identifiers or auxiliary information.

Use a maximum readable width where appropriate rather than allowing content to span an arbitrarily wide monitor.

### Drag and Drop

The entire clickable item should not become an ambiguous drag target. Preserve or improve the user's ability to distinguish:

- clicking/selecting an item;
- dragging an item to reorder it;
- keyboard focus on the item.

If a visible drag handle is added, it should be subtle and accessible. Any change from whole-row drag to handle-only drag must be verified against existing usage and tests.

### Diaries Responder / MQTT / Database

No contract or persistence change expected. Resequencing requests must remain exactly as currently implemented.

## Detailed Implementation Steps

- [ ] Complete 0016 and 0017 first.
- [ ] Capture screenshots of the current diaries and diary-page views for comparison.
- [ ] Inspect the `diaries-web` `.card-list`, `.card-link`, `.link-list`, `.page-shell`, `.page-heading`, `.eyebrow` and breadcrumb conventions.
- [ ] Decide whether each Angular view should use a card grid or a restrained list based on information density and ordering needs.
- [ ] Make diary/page names the primary content.
- [ ] Move `id` and `sequence` into secondary metadata or visually muted fields if users still need them.
- [ ] Remove Material elevation where it does not communicate state.
- [ ] Replace inset/grey title boxes with open reader heading layout.
- [ ] Preserve click navigation to the same routes.
- [ ] Preserve `cdkDropList`/`cdkDrag` behaviour and request generation.
- [ ] Add visual feedback for drag preview, placeholder and active drop location that uses the reader palette.
- [ ] Ensure long diary/page names wrap naturally rather than ellipsising unnecessarily.
- [ ] Ensure the list remains usable with many diaries/pages and existing scrolling behaviour.
- [ ] Update unit tests only where DOM structure changed; do not weaken behavioural assertions.
- [ ] Run production build.

## Non-Goals

- Do not redesign the day transcription in this stage.
- Do not redesign the fragment image/text editor.
- Do not alter reorder semantics or responder locking.
- Do not add new diary/page data fields.

## Acceptance Criteria

- [ ] Diaries and pages no longer look primarily like generic Material data tables.
- [ ] Visual language matches `diaries-web` paper/surface/line/accent conventions.
- [ ] Diary/page names are prominent and readable.
- [ ] Long names wrap without clipping important text.
- [ ] Selection/navigation by click still works.
- [ ] Drag-and-drop resequencing still works exactly as before.
- [ ] Reordering does not accidentally trigger navigation.
- [ ] Keyboard focus is visible.
- [ ] Relevant tests and production build pass.

## Validation

Use a diary set containing short and long names. Reorder at least two items and verify both the immediate client order and the retained/server-backed order after refresh/reconnect. Because this is a visual change around an existing mutation path, also check browser console and responder logs for unexpected duplicate reorder requests.

## Dependencies

- 0016 reader-style design foundation.
- 0017 common application shell and controls.

## Deployment and Rollback Notes

No persistence migration. Because this stage touches drag-and-drop markup, rollback is the previous client build if navigation or reorder regression is observed.

## Completion Summary

To be completed when implemented.

## Completed Date

To be completed.
