# 0053-FEAT — Implementation steps

**Status:** IN PROGRESS — implementation blocked until 0054-FEAT annual year-ownership is accepted. This is a coherent Reader feature; avoid unnecessarily subdividing implementation or staging deployments.

## Step 1 — Confirm source revisions and freeze the read-only Reader contract

- From the relevant Windows Cygwin checkout, record parent branch/revision/status, `.gitmodules`, each submodule revision/status, and particularly `diaries-web`. Compare with the supplied 2026-11-27 bundle; do not assume `mango` matches Windows. The bundle has no `.git` metadata and was captured with 0053 in `todo`.
- Confirm the **post-0054** source contract: DATED entries via Page → Diary; annual fragments by `year + placement`, with no owning Diary/Page/Marquee. Confirm deployed responder/Reader and retained MQTT records use the accepted 0054 representation. Keep canonical five-family MQTT subscription and atomic replay, no new persistence.
- Confirm new calendar URL design: recommend `/` = year index, `/years/{year}` = year overview, `/years/{year}/{month}` = calendar month, `/diaries` = physical volume index; preserve `/diaries/{diaryId}`, physical-month and Page URLs. Define `/fragments/{id}` canonical redirects for both DATED and annual fragments.
- Agree deterministic date/source ordering, year eligibility (including annual-only years), cross-volume month sequence and **year-scoped** PREAMBLE/EPILOGUE ordering as established by 0054. Annual fragments need no owning Diary, fake Page, Marquee or date heading. Define an annual fragment URL/anchor without forcing the scanned-page viewer.
- Clarify publication language: current valid retained records are readable; there is no per-object published flag. Preserve 404 for absent periods and 503 for unready/replaying state.
- Confirm relevant current historical records, particularly the 1830 split and 1828/1829 annual sections, against up-to-date development retained data. Do not rely on old database exports as acceptance evidence.

**Gate:** 0054 completion and its schema/MQTT contract independently verified; documented URL/ordering/optional provenance decisions and repository baseline; no data migration in 0053.

## Step 2 — Implement one coherent calendar-first Reader workflow

- Add a read-only calendar-year/month index to immutable `ProjectionSnapshot` or a snapshot-owned projection. Reuse resolved DATED fragments and **0054 year-owned annual indices**. Keep stable ordering and rebuild on the same atomic retained-state replay.
- Extend `SiteUrls`, Javalin `WebServer`, year/landing/month templates and navigation; preserve the physical archive routes without ambiguous redirects. Include GET/HEAD and expected method restrictions for new routes, breadcrumbs, canonical/ETag semantics and correct 404/503 behaviour.
- Aggregate all sources for a calendar month. Build fragment view and JS selection links to the calendar URL; keep actual Diary/Page/Marquee data per fragment and switch displayed source scans when crossing Diaries. Support selected-fragment query+hash, source-page return links, browser Back/Forward and deep links.
- Render year-owned preambles before and epilogues after the year's DATED content, keeping annual-only years reachable. Provide **optional, grounded source** physical-Diary provenance if available and safe TEXT/IMAGE/unavailable-media rendering; do not treat annual fragments as page-backed viewer selections.
- Reuse sanitisation/CSP and URL policies, typed media state, CSS/mobile controls, and GET/HEAD-only public behaviour; avoid client, responder, schema or MQTT protocol changes.
- Add focused projection and HTTP tests covering 1828/1829 annual content, January → February 1830, same-date multi-Diary overlaps, multiple annual sections for one year, annual-only year, legacy link preservation, selected fragments, scan switching, missing images, 404 vs 503 and replay/tombstones.

**Gate:** integrated reader feature and focused tests ready for consolidated verification.

## Step 3 — Consolidated regression, acceptance and separately authorised release

- From the verified parent checkout, run `./gradlew :diaries-web:test :diaries-web:build` in an appropriate terminal. Run relevant full Reader/MQTT integration tests against compatible responder and broker state. Validate changes without repeating already-accepted unrelated expensive migrations.
- Use the live development Reader for browser checks on desktop/mobile: calendar landing/year, January/February 1830 transition, cross-Diary source image and Marquee selection, 1828/1829 annual content, IMAGE/legacy rendering, physical routes and fragment links. Inspect Reader/responder logs and retained MQTT state together; fix failures and rerun affected tests.
- Record Git/submodule revisions, commands and outputs, application versions, checks, browser findings and rollback considerations under this feature's `evidence/` and `reports/` folders. No permanent evidence outside the Diaries parent feature directory.
- Do not publish/deploy to production without explicit authorisation. On successful accepted verification, record deployment/rollback receipts and request formal closure. Do not mark CLOSED based on a plan alone.

**Gate:** accepted integrated calendar-first Reader with archival and deep-link compatibility.
