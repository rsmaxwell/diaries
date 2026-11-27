# 0053-FEAT — Date-oriented public Reader navigation

## Change control

- **Type:** FEAT
- **Status:** IN PROGRESS — design reviewed 2026-11-27; implementation deferred until 0054 is accepted
- **Priority:** Normal
- **Opened:** 2026-11-26
- **Primary component:** `diaries-web` (read-only Java reader)
- **Prerequisite:** 0054-FEAT (calendar-year ownership of annual fragments), implemented and accepted **before** 0053 implementation. **Related:** prior 0029 work (historical context; verify status), 0028-FEAT (separate embedded-image work)
- **Review record:** [reports/2026-11-27-source-review.md](reports/2026-11-27-source-review.md)

## Problem and continuing relevance

The public Reader currently indexes by physical Diary and offers months only within that Diary. The physical volume `diary-1828-and-1829-and-jan-1830` contains January 1830, while `diary-1830` contains the later months. A reader should be able to browse one calendar year and move directly from January to February 1830 without choosing another volume.

Source review of `diaries-sources-20261127-203046.zip` confirms that calendar-first Reader routes and global calendar-month indices are **not yet implemented**. Existing `diaries-web` routes and month navigation remain physical-Diary-specific.

## Objective

Make historical **calendar year and month the primary public Reader navigation** while retaining physical Diaries, scanned Pages, Marquees and their existing persistent ownership as archival provenance. Implement this exclusively as a read-only projection over already-submitted canonical retained MQTT entities.

## Requirements

1. The `/` Reader landing page shows available historical years in chronological order; each year page shows available months in calendar order. The physical-volume browser remains accessible at `/diaries`.
2. All available January–December 1830 material belongs to the single calendar year 1830. Previous/Next published-month navigation crosses physical volume boundaries (notably January → February 1830) and skips genuinely missing months rather than manufacturing them.
3. A calendar month aggregates **all** resolvable DATED fragments for that calendar month, even if associated Pages belong to different Diaries. Order by date, then a documented deterministic physical-source order (Diary sequence/ID, Page sequence/ID, Fragment sequence/ID); retain distinct entries even when their dates or text match.
4. Each DATED entry retains its originating physical Diary, Page and optional Marquee, and a working link to the Reader source-page view. Selecting any entry displays the **actual** scanned Page and optional Marquee, including when the previous entry originated in another Diary. Preserve authenticated editor deep links only if separately agreed; no editor controls or privileged data are exposed by this public Reader.
5. Consume 0054's **calendar-year-owned** PREAMBLE and POSTAMBLE fragments. Present all of a year's preambles before its DATED entries and all postambles afterward, in deterministic annual sequence/ID order. Annual content has no owning Diary/Page/Marquee and does not require a manufactured date heading. Include years containing only annual fragments. Show optional **source** physical-Diary provenance only if 0054 actually records it; never infer ownership from that provenance or silently deduplicate annual fragments.
6. Preserve existing routes and selected-fragment deep links (`/diaries/{diaryId}/{year}/{month}[?fragment=id]`, day redirects, `/diaries/{diaryId}/pages/{pageId}`, and `/fragments/{fragmentId}`). A recommended new canonical route set is `/years/{year}` and `/years/{year}/{month}`; route decisions must be confirmed in Step 1. Existing physical-month views may continue to serve their original scoped content, rather than redirecting ambiguously to a larger calendar-month result.
7. Include only entities available in the current valid retained Reader projection. The existing contract has **no separate publication/visibility flag**: avoid claiming that a new filter for draft/private records exists. A missing month is 404/not available; an unready Reader projection continues to return 503. Explicit publication policy changes would require a separately approved contract change.
8. Support DATED TEXT, IMAGE, legacy MARQUEE compatibility and unavailable media states using existing sanitisation, typed image metadata, image-link safety and source-page rendering. Annual TEXT/IMAGE uses the corresponding annual-specific renderer and must handle unavailable Image metadata safely.
9. Maintain responsive design, calendar breadcrumbs, keyboard/pointer selection, browser Back/Forward behaviour, GET/HEAD semantics and existing HTTP security/cache behaviour.

## Boundaries and architecture

**In scope:** `diaries-web` calendar snapshot/index projection, routes/URL helpers, templates/CSS/JS, read-only provenance views, tests and Reader documentation.

**Out of scope:** PostgreSQL/JPA and annual-ownership migration (owned by 0054), rewriting MQTT topic families, moving DATED Fragments/Pages/Diaries, re-running accepted migrations, editing or authentication flows, and production deployment without authorisation.

Use canonical retained entity lookups (`diaries`, `pages`, `fragments`, `marquees`, `images`) and the existing atomic staged-replay mechanism. The responder retains authority; the Reader must not publish, mutate data or call RPCs.

## Acceptance criteria

- [ ] Calendar year/month home and URLs work; 1830 material appears under one year, including the January/February physical-volume boundary, when present in the retained dataset.
- [ ] Previous/Next published-month links traverse Diaries without loss of content or selection.
- [ ] Overlapping dated entries retain deterministic ordering, provenance and original scan/Marquee selection; no dropped or deduplicated valid fragments.
- [ ] Calendar-year-owned PREAMBLE/POSTAMBLE appears before/after the year's dated entries in stable order; annual-only years and optional grounded source provenance are supported; no owning Diary or invented Page/Marquee.
- [ ] DATED TEXT/IMAGE, legacy fallback, unavailable Images, links and sanitisation behave consistently in calendar and physical views.
- [ ] Old physical routes, source-page and selected-fragment deep links remain functional (including query, hash, Back/Forward and copy/paste).
- [ ] Year/month projection rebuilds correctly on MQTT replay/reconnect, tombstones and updates; 503/404 distinction and readiness are preserved; no database writes.
- [ ] Unit/HTTP/integration regression and representative desktop/mobile browser verification recorded under this feature directory.
- [ ] Git revisions, submodule status, test/build output, deployment/rollback receipts recorded when executed; production deployment and formal closure remain separately authorised.

## Status

**OPEN — IN PROGRESS; BLOCKED ON 0054.** Implement 0054 and accept its ownership/migration contract before implementing 0053. Then confirm route and annual-display decisions in Step 1. No application implementation, production deployment or acceptance test has been performed as part of the 2026-11-27 review.

See [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md).
