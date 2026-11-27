# 0053-FEAT — Source and scope review (2026-11-27)

## Review scope / limitations

- Inspected the uploaded `diaries-sources-20261127-203046.zip` snapshot, including parent `ARCHITECTURE.md`, `diaries-web` implementation/templates/JS/tests, fragment/DTO contracts in `diaries-responder`, and Angular editor routes.
- The bundle locates 0053 under `change-control/todo`, while the user reports having moved it to `in-progress` after preparing it. The user-reported move is authoritative; this review ZIP targets **only** the in-progress path and intentionally does not restore the TODO directory.
- The source ZIP does not include `.git` metadata; checkout branch, revision, modifications, submodule pointers and correspondence with live production or controller remain **unverified**. No runtime, retained-data or database checks were run; no tests/deployments were performed for this document review.

## Findings

1. **Still required.** `diaries-web/src/main/java/com/rsmaxwell/diaries/web/http/WebServer.java` currently renders `/` and `/diaries` as the same physical Diary index. `/diaries/{diaryId}/{year}/{month}` and its adjacent-month links use `snapshot.monthsForDiary(diaryId)`. There is no year-index route or cross-Diary month query.
2. **Existing projection is a good base.** `ProjectionSnapshot.java` indexes DATED fragments under `DiaryMonthKey(diaryId, month)` and annual fragments under `DiaryYearPlacementKey(diaryId, year, placement)`. A global calendar index can be derived from existing resolved fragments; no new MQTT topics, database columns, or responder changes are necessary for the Reader-only feature.
3. **Page ownership must remain physical.** DATED fragments are resolved from `fragment.pageId → page.diaryId`, whereas `FragmentItem.java` requires annual fragments to carry `diaryId` and forbids `pageId` and `marqueeId`. Thus requirement language promising physical Page and Marquee links for *every* fragment is inaccurate. Annual fragments should carry Diary provenance and a year/anchor link, not a fabricated source Page.
4. **Annual placement currently local to one Diary.** `WebServer.renderMonth` inserts annual sections on the first and last available DATED month of that *physical* Diary/year. A calendar aggregation must place each physical Diary's preamble before its first dated entry and its postamble after its last, even when other Diaries also contribute to that month. Annual-only Diary/year material must remain findable. `annualFragmentViews` currently handles IMAGE metadata only when available and does not display source/provenance labels; extend safely.
5. **Fragment selection is coupled to URL and viewer state.** `SiteUrls.monthFragment()` generates a physical month URL with `?fragment=id#fragment-id`; `diaries.js` uses `data-fragment-url`, `history.pushState`, query-parameter restore on `popstate`, and page ID/image switching. Merely adding global routes without reworking those view URLs would silently return users to volume-specific pages. Preserve legacy routes and source-page links while generating calendar-specific links for calendar view.
6. **No separate public/private flag in the Reader contract.** `TopicParser.canonicalFilters()` subscribes only to canonical retained Diary/Page/Fragment/Marquee/Image entities. Index membership is derived from resolved available data, not a publication boolean. Clarify the term *published* as 'available in the Reader projection'; a new visibility policy would be a distinct feature. `ProjectionService` preserves atomic replay readiness: unready=503, absent route/content=404.
7. **Rendering compatibility.** `FragmentItem.effectiveType()` still supports legacy null → MARQUEE and explicit unknown values; it is incorrect to assume all existing records are strictly TEXT/IMAGE. Reuse the established `FragmentHtmlSanitizer`, `ImageLinkUrlPolicy`, typed media logic, and scanned-page viewer. New annual pages should show missing/unavailable catalogue Images without throwing or inventing URLs.
8. **Architecture consistency.** `diaries-web/AGENTS.md` prohibits writes, RPC, direct DB access and authentication editing flows. The feature's calendar projection is consistent with this. The parent `ARCHITECTURE.md` describes the intended 0029 hybrid ownership model; its target/deployed-status prose must not be mistaken for runtime deployment evidence.
9. **Editor link wording needs care.** `diaries-client/src/app/app.routes.ts` has authenticated `/diary/:diaryId/:pageId[/:fragmentId]` routes; an unauthenticated Reader need not expose an Edit control. Physical Diary and source-page links are required; any editor deep link should be an explicitly approved, auth-guarded optional affordance.

## Recommended design decisions (for Step 1 confirmation)

- Canonical public chronology: `/` year index; `/years/{year}` annual/year overview; `/years/{year}/{month}` aggregated chronological month; `/diaries` and existing physical routes continue as archival views. Keep date/month numbers zero padded and reuse the configured base path.
- Dates belong to historical calendar `YearMonth.from(fragment.date())`. For same-date ties, order deterministically by physical Diary sequence+ID, Page sequence+ID, Fragment sequence+ID; make no text/date-based deduplication. The annual and DATED index should be derived within each immutable projection generation.
- Keep 404 for an absent month, including an annual-only year without dated months. Year overview can show annual-only sections; do not create fictitious month entries. Show explicit Diary attribution for cross-volume contributions.
- Preserve `?fragment=id#fragment-id` for DATED selection, including browser Back/Forward and actual scanned Page switching. Annual fragment IDs need a separate year/annual-anchor resolution path, because `resolveFragment` currently indexes DATED fragments only.
- Keep physical-month URLs serving original scoped content unless explicit, unambiguous redirect semantics are accepted. Preserve source-page and `/fragments/{id}` navigation and ensure the canonical calendar route is used from calendar views.
- Base Reader acceptance on up-to-date development MQTT/projection data, particularly whether all 1830 months are actually present; no assumed publication flag or completed live 0029 migration.

## Conclusion

**Keep 0053 IN PROGRESS.** The original motivation remains valid, and the proposed Reader-only implementation is architecturally consistent. The principal corrections are source-link rules for annual fragments, precise annual placement when multiple physical Diaries overlap, global link/selection semantics, and documentation of current publication/replay and type compatibility.

**Evidence state:** review only. No Step is CLOSED, and no implementation, verification, rollout or formal acceptance is asserted here.

## Coordination update — 2026-11-27

This report describes **pre-0054** source observations, not the future contract. 0054-FEAT will migrate annual PREAMBLE/POSTAMBLE ownership from Diary+year to calendar year, updating client/responder/Reader persistence and retained payload. For 0053, the former Diary/year annual rendering recommendation is superseded by year-level preamble/postamble ordering. 0053 implementation must wait until 0054 is accepted.
