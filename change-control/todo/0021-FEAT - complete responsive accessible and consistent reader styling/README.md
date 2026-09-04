# 0021-FEAT - Complete responsive, accessible and consistent reader styling

## Type

Feature

## Status

To do

## Priority

Medium

## Opened

2026-09-04

## Stage

6 of 6

## Summary

Complete the reader-style programme with a cross-application consistency, responsive-layout and accessibility pass. Remove temporary styling compromises introduced during staged migration, ensure all significant client screens work across practical viewport sizes, and document the resulting visual system.

## Background

Stages 0016-0020 intentionally change the client incrementally. By the end of stage 5, individual screens should already be substantially improved, but small inconsistencies are likely: spacing, button treatment, metadata font sizes, focus rings, breakpoints, empty states, dialog surfaces and duplicate CSS.

`diaries-web` already includes responsive behaviour at approximately 44rem, strong focus-visible treatment and reduced-motion handling. The Angular client should reach comparable quality while accounting for its richer editor UI.

## Expected Behaviour

After this stage:

- all major `diaries-client` screens use one coherent visual vocabulary;
- common spacing, typography and colours are centralised rather than duplicated;
- reader screens adapt cleanly to narrow widths;
- the fragment editor has a usable narrow-screen fallback, normally stacked image/text panes or another documented strategy;
- keyboard focus is visible throughout;
- controls have sufficient visual distinction in hover/focus/disabled states;
- reduced-motion preference is respected where transitions/animations exist;
- there are no obvious regressions in Material dialogs/overlays;
- visual similarity with `diaries-web` is intentional and documented.

## Scope

### Cross-Screen Audit

Review at least:

- sign-in/authentication screens;
- diaries list;
- diary/page navigation;
- day view;
- fragment editor;
- files dialog;
- alerts/errors;
- build/version display;
- empty/loading states.

### Responsive Behaviour

Establish documented breakpoints based on content needs rather than device names. `diaries-web` uses `44rem` as a reference point; the Angular editor may need an additional breakpoint because its two-pane workflow is more complex.

For narrow screens:

- avoid horizontal page scrolling;
- allow headers/actions to wrap or compact gracefully;
- stack diary-web-like two-column content where necessary;
- define how image and transcription editor panes stack or switch;
- ensure touch targets are practical;
- preserve access to all editing controls.

### Accessibility

Verify:

- visible keyboard focus;
- semantic heading order;
- buttons versus links are used appropriately;
- icon buttons have labels/tooltips;
- colour is not the sole carrier of error/selection/lock state;
- text contrast is reasonable against paper/surface colours;
- drag-and-drop has at least an understandable non-colour affordance; preserve any existing keyboard support and document limitations;
- reduced-motion preference is honoured for non-essential transitions.

### CSS/SCSS Consolidation

Remove temporary duplicates and literal values introduced during migration. Prefer shared tokens/mixins where they genuinely reduce drift, but do not create an over-engineered styling framework.

Do not use widespread `::ng-deep` overrides unless no supported alternative exists. Existing necessary Quill-specific overrides should be documented.

## Detailed Implementation Steps

- [ ] Complete 0016-0020 first.
- [ ] Perform a page-by-page visual audit against `diaries-web` and the shared token definitions.
- [ ] Record inconsistencies before changing them so the pass remains bounded.
- [ ] Define final content-width and breakpoint conventions.
- [ ] Make reader list/day layouts responsive.
- [ ] Define and implement the fragment editor narrow-screen behaviour.
- [ ] Verify Quill toolbar/content remain usable at the narrow breakpoint.
- [ ] Verify image viewer geometry after any stacking/resizing changes.
- [ ] Audit all focus-visible states using keyboard-only navigation.
- [ ] Audit hover, active, disabled, selected, error and lock states.
- [ ] Ensure invalid/error states use text/icon/border semantics in addition to colour.
- [ ] Add `prefers-reduced-motion` handling where the client uses non-essential transitions.
- [ ] Remove duplicated palette literals and obsolete Material-style overrides superseded by the new system.
- [ ] Review component SCSS for accidental fixed heights that cause clipping at larger text sizes.
- [ ] Test browser zoom at 200% on core reader/navigation flows.
- [ ] Run all relevant tests and production build.
- [ ] Perform full application smoke test against a real responder/broker/database environment.
- [ ] Update client README/design notes to describe the visual relationship with `diaries-web`.

## Non-Goals

- Pixel-perfect identity between the two applications.
- Removal of controls unique to the Angular editor.
- Replacement of Angular Material solely for stylistic purity.
- Server-side rendering of Angular views.
- Any MQTT/database protocol redesign.

## Acceptance Criteria

- [ ] Major screens look intentionally related to `diaries-web`.
- [ ] Reader content consistently uses the defined serif typography; controls/metadata consistently use UI typography.
- [ ] Shared palette tokens are used instead of scattered literal colours.
- [ ] Desktop layouts remain strong at wide widths without excessively long reading lines.
- [ ] Narrow layouts avoid horizontal page overflow.
- [ ] Fragment editor remains usable at the agreed narrow breakpoint.
- [ ] Keyboard focus is visible throughout the core workflow.
- [ ] Selection/error/lock state is not conveyed by colour alone.
- [ ] 200% browser zoom remains usable for core navigation and reading.
- [ ] Reduced-motion preference is respected where applicable.
- [ ] All existing behavioural tests pass or are legitimately updated for DOM-only changes.
- [ ] Production client build passes.
- [ ] End-to-end smoke testing confirms MQTT/edit/reorder behaviour is unchanged.

## Validation Matrix

Test at minimum these viewport classes:

```text
wide desktop       ~1440 px or greater
normal desktop     ~1024-1280 px
narrow/tablet      ~768 px
phone-like narrow  ~390-430 px where practical
```

For the fragment editor, if phone-like use is judged impractical, the UI must still fail gracefully and the supported minimum width should be documented rather than leaving controls inaccessible.

Perform keyboard-only navigation through sign-in, diary selection, day selection, fragment selection and available editor controls. Repeat core navigation at 200% zoom.

## Dependencies

- Requires completion of stages 0016-0020.

## Deployment and Rollback Notes

Client-only intended. No database or retained-state migration. Rollback is the previous stable client image. Final deployment should be accompanied by before/after screenshots and normal client smoke-test evidence.

## Completion Summary

To be completed when implemented. The final summary should explicitly state any intentional visual differences that remain between `diaries-client` and `diaries-web` because of editing requirements.

## Completed Date

To be completed.
