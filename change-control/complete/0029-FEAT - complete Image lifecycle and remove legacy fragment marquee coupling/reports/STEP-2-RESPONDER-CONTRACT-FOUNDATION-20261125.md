# Step 2 — Responder contract foundation (candidate, NOT deployed)

Source baseline: Diaries bundle `diaries-sources-20261125-123246.zip`; published parent revision `898f293`, responder submodule `7aa6296` as last observed. No live working tree was modified to prepare this ZIP. Confirm local status before applying.

## Implemented in this candidate

- Explicit `FragmentPlacement` enum with PREAMBLE, DATED and POSTAMBLE.
- Fragment JPA model carries `placement` and explicit optional Diary association. DTOs carry `diaryId` and `placement`.
- Publish DTO routes annual Fragments to `diaries/years/<diaryId>/<year>/<placement>/<fragmentId>` instead of a date alias. Canonical `diaries/fragments/<id>` retained.
- A pure structural validation helper and JUnit tests for exclusive Page/annual ownership.

## Integration limitations / blockers

**Do not build or deploy this candidate as a standalone release.** Database columns do not exist until Step 2 migration; the current application repositories, handlers, client and public reader still use the old contract. The `MARQUEE` enum is deliberately not switched to TEXT in this partial source candidate. The helper is not yet wired into handlers. Annual publishing and old alias removal require full startup/replay reconciliation and tracked previous topic ownership; changing the DTO alone does not remove stale retained aliases. JPA `diary_id` must be hydrated or resolved on save and on DB DTO retrieval. Reader and client changes must accompany this work. Existing `marquee.page_id` remains until all consumers derive Page through Fragment. The preceding migration SQL remains **NOT FOR EXECUTION**.

## Additional review observations

- `FragmentPublishDTO.getTopics()` currently always emits a date topic; annual publication needs an independent topic and a consumer projection for it.
- Retained publication on edits must remove **old** annual/date aliases when placement, year, or Diary changes; deriving only new topics is insufficient.
- The preamble migration needs to preserve HTML hyperlinks; approved simplification of 1828 decoration is a separate reviewed content transform.
- The 49 development-only legacy HTML records are not in the production-shaped SQL candidate and must be separately disposed before a development rehearsal.

Status: **candidate only, no compilation/test execution reported**. No acceptance gate closed.
