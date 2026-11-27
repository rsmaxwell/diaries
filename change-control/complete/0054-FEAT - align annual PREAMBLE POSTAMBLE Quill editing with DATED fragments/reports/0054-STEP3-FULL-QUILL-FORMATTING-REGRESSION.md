# 0054 Step 3 — Shared Quill formatting regression and Reader bullet preservation

## Purpose

Validate the complete shared DATED/PREAMBLE/POSTAMBLE Quill toolbar through save, read-only Editor preview, and Java Reader output. The previously verified red-background fix is necessary but not sufficient evidence for all formatting.

## Source findings

- All three editors share `TEXT_EDITOR_MODULES`: bold, italic, underline, text/background colours (Quill default palette), headings (1–3), bullet/ordered lists, hyperlinks, font family and size.
- Reader sanitiser currently retains semantic formatting and approved `ql-*` classes; stylesheet defines heading/browser defaults, font families/sizes, alignment and palette-colour classes.
- Quill 2 represents bullet items as `<ol><li data-list="bullet">...`. Sanitisation drops `data-list`, causing the Reader to display bullet items as numbered. This patch converts only the recognised bullet marker to a fixed `ql-list-bullet` class before OWASP sanitation; other attributes remain subject to existing sanitisation.
- Reader already allows `ql-indent-1` through `ql-indent-5`, but lacked CSS indentation definitions. This patch adds the corresponding CSS rules.
- Existing strict Reader CSP remains unchanged, and the palette/class colour conversion from the previous package remains in place.

## Included files

- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/rendering/FragmentHtmlSanitizer.java`
- `diaries-web/src/main/resources/static/css/diaries.css`
- `diaries-web/src/test/java/com/rsmaxwell/diaries/web/rendering/RenderingSafetyTest.java`
- this report

## Automated verification requirements

1. `./gradlew :diaries-web:test --tests 'com.rsmaxwell.diaries.web.rendering.RenderingSafetyTest'`
2. `./gradlew :diaries-web:installDist`
3. Preserve and report actual exit codes and test failures.

Tests now cover semantic bold/italic/underline, headings, font classes and sizes, combined colours, safe hyperlinks, Quill 2 bullets with ordered-list companions, indentation, clear-format output, CSS availability, and rejection of executable HTML/unsafe attributes.

**Status**: prepared, not yet accepted. The container could not run Gradle; wrapper attempted to download Gradle 9.6.1 from `services.gradle.org` but network access was unavailable. No deployment performed.

## Browser acceptance after Reader restart

Use a temporary PREAMBLE TEXT fragment in an appropriate development diary/year. Test headings, bold/italic/underline, bullet and numbered lists, both font families, size choices, blue foreground, red background, a safe external link, combined formatting and clearing a format. Save and reopen in Quill; compare read-only Editor preview and Reader. Repeat quick parity checks in POSTAMBLE and DATED and confirm pasted images remain blocked. Check mixed bullet/ordered list particularly carefully. Do not erase historical content; remove only temporary test fragments after evidence is accepted.

Record actual screenshot/test evidence in the 0054 feature directory. Do not close Step 3 before these checks pass.
