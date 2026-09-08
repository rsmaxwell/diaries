# 0017-FEAT - Restyle diaries-client application shell and common controls

## Type

Feature

## Status

In progress

## Priority

Medium

## Opened

2026-09-04

## Stage

2 of 6

## Summary

Apply the reader-style design foundation to the common Angular application shell: full headers/footers, plain headers/footers, page headers/footers, navigation controls, alerts and shared dialogs. The objective is to remove the strongest visual mismatch between `diaries-client` and `diaries-web` before changing diary content screens.

## Background

The existing client uses reusable components beneath `src/app/headers/`, including `fullheader`, `fullfooter`, `pageheader`, `pagefooter`, `plainheader` and `plainfooter`. These components frame most of the application. Because they are shared, changing them early gives a large visual improvement with limited functional risk.

`diaries-web` uses an understated header/footer with thin separators, warm surfaces, modest navigation, strong focus states and small sans-serif metadata. The Angular client should adopt the same visual language while preserving the richer controls required for editing.

## Expected Behaviour

After this stage:

- top-level client pages have a warm, restrained shell consistent with `diaries-web`;
- headers no longer dominate the page like a generic Material application toolbar;
- diary/application titles are visually distinct from buttons and metadata;
- editing controls remain easy to discover and operate;
- footer/navigation controls are visually quieter but still have clear hover, focus and disabled states;
- common dialogs and alerts fit the same palette.

## Scope

### Diaries Client

Inspect and update as appropriate:

```text
src/app/headers/fullheader/*
src/app/headers/fullfooter/*
src/app/headers/plainheader/*
src/app/headers/plainfooter/*
src/app/headers/pageheader/*
src/app/headers/pagefooter/*
src/app/alert/*
src/app/alerts/*
src/app/alertbuttons/*
src/app/files-list-dialog/*
src/app/build-info/version-info.component.*
```

Use tokens introduced by 0016 rather than literal colours.

For common headers, aim for the design characteristics of `.site-header`, `.site-header__inner` and `.site-title` from `diaries-web`:

- thin bottom border;
- surface background rather than strong filled toolbar colour;
- constrained or sensibly padded content width;
- title typography with serif emphasis where appropriate;
- UI controls in system sans-serif;
- no unnecessary box shadow/elevation.

For page editing headers, preserve the current actions such as add/delete/list files/create marquee/edit marquee/delete marquee. The styling may become more compact and reader-like, but the action availability and event outputs must not change.

For page footers, preserve back/up/forward semantics and disabled states. Consider styling them similarly to `diaries-web` adjacent navigation while retaining icon/button affordances required by the editor.

### Diaries Responder

No change expected.

### MQTT Contract and Retained State

No change expected.

### Database

No change expected.

### Images and Static Files

No change expected.

### Build, Configuration, and Deployment

No new runtime configuration expected.

## Detailed Implementation Steps

- [x] Complete 0016 first and consume its shared design tokens.
- [x] Inventory all shared header/footer variants and identify which routes use each one.
- [x] Restyle `fullheader` to use the reader surface, line and typography vocabulary.
- [x] Restyle `fullfooter` as a light separator/footer rather than a visually heavy application bar.
- [x] Restyle plain header/footer variants consistently.
- [x] Restyle `pageheader` editing actions without removing, renaming or reordering behaviour unless there is a strong usability reason documented here.
- [x] Restyle `pagefooter` navigation so previous/up/next controls fit the reader design.
- [x] Ensure icon-only buttons retain accessible labels/tooltips.
- [x] Give hover, active, focus-visible and disabled states distinct treatments.
- [x] Restyle alerts/notices to use a restrained accent-left-rule treatment similar to `diaries-web .notice` where suitable.
- [x] Restyle file-list dialog and version/build information to use surface/line/muted tokens.
- [x] Check Angular CDK overlay surfaces because dialog styling is rendered outside normal component hierarchy.
- [x] Check narrow widths so header actions wrap or condense rather than overlap.
- [x] Run component tests and production build.

## Non-Goals

- No redesign of diaries/page/day content layouts yet.
- No route changes.
- No changes to edit action behaviour.
- No changes to MQTT RPC or retained state.
- No new server-side styling or responder endpoints.

## Acceptance Criteria

- [x] All shared header/footer variants visibly belong to the same design system as `diaries-web`.
- [x] Editing actions remain functionally identical.
- [x] Back/up/forward navigation remains functionally identical.
- [x] Alerts and dialogs remain readable and accessible at source and component-test level.
- [x] Actionable controls have an explicit, high-contrast `:focus-visible` treatment.
- [x] Controls remain usable at typical desktop widths and a narrow mobile/tablet width.
- [x] Existing relevant component tests pass.
- [x] Production Angular build passes.

## Validation

### Automated Tests and Build

The focused shell and alert test run passed all 18 tests:

```text
node node_modules/@angular/cli/bin/ng.js test --watch=false \
  --include="src/app/headers/**/*.spec.ts" \
  --include="src/app/alerts/*.spec.ts" \
  --include="src/app/alert/*.spec.ts" \
  --include="src/app/alertbuttons/*.spec.ts"
```

The production build passed using the repository-installed Angular CLI:

```text
node scripts/generate-build-info.js
node node_modules/@angular/cli/bin/ng.js build --configuration production
```

The host `npm` wrapper was unavailable because its referenced global `npm-cli.js` was missing. The build retained the existing `quill-delta` and `buffer` CommonJS warnings.

The complete Karma suite compiled and ran 30 tests: 21 passed and 9 failed. The remaining failures are pre-existing TestBed setup defects in unrelated component smoke tests, where `HttpClient` and/or `ActivatedRoute` providers are missing.

### Browser Verification

The development client was smoke-tested at `http://127.0.0.1:4200/` at 1280 by 720 and 390 by 800 viewports. The sign-in shell used the expected paper, surface, ink, separator and serif-title styles; the shared header and footer had no horizontal overflow; and the browser console reported no warnings or errors.

Authenticated diaries/page/day/editor screens and an opened file-list dialog still require manual verification with a running responder and valid diary data. The existing sign-in form itself remains wider than the 390-pixel viewport; that content-screen issue is outside this shell-stage scope.

## Dependencies

- Requires **0016-FEAT - establish diaries-client reader-style design foundation**.

## Deployment and Rollback Notes

Client-only presentation change. No database or MQTT migration. Roll back by deploying the prior client build.

## Completion Summary

The source implementation is complete. A shared shell stylesheet now applies the 0016 design tokens consistently to every full, plain and page header/footer variant. Existing editing action outputs and page-navigation outputs are preserved, while controls now have consistent accessible names and hover, active, focus-visible and disabled states. Alerts use typed reader-style notices, build information uses metadata typography, and the file-list dialog uses the shared surface, line and responsive sizing rules, including its CDK overlay container.

Focused tests and the production build pass. The change remains in progress pending repair of the pre-existing full-suite TestBed provider failures and manual authenticated screen/dialog verification.

## Completed Date

Not complete.
