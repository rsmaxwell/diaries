# 0054 Step 3 — Prevent inline image embeds (second-layer guard)

## Browser evidence
27 November 2026: screenshot pasted directly into DATED Quill TEXT Fragment 2354 despite image toolbar control being removed. Hyperlink to example.com worked (PASS). Image exclusion was a confirmed FAIL.

## Implementation
- Keep the same shared toolbar in DATED/PREAMBLE/POSTAMBLE.
- Check both ClipboardData.items and ClipboardData.files during paste.
- Listen for user-origin Quill `text-change` deltas and remove newly inserted `image` embeds, which covers clipboard handlers that bypass paste-event prevention.
- Preserve previously saved legacy embeds loaded through programmatic (`api`) changes.
- Unregister the delta listener on editor cleanup.
- Add tests for image-file paste, paste fallback, programmatic loads and newly inserted image embeds.

## Acceptance status
Source-level package prepared; tests/build and actual clipboard paste regression **NOT RUN** here. Apply on top of latest 0054 packages. Verify in DATED and annual editors, including screenshot paste and file drag/drop. Do not save an image during testing. 0054 remains OPEN.
