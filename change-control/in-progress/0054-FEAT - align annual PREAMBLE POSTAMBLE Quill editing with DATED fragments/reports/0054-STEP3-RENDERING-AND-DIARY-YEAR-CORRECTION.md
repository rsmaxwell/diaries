# 0054 Step 3 — Rendering and diary/year correction

Date: 2026-11-27. Status: IMPLEMENTED IN CHANGE PACKAGE; VERIFICATION PENDING.

## Browser evidence

- PREAMBLE fragment 806: saving formatting and cancelling edits passed.
- POSTAMBLE fragment 2352: red background remains in Quill while editing, but disappears in the read-only Editor preview. Reader display also lacks red background; verify whether the Reader deployment includes the earlier Step 2 sanitizer patch.
- POSTAMBLE 1830 is displayed at the end of January in Diary 1, not December in Diary 2; this follows the current diary/year data model. Defer cross-diary modelling (see deferred design note).
- Targeted Angular tests last reported 32/32 pass *before* this correction.

## Changes

1. Annual Editor read-only preview now renders only supported text elements, filtered Quill classes, HTTP(S)/relative hyperlinks, and explicitly validated CSS foreground/background colour values using DOM node construction. It does not bypass Angular security sanitisation or insert untrusted HTML.
2. Annual Editor displays the selected diary's name and identifier adjacent to the year field.
3. Initially chooses the earliest DATED year belonging to a page in the selected diary; retains manual year choices. Diary transitions reset the automatic selection and unsubscribe stale dated-topic streams. The current year remains a fallback if no matching DATED fragment is present.
4. Adds preview safety/formatting tests and diary/year selection coverage.

## Verification gates (not yet executed)

- Client: targeted Angular tests, full Angular build, and browser check for PREAMBLE/POSTAMBLE formatting, cancel, diary switch/year override, and links.
- Reader: ensure Java sanitizer tests pass; rebuild/restart **development Reader** so it has the prior Step 2 HTML sanitisation improvements. Verify red POSTAMBLE background in Reader. If still absent, capture Reader HTML markup and inspect renderer.
- No responder or database change. No deployment attempted. Keep Step 3 OPEN.

## Risk/operation note

Initial year resolution subscribes to retained `diaries/fragments/+` and filters DATED records by the selected diary's page IDs. This is a broad retained-topic subscription, so observe MQTT subscription time and UI responsiveness; consider a narrower per-diary index in a future optimisation if necessary.
