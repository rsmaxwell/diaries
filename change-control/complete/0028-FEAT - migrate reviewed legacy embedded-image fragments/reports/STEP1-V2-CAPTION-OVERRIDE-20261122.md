# 0028 Step 1 — V2 caption override for IMAGE Fragment migration

**Status:** implementation and offline regression tests passed in the supplied source copy; **Step 1 remains OPEN**. No production apply permission or migration implementation is included.

## Purpose

Fragment 575 has a frozen caption, `Voyage for Copenhagen to St Petersburg`, but its reviewer-approved editorial caption is `Voyage from Copenhagen to St Petersburg`. The V2 review JSON previously had no editable override, although the historical V1 review had one.

## Changes

- Retain exact source filename `tools/step4_0051_compatibility_review.py`, existing schema `0028-0051-review-v2` and source fingerprints. Add reviewer-owned string `caption_override` to prepared V2 decision records (initial value `""`, preserving the frozen caption). Do not derive it automatically from `legacy_review.caption_override`.
- In the offline portal, show the frozen original caption (when unambiguously extractable from verified simple HTML), editable per-occurrence override and effective IMAGE Fragment caption. For complex HTML, require manual source review instead of asserting an unverified caption. Always display data as inert text, never render HTML from the source.
- Include override in browser import/export and material review fields. Changing it invalidates `reviewed_at` and `v2_review_confirmed`. Old V2 exported JSON without the new field imports unchanged.
- Reject overrides that are non-string, whitespace-only, longer than 2000 characters, contain control/newline/HTML angle brackets, or are requested for DEFER/KEEP_LEGACY decisions. The validator still cannot authorise migration.
- Provide the already-rendered **PRIVATE** offline portal at the existing filename and path `evidence/Step 1/private/20261121T122838Z-post0051-v2/0028-0051-review-v2.SOURCE-SUGGESTIONS.PRIVATE.html`, so Ctrl+F5 reloads the new UI after applying the ZIP. The sealed original V2 draft, `SHA256SUMS.txt`, frozen inventory, legacy review and 0051 evidence are untouched.
- Portal was regenerated from the user-provided `(33)` draft plus the checksum-verified frozen source snapshot. It carries PRIVATE text/source snippets and the 72 review occurrences; **do not commit this HTML to Git or publish this ZIP**. Existing reviewer decisions are unchanged except for adding empty `caption_override` controls.

## Verification (local source copy, 22 November 2026)

- Python syntax compilation: PASS.
- 36 `test_step4_0051*.py` standard-library unit tests: PASS, including five new caption-override tests.
- Chromium headless offline portal: PASS (72 occurrences, reviewed decisions unchanged, source/effective caption preview, override edit clears timestamp/confirmation, export and import of older draft `(33)`, preserved protected evidence and disabled migration).
- No database access, MQTT, API changes, deployment, or runtime migration performed. No production apply authorisation granted.

## Windows Cygwin / Beyond Compare application

1. Export the current browser draft **before** applying the ZIP: refreshing an offline page discards unsaved in-memory edits.
2. Inspect and apply the ZIP relative to the Windows Diaries repository root with Beyond Compare 4. Preserve independent local modifications by merging the Python tool if necessary. The package intentionally replaces one generated, unsealed PRIVATE HTML portal at the same path.
3. With that HTML open in the browser, press **Ctrl+F5**. No restart or source-regeneration command is needed because the replacement HTML is included in the package. If you are viewing a different HTML file, open the path above.
4. Draft `(33)` is preloaded in the replacement portal. If you have a newer exported draft, use **Resume from exported PRIVATE JSON** to import it.
5. For Fragment 575, enter `Voyage from Copenhagen to St Petersburg` in Caption override; then **Record review time**, re-confirm V2, and export the new PRIVATE JSON. The old original figcaption remains frozen, untouched.

## Follow-on migration acceptance

The 0028 migration must apply the reviewed, nonblank `caption_override` to the new IMAGE Fragment's `text` field instead of changing the reusable catalogue Image caption. This code is **not** included here; add coverage for Fragment 575 at the 0028 migration implementation/acceptance stage.
