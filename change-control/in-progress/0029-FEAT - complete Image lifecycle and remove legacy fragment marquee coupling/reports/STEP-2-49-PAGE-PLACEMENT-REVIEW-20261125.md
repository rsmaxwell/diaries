# 0029-FEAT Step 2 — source HTML and Page context review (25 November 2026)

**State: REVIEW CANDIDATE, NO MIGRATION AUTHORITY.** Based on the uploaded 49-row source-context CSV, 63-row Page-context CSV and 49-row original manifest. No database connection or write operation was made in preparing this report.

## Summary

- 49 source records present with `source_unchanged=t` and their original HTML preserved. All have a unique candidate catalogue Image, but catalogue checksum metadata is **not proof** of byte equivalence to the original embedded image.
- One existing dated IMAGE link: source Fragment **84**, Image **3**, Page **692**, dated IMAGE Fragment **2338**. Its presence does not justify deleting source Fragment 84 without content and caption checks.
- 35 records have a single same-day candidate Page; those are **ownership candidates**, not approved placements.
- 10 of the 13 multiple-Page cases have an especially strong Page identification based on the scanned-image filename `imgNNNN` matching the candidate Page name and consistency with the same-day text.
- Three records remain genuinely unresolved: source Fragments **611, 612, 613** (Alexander Nevsky Lavra, 14 July 1829). Their filenames begin `img2903`, while candidate Pages **756 (`img2904`)** and **757 (`img2905`)** both hold narrative for 14 July. Both Pages belong to the same Diary, but context alone cannot prove which Page should own the image. Do not assign automatically.

## Provisional multiple-Page assignments (NOT approved)

| Source Fragment(s) | Image(s) | Candidate Pages | Strong suggested Page | Basis |
|---|---|---|---|---|
| 114–118 | 5–9 | 694 `img2842`, 695 `img2843` | **694** | Image filenames `img2842`; April 17 narrative begins on 694 |
| 565 | 75 | 741 `img2889`, 742 `img2890`, 743 `img2891` | **743** | `img2891` filename; June 20 narrative continues there |
| 575 | 76 | 744 `img2892`, 745 `img2893` | **744** | `img2892` filename and date context |
| 598–600 | 18, 21, 20 | 752 `img2900`, 753 `img2901` | **752** | `img2900` filenames; Hermitage visit begins in Page 752 narrative |
| 611–613 | 24, 23, 26 | 756 `img2904`, 757 `img2905` | **UNRESOLVED** | `img2903` filenames match neither candidate; visit spans Page boundary |

## Source content and risk notes

- HTML captions and image `src` values are transcribed into the annotated CSV for **all 49** source Fragments. Use them when constructing new `IMAGE` Fragment text/labels; do not discard caption information.
- There are 48 unique catalogue Image IDs across 49 records: Fragments **547** and **565** both refer to Image **75** (`img2891-image-copenhagen-east.png`). This is not inherently a duplicate: dates and captions differ.
- Corrected catalogue Images **18** (Hermitage; source 598) and **25** (St Isaac’s Church; source 606) require checks of actual current Image/file contents, not just the historical catalogue metadata or matching filenames.
- Some legacy HTML has malformed incidental quote characters next to `img` tags. Preserve original source verbatim in evidence, but migrate structured caption/image fields rather than replaying malformed HTML unchanged.
- The approved 0029 production-shaped `step2-hybrid-schema-and-data.sql` has an exact eleven-Page-less-row guard. **Do not change that guard to accept 60 rows or run it on this development database.** The 49 records must be reconciled through reviewed 0028-compatible conversion evidence first.

## Consolidated next gate

1. Obtain human confirmation of Page ownership for the three unresolved Alexander Nevsky records; confirm the 10 strong suggestions and the 35 single candidates against the original scanned diary and narrative where necessary.
2. Recheck source HTML hashes and catalogue Image/file checksums against the actual source media, including Images 18 and 25. Record source-to-destination and content/caption retention receipts using the established 0028 journal model.
3. Carry out **one** isolated-restored-database rehearsal: migrate the 48 missing IMAGE Fragments idempotently, verify preexisting Fragment 2338, reconcile the original 49 without deleting originals until acceptance checks pass; then rehearse the guarded 0029 ownership/schema transition with an explicit development-specific approved mapping (not by weakening production SQL).
4. Verify row counts, Page/Diary/date/order, retained MQTT topics, reader and Angular authoring behaviour. Record backup/restore and rollback checks before considering live development deployment.

## Verification status

Source/page CSV review and ZIP integrity: inspected locally. No runtime migration, database changes, byte equivalence verification, reader browser checks or deployment are claimed. **0029-FEAT Step 2 OPEN.**
