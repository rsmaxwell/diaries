# 0017-FEAT - Restyle diaries-client application shell and common controls

## Type

Feature

## Status

To do

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

- [ ] Complete 0016 first and consume its shared design tokens.
- [ ] Inventory all shared header/footer variants and identify which routes use each one.
- [ ] Restyle `fullheader` to use the reader surface, line and typography vocabulary.
- [ ] Restyle `fullfooter` as a light separator/footer rather than a visually heavy application bar.
- [ ] Restyle plain header/footer variants consistently.
- [ ] Restyle `pageheader` editing actions without removing, renaming or reordering behaviour unless there is a strong usability reason documented here.
- [ ] Restyle `pagefooter` navigation so previous/up/next controls fit the reader design.
- [ ] Ensure icon-only buttons retain accessible labels/tooltips.
- [ ] Give hover, active, focus-visible and disabled states distinct treatments.
- [ ] Restyle alerts/notices to use a restrained accent-left-rule treatment similar to `diaries-web .notice` where suitable.
- [ ] Restyle file-list dialog and version/build information to use surface/line/muted tokens.
- [ ] Check Angular CDK overlay surfaces because dialog styling is rendered outside normal component hierarchy.
- [ ] Check narrow widths so header actions wrap or condense rather than overlap.
- [ ] Run component tests and production build.

## Non-Goals

- No redesign of diaries/page/day content layouts yet.
- No route changes.
- No changes to edit action behaviour.
- No changes to MQTT RPC or retained state.
- No new server-side styling or responder endpoints.

## Acceptance Criteria

- [ ] All shared header/footer variants visibly belong to the same design system as `diaries-web`.
- [ ] Editing actions remain functionally identical.
- [ ] Back/up/forward navigation remains functionally identical.
- [ ] Alerts and dialogs remain readable and accessible.
- [ ] Keyboard users can see focus on every actionable control.
- [ ] Controls remain usable at typical desktop widths and a narrow mobile/tablet width.
- [ ] Existing relevant component tests pass.
- [ ] Production Angular build passes.

## Validation

Manually traverse sign-in, diaries list, diary page, day view and fragment editor. Exercise every common header/footer action including disabled navigation states. Open at least one file-list or confirmation-style dialog and verify focus and text contrast.

## Dependencies

- Requires **0016-FEAT - establish diaries-client reader-style design foundation**.

## Deployment and Rollback Notes

Client-only presentation change. No database or MQTT migration. Roll back by deploying the prior client build.

## Completion Summary

To be completed when implemented.

## Completed Date

To be completed.
