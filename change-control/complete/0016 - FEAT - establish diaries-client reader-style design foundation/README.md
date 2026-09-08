# 0016-FEAT - Establish diaries-client reader-style design foundation

## Type

Feature

## Status

In progress

## Priority

Medium

## Opened

2026-09-04

## Stage

1 of 6

## Summary

Create the common visual foundation required to make `diaries-client` resemble `diaries-web`. Introduce centrally defined design tokens, typography rules, page/surface colours, border and focus conventions, and an Angular Material theme strategy that can be reused by every later stage.

This stage deliberately avoids redesigning individual diary screens. Its purpose is to stop later work from copying ad-hoc colours, font declarations and spacing values into individual component stylesheets.

## Background

`diaries-web` already has a coherent reader-oriented visual vocabulary in `src/main/resources/static/css/diaries.css`, including values equivalent to:

```text
ink          #28241f
muted        #655e54
paper        #fbf8f1
surface      #fffdf8
line         #d9cfbd
accent       #765326
accent-dark  #4d3417
focus        #165d9c
```

It also deliberately separates typography by purpose:

- Georgia / Times-style serif for diary content and prominent reader headings;
- system sans-serif for metadata, controls, breadcrumbs and small UI labels.

The current Angular client uses a mixture of Material defaults, Roboto, neutral SCSS constants and component-local literal colours. Later reader-style work will be much easier and safer if these concepts are normalised first.

## Expected Behaviour

After this stage:

- the application has one documented source of truth for the reader-style palette and typography;
- global page background and base foreground colours reflect the `diaries-web` visual language;
- common focus-visible treatment is available and clearly visible;
- Material components can inherit or be themed toward the same palette without breaking component behaviour;
- existing screens remain functionally unchanged;
- no component needs to import values from `diaries-web` at runtime.

The client may look only partially transformed at this point. That is expected.

## Scope

### Diaries Client

Primary files to inspect or change include:

- `diaries-client/src/app/theme.scss`;
- `diaries-client/src/styles.scss` and/or the global stylesheet configured by `angular.json`;
- `diaries-client/src/styles/_constants.scss` or equivalent shared SCSS constants;
- Angular Material theme setup in `app.config.ts` or global theme files if applicable.

Introduce semantic tokens rather than component-specific names. Suitable examples are:

```scss
$diaries-ink: #28241f;
$diaries-muted: #655e54;
$diaries-paper: #fbf8f1;
$diaries-surface: #fffdf8;
$diaries-line: #d9cfbd;
$diaries-accent: #765326;
$diaries-accent-dark: #4d3417;
$diaries-focus: #165d9c;
```

CSS custom properties may also be useful where runtime inheritance simplifies component styling. If SCSS variables and CSS custom properties are both used, define a clear relationship rather than maintaining two independent palettes.

Define reusable typography roles such as:

- reader/body serif;
- heading serif;
- UI/control sans-serif;
- metadata sans-serif;
- monospace where request/build identifiers require it.

Do not globally force every Angular Material control to Georgia. Controls should remain UI-like and legible.

### Diaries Responder

No change expected.

### MQTT Contract and Retained State

No change expected. Verify that no presentation refactor accidentally changes component lifecycle or subscriptions.

### Database

No change expected.

### Images and Static Files

No change expected.

### Build, Configuration, and Deployment

No new runtime configuration should be required. The normal client build and existing deployment image should carry the compiled styles.

### Documentation

Document the design tokens and the rule that `diaries-web` is the visual reference but not a runtime dependency. A short comment in the shared style file should explain this intent.

## Detailed Implementation Steps

- [x] Identify the actual global Angular stylesheet entry points from `angular.json`.
- [x] Inspect `src/app/theme.scss`, shared constants and current Material theme configuration.
- [x] Define semantic reader-style palette tokens matching `diaries-web`.
- [x] Define reader serif and UI sans-serif font stacks without introducing downloadable font assets.
- [x] Add base `html`/`body` paper background, ink foreground and box-sizing conventions where safe.
- [x] Add common link and `:focus-visible` treatment compatible with Angular Material components.
- [x] Decide whether Material theming should use an Angular Material theme API or limited CSS overrides; prefer the supported Material theming API where practical.
- [x] Ensure overlays/dialogs continue to receive correct typography and surface colours.
- [x] Remove or deprecate duplicate palette constants only where all references can be safely migrated in this stage; otherwise retain compatibility aliases temporarily.
- [x] Add comments describing which tokens are intended for reader content versus controls.
- [ ] Run existing unit tests and production build.
- [ ] Smoke-test sign-in, diaries list, diary page, day view and fragment editor to ensure the global changes have not made controls unreadable.

## Non-Goals

This stage does not:

- redesign diaries or page tables;
- redesign the day view;
- redesign the fragment editor;
- change navigation behaviour;
- remove Angular Material;
- alter stored Quill content;
- alter responder or MQTT behaviour.

## Acceptance Criteria

- [x] A single coherent reader-style palette is defined centrally.
- [x] Reader and UI typography roles are defined centrally.
- [x] `paper`, `surface`, `ink`, `muted`, `line`, `accent`, `accent-dark` and `focus` concepts are available to later components.
- [x] The application background and base text colours are visually consistent with `diaries-web`.
- [x] Keyboard focus remains clearly visible.
- [x] Material dialogs, buttons, menus and inputs remain readable and usable at the theme/source level.
- [x] No MQTT, responder, database or route contract changes are introduced.
- [ ] Existing client tests pass.
- [x] `npm`/Angular production build passes.

## Validation

### Client Tests and Build

Suggested commands from `diaries-client`:

```text
npm test -- --watch=false
npm run build
```

Use the repository's actual scripts if they differ.

Result on 2026-09-04: the production Angular build passed using the repository-installed Angular CLI. The host `npm` wrapper was unavailable because its referenced global `npm-cli.js` was missing, so the equivalent direct command was used:

```text
node scripts/generate-build-info.js
node node_modules/@angular/cli/bin/ng.js build --configuration production
```

The Karma test bundle compiled successfully and Chrome launched. The run completed with 8 passing and 14 failing tests. All remaining failures are pre-existing smoke-test setup defects: the affected TestBed configurations do not provide `HttpClient` and/or `ActivatedRoute`. Repairing the general client test harness is outside this presentation feature and remains required before this acceptance criterion can be closed.

### Manual Verification

Check at minimum:

1. sign-in page;
2. diaries list;
3. diary page list;
4. day view with transcription;
5. fragment editor;
6. an Angular Material dialog;
7. keyboard tab navigation and focus visibility.

Record screenshots before and after if useful.

## Dependencies

None. This is the foundation stage.

## Deployment and Rollback Notes

Client-only styling change. Rollback is achieved by deploying the previous `diaries-client` image/source revision. No database backup or retained-topic cleanup is required.

## Completion Summary

The source implementation is complete. `src/styles/_tokens.scss` is now the single Sass source for the reader palette and typography roles and emits matching `--diaries-*` runtime properties. Global page, link, focus and dialog-container styling consumes those properties. The stock prebuilt Material theme was replaced with the supported Material 20 Sass theme API and semantic system-token overrides; Material controls remain system-sans while reader content inherits the serif role. Existing neutral constants remain available through a compatibility entry point for the staged migration. Duplicate global Material and Quill stylesheet loading was removed, and the client README documents the design contract and the non-runtime relationship to `diaries-web`.

The production build passes and the full test bundle compiles. The change remains in progress pending repair of the pre-existing TestBed provider failures and manual authenticated screen/dialog/focus smoke testing.

## Completed Date

Not complete.
