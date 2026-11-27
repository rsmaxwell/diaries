# 0054-FEAT — Step 3 toolbar-parity adjustment

**Status:** IMPLEMENTED; verification OPEN. **Owner decision:** 27 November 2026.

## Agreed scope

DATED, PREAMBLE and POSTAMBLE TEXT use the same Quill toolbar object. Retain links, font, size and formatting; remove the inline image toolbar control everywhere. IMAGE fragments and the Image Catalogue remain the supported image workflow.

## Implementation

- Replaced separate `DATED_TEXT_EDITOR_MODULES` and `ANNUAL_TEXT_EDITOR_MODULES` with one `TEXT_EDITOR_MODULES` constant, used by both components.
- Removed DATED Quill image picker handler and now-unused dependency; no change to IMAGE fragments or image catalogue operations.
- Added a shared paste/drop guard for image files and rich HTML containing `<img>`. Such an entire paste or drop is rejected (not silently stripped); ordinary text, formatting and links are allowed. This does not alter hydration of already-saved legacy HTML; existing HTML and image migrations remain a separate concern.
- Applied the guard to the DATED editor and annual **new** and **edit** text editors, with cleanup on component destruction. Added focused tests.
- Reader `FragmentHtmlSanitizer` already uses `allowStandardUrlProtocols()` and was not modified in this adjustment. Quill's default hyperlink behaviour remains in place. No new application-level link URL validation was introduced.

## Verification performed in preparation environment

- TypeScript parser/type check of self-contained shared-toolbar file: `tsc --noEmit --noResolve --target es2022 --lib dom,es2022`: PASS.
- Source-level inspection: both components import the same toolbar object; annual new and edit events attach the guard; old image handler removed.
- Package contents and integrity: inspected.

**Not performed here:** Angular build or Karma tests because this source bundle has no `node_modules`; browser regression and release validation remain OPEN. Previously reported Step 2 test success predates this adjustment and does not validate it.

## Recommended Windows Cygwin verification

From `C:/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries`, after reviewing/applying the ZIP:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
(cd diaries-client && npx ng test --watch=false --browsers=ChromeHeadless --include=src/app/fragment/quill-text-toolbar.spec.ts --include=src/app/fragment/text-panel/text-panel.component.spec.ts --include=src/app/diary/annual-editor/annual-editor.component.spec.ts)
(cd diaries-client && npm run build)
```

Then browser-check both annual create/edit editors and DATED editor: identical toolbar, link insertion, font/size/colour formatting, image button absent, image paste/drop rejected, normal paste permitted; verify existing catalogue IMAGE fragments and Reader rendering. Preserve log evidence within this feature directory. Do not release or close 0054 without acceptance.

## Repository state

The source bundle represents the 26 November 2026 snapshot; Step 2 package was used as the baseline for this supplemental ZIP. Latest user terminal reports indicated `main` with uncommitted Client and Reader changes and untracked feature documentation; review with Beyond Compare and do not overwrite unrelated work. Parent submodules are independent; commit Client separately before updating parent pin at release.

## Rollback

Revert only this supplemental change using the previous version from the Step 2 ZIP, or reverse the relevant Client commit once made. Do not roll back the whole parent feature directory merely to undo toolbar parity.
