# 0054-FEAT — Align annual PREAMBLE/POSTAMBLE Quill editing with DATED fragments

**Status:** CLOSED — 27 November 2026 (owner approved)  
**Repository:** Diaries parent repository (`rsmaxwell/diaries`)  
**Component:** Angular Diaries Client — annual editor  
**Production impact:** None until implementation, testing and release approval

## User request

Upgrade the text entry fields for PREAMBLE and POSTAMBLE Fragments to offer the same Quill rich-text editing experience as normal DATED TEXT Fragments.

## Important source observation

In the uploaded `diaries-sources-20261126-131148.zip` snapshot, the annual editor **already uses `ngx-quill`** for both new and existing annual TEXT Fragments:

- `diaries-client/src/app/diary/annual-editor/annual-editor.component.html` has `<quill-editor>` controls bound to `newText` and `editText`, with `format="html"`.
- `annual-editor.component.ts` already imports `QuillModule` and specifies a reduced toolbar (basic formatting, headings, lists and links).
- Normal DATED TEXT Fragments use `diaries-client/src/app/fragment/text-panel/text-panel.component.{html,ts}` with a fuller toolbar, image handling, font/size/colour controls, reactive form and more advanced edit/lock management.

Therefore this feature is primarily **editor-parity and usability work**, not an initial Quill installation. Verify the live Windows checkout before changing code, because the source bundle predates the final 0029 closure.

## Objective

Provide PREAMBLE and POSTAMBLE TEXT Fragments with a Quill interface matching the normal DATED TEXT workflow where appropriate, without changing annual Fragment ownership, placement or image catalogue semantics.

## Scope

- Assess and align annual Quill editing/creation toolbar, appearance, keyboard behaviour and HTML persistence with the DATED transcription editor.
- Reuse or extract shared Quill configuration/behaviour where practical to prevent the two editors drifting.
- Preserve existing annual Fragment CRUD, order, year/placement selection and MQTT retained update behaviour.
- Preserve explicit lock acquisition, save, unchanged-edit unlock, cancel and failure/retry semantics.
- Ensure HTML (including links, styling and any supported embedded images) survives save/reload/Reader display without accidental transformations; only enable DATED image functionality if compatible with annual content and catalogue policy.
- Cover both PREAMBLE and POSTAMBLE and new vs existing TEXT Fragments.
- Respect the existing server-side size/validation requirements (client currently checks 4096 characters on edit); avoid silent truncation or destructive conversion.

## Out of scope

- Database migration or change to the Fragment ownership/schema established in 0029.
- Modifying annual IMAGE Fragment catalogue/link management.
- Reworking the DATED editor beyond safe shared-component refactoring.
- Reader redesign or unrelated feature work.
- Deployment before consolidated verification and approval.

## Acceptance criteria

1. Both PREAMBLE and POSTAMBLE TEXT Fragments can be created and edited using Quill, with the agreed parity controls and presentation of DATED text.
2. Rich HTML including formatting and links persists after save, navigation, MQTT refresh, page reload and reopening an annual Fragment; existing stored HTML renders without loss.
3. Lock ownership, unchanged edit, cancel, save failure, retry and navigation do not leave stale edit locks.
4. Annual IMAGE fragments, sequence order, year/placement filters and existing DATED editing continue working unchanged.
5. Focused Angular tests and consolidated browser integration/regression tests pass for creation/editing of both annual placements, DATED text and Reader rendering.
6. Changes, source revisions and test results are documented under this feature; status is changed to CLOSED only upon acceptance.

## Delivery and evidence

Keep this feature's design, scripts, test logs and acceptance reports under this directory. Apply source changes in a coherent client increment; test together after implementation. No production migration is anticipated.

## Initial evidence sources

- Uploaded Diaries sources dated 26 November 2026 at 13:11:48.
- `diaries-client/src/app/diary/annual-editor/annual-editor.component.ts` and `.html`.
- `diaries-client/src/app/fragment/text-panel/text-panel.component.ts` and `.html`.
- Closed `0029-FEAT` provides the established annual Fragment ownership and lifecycle contract.

## Formal closure — 27 November 2026

All acceptance gates are CLOSED following explicit owner approval. Production
Client `0.0.9-build-82`, Reader `0.0.9-build-11` and unchanged Responder
`0.0.9-build-87` were verified healthy. See the production acceptance report
for source revisions, smoke testing and rollback instructions. The separate
cross-diary annual-content design consideration remains deferred.
