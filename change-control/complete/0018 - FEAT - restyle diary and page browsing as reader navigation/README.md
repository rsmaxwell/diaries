# 0018-FEAT - Restyle diary and page browsing as reader navigation

## Type

Feature

## Status

In progress

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

- [x] Complete 0016 and 0017 first.
- [ ] Capture screenshots of the current diaries and diary-page views for comparison.
- [x] Inspect the `diaries-web` `.card-list`, `.card-link`, `.link-list`, `.page-shell`, `.page-heading`, `.eyebrow` and breadcrumb conventions.
- [x] Decide whether each Angular view should use a card grid or a restrained list based on information density and ordering needs.
- [x] Make diary/page names the primary content.
- [x] Move `id` and `sequence` into secondary metadata or visually muted fields if users still need them.
- [x] Remove Material elevation where it does not communicate state.
- [x] Replace inset/grey title boxes with open reader heading layout.
- [x] Preserve click navigation to the same routes.
- [x] Preserve `cdkDropList`/`cdkDrag` behaviour and request generation.
- [x] Add visual feedback for drag preview, placeholder and active drop location that uses the reader palette.
- [x] Ensure long diary/page names wrap naturally rather than ellipsising unnecessarily.
- [x] Ensure the list remains usable with many diaries/pages and existing scrolling behaviour.
- [x] Update unit tests only where DOM structure changed; do not weaken behavioural assertions.
- [x] Run production build.

## Non-Goals

- Do not redesign the day transcription in this stage.
- Do not redesign the fragment image/text editor.
- Do not alter reorder semantics or responder locking.
- Do not add new diary/page data fields.

## Acceptance Criteria

- [x] Diaries and pages no longer look primarily like generic Material data tables.
- [x] Visual language matches `diaries-web` paper/surface/line/accent conventions.
- [x] Diary/page names are prominent and readable.
- [x] Long names wrap without clipping important text.
- [x] Selection/navigation by click still works.
- [x] Drag-and-drop resequencing retains the existing update and normalise request flow.
- [x] Reordering does not accidentally trigger navigation.
- [x] Keyboard focus has the shared high-contrast focus-visible treatment.
- [x] Relevant tests and production build pass.

## Validation

### Automated Tests and Build

Focused component tests passed all 6 tests:

```text
node node_modules/@angular/cli/bin/ng.js test --watch=false \
  --include="src/app/diaries/diaries.component.spec.ts" \
  --include="src/app/diary/diary.component.spec.ts"
```

These tests cover semantic reader-list rendering, long-name wrapping, accessible drag handles, unchanged click routes, top-to-bottom resequencing, the existing update/normalise RPC sequence and the absence of navigation during reorder handling.

The production build passed:

```text
node node_modules/@angular/cli/bin/ng.js build --configuration production
```

The initial sandboxed build could not reach Google Fonts for Angular's font-inlining step; the same build passed with normal network access. Existing `quill-delta` and `buffer` CommonJS warnings remain.

The complete Karma suite compiled and ran 34 tests: 27 passed and 7 failed. All seven failures are the previously documented TestBed setup defects in unrelated specs, caused by missing `HttpClient` or `ActivatedRoute` providers.

### Manual Verification

The development route at `http://127.0.0.1:4200/diaries` correctly enforced authentication and redirected the available browser session to sign-in. Because no authenticated responder-backed session was available, before/after screenshots and live drag persistence could not be verified safely.

Still verify with a running responder and representative data:

1. short and long diary and page names at desktop and narrow widths;
2. click navigation to the existing diary and page routes;
3. drag at least two items using their handles;
4. the immediate order and retained/server-backed order after refresh or reconnect;
5. browser console and responder logs for duplicate reorder requests.

## Dependencies

- 0016 reader-style design foundation.
- 0017 common application shell and controls.

## Deployment and Rollback Notes

No persistence migration. Because this stage touches drag-and-drop markup, rollback is the previous client build if navigation or reorder regression is observed.

## Completion Summary

The source implementation is complete. Both Material tables were replaced with semantic ordered reader lists built directly on Angular CDK drag/drop. Diary and page names are now the primary serif content, while IDs and sequence positions are secondary metadata. Each item separates its full-width navigation control from a labelled drag handle, preventing a reorder gesture from invoking navigation. Shared reader-navigation styles provide constrained width, open page headings, warm surfaces, thin borders, long-name wrapping, visible focus, responsive sizing, drag previews and drop placeholders.

The focused tests and production build pass. The change remains in progress pending authenticated before/after screenshots and end-to-end verification that server-backed order survives refresh/reconnect.

## Completed Date

Not complete.
