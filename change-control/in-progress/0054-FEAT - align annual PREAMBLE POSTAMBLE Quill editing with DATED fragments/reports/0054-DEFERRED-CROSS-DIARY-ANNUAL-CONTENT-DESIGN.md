# 0054-FEAT — Deferred design consideration: annual editorial content spanning physical diaries

## Status
Deferred design consideration. **Not a defect in 0054 and not a closure blocker.** No new feature is opened by this report, and no data-model or Reader-ordering change is authorised here.

## Observed behaviour (browser acceptance, 2026-11-27)
The current PREAMBLE/POSTAMBLE model associates each fragment with a **specific diary and calendar year**. The Reader places annual fragments around the dated entries belonging to that diary/year.

The historical entries for 1830 span two physical diaries:
- `diary-1828-and-1829-and-jan-1830` (Diary 1) contains January 1830, and the 1830 PREAMBLE (`Highlights`, Fragment 806).
- `diary-1830` (Diary 2) continues from February 1830 through December.
- POSTAMBLE Fragment 2352 associated with Diary 1/year 1830 appears after **January** in Diary 1, not after December in Diary 2. This placement was confirmed in the Reader and is consistent with the current implementation, though potentially confusing to readers/editors.

## Deferred question
Should a PREAMBLE/POSTAMBLE be associated with a *calendar year spanning multiple physical diaries*, a *physical diary*, or should separate concepts be supported?

Future design work should evaluate:
- Year-level editorial content independent of physical diary boundaries.
- Distinct diary-level introductions/conclusions versus year-level introductions/conclusions.
- Reader placement and chronological navigation across physical diaries, without duplicates.
- Editor selection and discoverability, persistence, existing fragment relationships and data migration.

## 0054 scope decision
Keep the **existing diary/year model** and current Reader placement for 0054. Do not migrate Fragment 806 or 2352 as part of this feature. Revisit through a separately scoped feature when a replacement design has been agreed.

## Separate outstanding acceptance issue
This deferral **does not** close the rich-text rendering issue: a red background applied to POSTAMBLE Fragment 2352 was visible while editing but absent from the Editor read-only display and Reader. Determine whether saved Quill HTML retains the style and fix the affected rendering path before accepting 0054.
