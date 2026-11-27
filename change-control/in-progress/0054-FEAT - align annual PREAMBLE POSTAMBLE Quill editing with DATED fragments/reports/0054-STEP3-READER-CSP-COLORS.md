# 0054 — Step 3: Reader Quill colour rendering under CSP

## Evidence and cause

Browser Elements inspection of PREAMBLE Fragment 2353 on 2026-11-27 showed `<span style="background-color:rgb(230, 0, 0)">xxxx</span>` in the Reader DOM, but no visible red background. The Reader sends `style-src 'self'`, which disallows inline styles. This establishes that storage and HTML sanitisation preserve the colour; the browser does not apply the inline declaration.

## Implementation

- After OWASP HTML sanitisation, convert recognised values in Quill's default 35-colour palette to predefined `ql-color-<hex>` / `ql-background-<hex>` CSS classes. Other styles are discarded from the Reader output; the source content is not modified.
- Provide matching rules in the Reader's existing static CSS, used by DATED, PREAMBLE and POSTAMBLE.
- Preserve the existing `style-src 'self'` CSP and existing URL/HTML sanitisation.
- Add Java regression cases for colour conversion, class/font preservation, unknown colours and stylesheet mappings.

## Verification and remaining acceptance

Source and package checks completed in the packaging environment. Java 25 Gradle tests and Reader browser integration were **not** run here. Execute `./gradlew :diaries-web:test --tests 'com.rsmaxwell.diaries.web.rendering.RenderingSafetyTest'` then `./gradlew :diaries-web:installDist` from the Windows Diaries repo root. Restart the existing localhost:8080 Reader process from the updated distribution, refresh, and confirm a red background for PREAMBLE Fragment 2353 and POSTAMBLE Fragment 2352 in their respective Diary 1 months. Inspect DOM to verify a `ql-background-e60000` class instead of an inline `style` attribute. Check the existing Content Security Policy remains unchanged.

Feature remains OPEN until acceptance evidence and release checks are recorded.
