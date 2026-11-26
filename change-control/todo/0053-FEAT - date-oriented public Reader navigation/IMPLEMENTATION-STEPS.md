# 0053-FEAT — Implementation steps

**Status:** TODO; plan only. Execute after 0029's current live-development acceptance work is completed or when separately prioritised.

## Step 1 — Confirm source contract and design calendar projection

- Check the actual Windows and controller Git/submodule revisions and uncommitted changes before editing, including the current `diaries-web` checkout (the 2026-11-25 source bundle may be older than local changes).
- Review existing routes in `diaries-web` `WebServer`, month-reader template, `ProjectionService`/`ProjectionSnapshot`, `DiaryMonthKey`, `DiaryDayKey`, `DiaryYearPlacementKey`, MQTT subscriptions and source Page/Marquee resolver.
- Determine the minimal year/month view model: key by calendar year/month, retain source Diary/Page IDs, stable ordering and appropriate grouping when multiple Diaries contribute. Document how PREAMBLE/POSTAMBLE are presented in a calendar aggregation without losing their Diary ownership.
- Map current published-month/volume routing and decide canonical calendar URLs plus redirects/backward compatibility for physical-volume deep links and selected Fragments.
- Confirm 1830 test fixture from actual data and any cross-volume overlap cases; preserve physical provenance.

**Gate:** agreed date-oriented view and route/provenance semantics, with no data migration.

## Step 2 — Implement complete Reader calendar navigation

- Implement calendar landing/index and year/month routes; cross-volume month selection and Previous/Next boundaries.
- Implement aggregated month rendering using the existing read-only retained MQTT projection, including DATED TEXT/IMAGE and year-level PREAMBLE/POSTAMBLE.
- Preserve physical Diary/Page and Marquee link/selection, highlights, captions, links and reader XSS protections. Keep the separate volume browser and legacy deep links.
- Add focused unit/integration tests for 1829→1830 and January→February 1830 transitions, overlap/ties, source provenance, annual placement, empty/unpublished months and replay.

**Gate:** coherent implementation ready for consolidated verification, not piecemeal release.

## Step 3 — Consolidated regression and acceptance

- Build and test `diaries-web`; run relevant integration/projection/route tests and browser checks with compatible responder/MQTT retained state.
- Verify navigation across the January/February 1830 physical boundary; test January 1828 and 1829 annual introductions, Marquee/source-page selection and IMAGE display.
- Inspect browser and reader/responder logs, and MQTT retained-state behaviour; fix regressions then repeat affected tests.
- Capture command outputs, versions, browser evidence, rollback considerations and deployment receipts under this feature's `evidence/` and `reports/` directories.
- Deploy only after authorisation; preserve physical-volume navigation and production rollback. Close only after formal acceptance.

**Gate:** calendar-first Reader accepted, old links and physical-source view preserved.
