# 0029-FEAT — Step 2 annual sequence isolation (integration overlay)

Date: 2026-11-25
Status: **candidate — not deployable or accepted**

## Baseline and package relationship

Based on `diaries-sources-20261125-123246.zip` with `0029-FEAT-step2-consolidated-source-review-20261125.zip` overlaid. Apply this **after** the consolidated source candidate when assembling the eventual integrated feature; it does not replace the consolidated candidate. Source bundle lacks Git history, so the Windows checkout must be reviewed before applying.

## Defect addressed

The old `findAllByDate(year,month,day)` sequence selection included all Fragments for that date. Under the approved hybrid design, a PREAMBLE and a dated entry may both retain `year/month/day` = 1 January. Normalising that date would mistakenly renumber the year preamble (or postamble), potentially losing its intended order.

## Changes

- `FragmentRepository.findAllByDate` selects only DATED or pre-migration NULL placement; it cannot reorder annual Fragments.
- A new `findAllByAnnualPlacement(diaryId,year,placement)` query isolates each annual group.
- `FragmentSequenceNormaliser.normaliseAnnual` renumbers within the specified Diary/year/PREAMBLE-or-POSTAMBLE group using the existing optimistic version update.
- `normaliseAffectedDates` routes changes of annual sequence to the annual normaliser and rejects an annual ownership transition via this generic entry point.
- Focused repository-double tests cover isolation from dated entries and from the opposite annual group, plus invalid placement.

## Verification and outstanding integration

Source inspection and static assertions performed; **full Gradle compilation and JUnit tests not run** because a usable Gradle distribution is not installed in this environment. This does not constitute a passing build.

Remaining requirements before running migration or deploying: complete annual creation/update/deletion RPCs and editor UI; publish/remove old retained aliases when identity changes; ensure year-level reader integration; resolve 49 development-only legacy sources; run Windows full builds, tests and end-to-end verification. The database schema migration remains prohibited until those integrations are ready.

No database or production operations performed.
