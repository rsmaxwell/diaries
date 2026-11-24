# 0028 Step 1 — Reconcile v2 review drafts (91) and (92)

**Date:** 2026-11-23  
**Status:** Review draft recovered, not a migration manifest approval. Step 1 remains OPEN.

## Inputs

- `(91)`: saved in `diaries-sources-20261123-082352.zip` under the 0028 Step 1 private evidence area.
- `(92)`: `0028-0051-review-v2.DRAFT.PRIVATE (92).json`, exported after recording Fragment 598.
- Both inputs have the same `fingerprints` object, identical 72 occurrence keys, and equal per-occurrence frozen source identity fields (including source hashes, versions, original Marquee and link states).
- `(91)` contains 71 `CONVERT_TO_IMAGE` decisions, 70 confirmed, and one `DEFER` (Fragment 1564).
- `(92)` contains 32 `CONVERT_TO_IMAGE` decisions, 23 confirmed, one `DEFER`, and 39 blank dispositions. It must not replace `(91)`.

## Recovery

Start with `(91)` unchanged. For Fragment 598 only:
- Preserve its validated Page 752 provenance, original caption/date/sequence text, Image 18 identity, and other review fields.
- Copy `reviewed_at` and `v2_review_confirmed=YES` from `(92)`.
- Preserve the substantive older review note, append the newly recorded reviewer note from `(92)`, and clarify that 0052 corrected Image 18, while visual verification of legacy Fragment 598 in the production public Reader is a **post-0028** acceptance condition.

All other 71 occurrence objects are byte-equivalent in parsed content to `(91)`.

## Validated recovered draft

- 72 occurrences, 72 unique fragment/occurrence keys.
- 71 `CONVERT_TO_IMAGE`, all 71 `v2_review_confirmed=YES`.
- 1 explicitly `DEFER` (Fragment 1564).
- No blank dispositions.
- Preserves Fragment 575's previously approved caption override.
- `review_status=UNREVIEWED_V2` and `productionApplyAllowed=false` intentionally retained. **No production apply is authorised.**
- SHA-256: `db17c6e58760e3c7c1bbe7adcccd4f50994a3bf2fc3754ea5f25f250dd751657`

## Next acceptance work

Import the recovered PRIVATE JSON in the offline portal, verify the counts and key decisions, then export a new draft if needed. Run a fresh read-only production inventory/catalogue reconciliation after 0052; resolve any drift; validate and sign off the final reviewed manifest. Keep private JSON under the feature's private evidence directory, not in a public Git commit. Do not perform the migration or run an apply action as part of this recovery.
