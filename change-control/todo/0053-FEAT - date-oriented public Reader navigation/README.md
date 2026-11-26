# 0053-FEAT — Date-oriented public Reader navigation

## Change control

- **Type:** FEAT
- **Status:** TODO — accepted future enhancement; implementation not started
- **Priority:** Normal
- **Opened:** 2026-11-26
- **Owner:** Diaries application (primarily `diaries-web`)
- **Related:** 0029-FEAT (hybrid physical Page / Diary-year Fragment ownership)
- **Identifier:** 0053 is the next identifier known from the current 0052 work; verify against the full current change-control tree before applying if any newer item has been opened.

## Problem

The public Reader currently presents months underneath the *physical Diary* containing their source Pages. The first physical volume covers 1828, 1829 and **January 1830**, whereas February–December 1830 belong to the next physical volume. A reader looking for the year 1830 must navigate two separate physical volumes, even though the entries are one chronological sequence.

## Objective

Make **historical calendar year and month the primary public Reader navigation**, independent of the physical volume holding the entry. Keep the physical-volume view and original source Pages available as archival provenance, and preserve the existing database/MQTT/editor ownership model.

## Requested behaviour

1. Public Reader landing page offers a chronological **year index** and each year offers its available months in calendar order. Readers should not need to identify the source physical volume first.
2. **January 1830** from `diary-1828-and-1829-and-jan-1830` and **February–December 1830** from `diary-1830` appear together under calendar **1830**, with continuous Previous/Next month navigation across the physical-volume boundary.
3. Month content aggregates relevant DATED Fragments across physical Diaries for the requested calendar month, ordered by historical date then stable source sequence; do not invent missing months or silently deduplicate legitimate distinct entries.
4. For every entry retain provenance and working links to its **physical Diary**, **scanned Page**, optional **Marquee**, and the corresponding editor/source view. Selecting an entry must continue to display and highlight its actual scanned Page.
5. Display annual **PREAMBLE** before the first dated entry of its associated Diary/year, and **POSTAMBLE** after that Diary/year's final dated entry. If multiple physical Diaries contribute annual content to one calendar year, preserve Diary association, stable ordering and clear provenance rather than merging text ambiguously.
6. Keep an accessible **physical diaries / volumes** browsing route for archival use. Existing volume/month URLs and deep links must continue to work or redirect unambiguously, with fragment selection intact.
7. Reader shows only published/available material; distinguish an unavailable month from an empty result, without exposing private/editor-only controls.
8. Responsive desktop/mobile experience, with clear month and year breadcrumbs and navigation.

## Scope and boundaries

**In scope:** `diaries-web` navigation/routes, calendar-year/month projection over existing retained MQTT `diaries/#` state, reader templates, source-link preservation, integration and regression tests, documentation.

**Out of scope:** changing PostgreSQL ownership or physical Page mappings, moving Fragments between physical Diaries, modifying catalogue Images, changing the Angular editor, re-running 0029 migration, or introducing a new persistence model unless analysis reveals a necessary reader-only index. Production deployment is separately gated.

**Architectural constraint:** Physical Diaries and Pages remain source-of-truth provenance. Calendar organisation is a **read-only view/projection**, not a replacement for storage ownership. Preserve 0029 `TEXT`/`IMAGE` types and `PREAMBLE`/`DATED`/`POSTAMBLE` semantics.

## Acceptance criteria

- [ ] Calendar landing page lists available years and months in chronological order, with 1830 January–December appearing under a **single year** when published.
- [ ] January→February 1830 Previous/Next navigation crosses physical volumes without losing reader context.
- [ ] Deep links to month and Fragment remain usable, with the correct scanned Page and Marquee selection.
- [ ] 1828 and 1829 introductory material remains above dated entries; 1830 handling is correct even where annual sections originate in a different volume.
- [ ] TEXT and IMAGE content, captions, links, highlights, source selection and rendering safety work across volume boundaries.
- [ ] Multiple source Diaries with overlapping months or dates are handled predictably, with visible provenance and no accidental content loss/duplication.
- [ ] Year/month data updates correctly after MQTT retained-state replay or responder restart, with no new database writes.
- [ ] Existing physical-volume browse route and key legacy deep links remain functional.
- [ ] Automated reader tests, representative browser checks and a consolidated regression pass, with accepted evidence in this feature directory.
- [ ] Production deployment and formal closure require separate authorisation; mark steps CLOSED only after evidence accepted.

## Status / decision

**OPEN — TODO.** Feature record created only. No application code, MQTT, database, deployment or 0029 files changed.

See [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md) for the proposed substantial implementation chunks.
