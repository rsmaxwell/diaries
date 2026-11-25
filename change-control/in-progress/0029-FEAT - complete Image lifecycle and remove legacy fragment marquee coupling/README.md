# 0029-FEAT — Final Fragment integrity and reconciliation

## Type / status / history

- **Type:** Feature
- **Status:** In progress
- **Priority:** High
- **Opened:** 2026-09-08
- **Scope revision:** 2026-11-25. Original Image lifecycle/legacy Marquee coupling history remains in Git; existing feature directory name stays unchanged for traceability.
- **Approved model:** Hybrid physical Page and Diary-year ownership, replacing the earlier all-Fragments-must-have-a-Page decision. See `ARCHITECTURE.md` and `reports/APPROVED-HYBRID-DIARY-YEAR-FRAGMENT-MODEL-20261125.md`.

## Objective

Complete and enforce the final **TEXT/IMAGE** content model and **PREAMBLE/DATED/POSTAMBLE** placement, reconcile legacy data with the actual ownership semantics, remove redundant Marquee Page persistence, and provide repeatable, safe reconciliation of PostgreSQL, image catalogue/files and retained MQTT state. Preserve accepted 0024/0025/0028/0051 Image features rather than rebuilding them.

## Authoritative target model — approved 2026-11-25, not yet deployed

A Diary is a physical book **and** a digital edition. It has physical Pages and calendar-year editorial sections. Every Fragment has:

- A non-null `type`: **`TEXT`** (transcription, highlights, front matter and commentary) or **`IMAGE`** (occurrence of a Catalogue Image). The old `MARQUEE` type is replaced by `TEXT` throughout PostgreSQL, responder, editor, public reader and retained MQTT.
- A non-null `placement`: **`PREAMBLE`**, **`DATED`**, **`POSTAMBLE`**, independent of its content type.
- A stable ordering/sequence in its appropriate group and validated diary/year/date identity.

| Placement | Required ownership | Page relation | Marquee | Rendering |
|---|---|---|---|---|
| `DATED` | Physical Page, which determines Diary | Non-null | Optional 0..1 | Within normal date heading |
| `PREAMBLE` | Explicit Diary + calendar year | Null | None | Before first dated heading that year |
| `POSTAMBLE` | Explicit Diary + calendar year | Null | None | After last dated entry that year |

Ownership is **exclusive**, not a nullable Page with ambiguous meaning. A year-level Fragment must have an unambiguous, validated **Diary association** in persistent storage (e.g. explicit `diary_id`) as well as `year`; a year number alone does not identify a Diary, and one Diary can span multiple years. `DATED` Diary ownership is derived from its Page. Audit the current schema and existing date/diary lookup and choose the minimal stable contract and corresponding constraints before coding.

Both TEXT and IMAGE can occur in any placement; only DATED Fragments may have a Marquee, because a Marquee locates content on a scanned Page. A DATED Fragment may have **no** Marquee (e.g. added commentary or inserted Image). A Marquee belongs to its Fragment; its Page derives from the Fragment's Page and `marquee.page_id` must be retired after compatible migration. Existing retained `Fragment.marqueeId` may continue as a derived field for consumers.

An IMAGE Fragment has a required catalogue Image reference. The **Catalogue Image** owns independently optional caption and alt text; the **IMAGE occurrence** owns an independently optional HTTP(S) click-through link. Caption and link are independent, and may coexist. Keep explanations specific to a particular occurrence as separate TEXT Fragments rather than inventing a Fragment caption.

### Annual reading order

For each Diary and calendar year, show ordered PREAMBLE content (no date heading), then DATED Fragments under date headings in established page/fragment order, then ordered POSTAMBLE (no date heading), before the following year's preamble. Do not invent January/December dates, silently place annual material under 1 January, or put Page-less Fragments in the Page's fragment list. The editor and public reader must use the same semantics, and support editing annual content without a selected physical Page.

### Initial content disposition — reviewed, not yet migrated

Production 2026-11-25 read-only diagnostics identified **11** Page-less Fragments. All have non-empty HTML and none is among the **71** recorded 0028 migration source Fragments. Proposed approved treatment:

| Fragment IDs | Destination placement | Diary/year or Page | Notes |
|---|---|---|---|
| 1, 2, 3 | `PREAMBLE` | Verified Diary covering 1828; year 1828 | Annual highlights/title/front matter; maintain order; simplify decorative HTML retaining text and useful links |
| 387 | `PREAMBLE` | Verified Diary covering 1829; year 1829 | Annual highlights |
| 806 | `PREAMBLE` | Verified Diary covering 1830; year 1830 | Annual highlights |
| 1177 | `PREAMBLE` | `diary-1831`, year 1831 | Annual highlights |
| 1563, 1564 | `PREAMBLE` | `diary-1832`, year 1832 | Highlights and introduction; preserve content |
| 1926 | `PREAMBLE` | `diary-1834`, year 1834 | Annual highlights |
| 1738 | `DATED` / `TEXT` | Candidate Page 1005 (`img3018`), 1832-06-27 | Significant commentary, no Marquee; preserve |
| 2061 | `DATED` / `TEXT` | Candidate Page 1078 (`img2706`), 1834-05-14 | Historical link; preserve |

These are **migration targets**, not verified applied changes. Existing annual Fragments are already Page-less; do **not** assign them artificial Pages. Candidate Pages for the two DATED exceptions still require guarded preflight. The 49 extra development Page-less Fragments predominantly contain legacy image HTML; reconcile them against 0028 acceptance and actual catalogue Image Fragments before any deletion/repair. No actual POSTAMBLE records exist yet; use synthetic tests.

The development-only correction of 22 NULL-type Fragments associated with matching Marquees to `MARQUEE` was completed and verified on 2026-11-25. Production had **zero** analogous missing-type-with-Marquee rows, so no equivalent correction was needed. This is historical evidence, **not** final TEXT migration or MQTT publication.

## In scope

1. **Data preflight and disposition:** record actual Git/deployment states, constraints, Fragment type/placement/Page/Diary/year/sequence anomalies, 0028 provenance, and retained MQTT state; safely classify Page-less and legacy HTML Fragments without losing content.
2. **Coordinated schema/contract implementation:** implement type and placement enums and validated ownership; persist year-level Diary association; update responder RPCs/publications/normalisation, Angular editor/date-grouping, public reader projection, Java/TypeScript contracts, and test fixtures together. Existing ordinary records default to `DATED` only when they genuinely belong to a Page; classify approved annual exceptions first.
3. **Final integrity:** require valid `type`, `placement`, owner, year and IMAGE reference; constrain DATED to Page ownership and PREAMBLE/POSTAMBLE to Diary/year ownership with null Page; disallow Marquees for annual Fragments and permit 0..1 for DATED; retire persistent Marquee `page_id` after validating derives/rollbacks. Add service-level checks where PostgreSQL CHECK cannot enforce cross-table invariants.
4. **Operational reconciliation:** reuse existing image protections and report-only Image reconciler; fill verified gaps in reports for DB-to-files metadata/checksums, Fragment/Marquee ownership and retained MQTT object comparison/replay. Reporting must not silently repair production state.
5. **Consolidated regression and deployment:** validate ordering, source-page selection and no-date-heading annual sections, mixed years, POSTAMBLE synthetic fixture, Catalogue caption/link independence, lock/edit flows, old retained-state cleanup, backup/rollback compatibility, and production pre/postflight.

## Out of scope

- Reimplementing existing Image authoring/protection, or repeating accepted 0028 migrations for their own sake.
- Deleting meaningful editorial/legacy records, guessing Diary/Page associations, or automatically overwriting Image files.
- Adding Fragment-level captions, additional Fragment types, or fabricated dates for annual sections.
- Removing derived `Fragment.marqueeId` solely as a cleanup exercise.

## Acceptance criteria

- [ ] Complete read-only preflight and reviewed disposition of all Page-less/legacy records, with production/development differences recorded.
- [ ] Exactly `TEXT` and `IMAGE` active Fragment types; only `PREAMBLE`, `DATED`, `POSTAMBLE` active placements, enforced in database and application.
- [ ] All `DATED` Fragments have a valid Page and its Diary; all PREAMBLE/POSTAMBLE have a validated explicit Diary/year owner, **no Page, no Marquee**, with appropriate conditional constraints.
- [ ] Introductory 1828 Fragments 1/2/3 and 1832 Fragments 1563/1564 display *above* their 1 January date headings without being Page-associated. Other approved annual highlights likewise display in correct Diary/year; all links/text preserved.
- [ ] `DATED` 1738 and 2061 retain content on verified Pages and render normally without a Marquee.
- [ ] Catalogue owns caption/alt text; IMAGE occurrence independently owns optional image link; optional DATED Marquee works for both TEXT and IMAGE.
- [ ] `marquee.page_id` ceases to be independently authoritative; no invalid Marquee-to-Fragment/owner relationships remain.
- [ ] Annual ordering works across year boundaries; synthetic POSTAMBLE appears after final dated entry and before following year's PREAMBLE; editor and reader agree.
- [ ] PostgreSQL, Image catalogue/files and retained MQTT states reconcile with repeatable non-destructive reports, correctly handling annual Fragments without Page-derived topics.
- [ ] Development regression and controlled production migration, backup/rollback, compatibility, replay, postflight and GUI acceptance evidence are archived.
- [ ] Feature formally closed only after owner acceptance; historical evidence retained under parent change-control feature directory.

## Deployment / rollback

Do not run destructive production SQL solely from this documentation. Record existing image/DB backups and restoration capability before schema modifications. Coordinate schema, responder, editor and reader to avoid incompatible intermediate MQTT types or ownership. Prepare a guarded, reproducible SQL migration and rollback with explicit original-row evidence, reconcile retained topics, and test real annual content plus a synthetic POSTAMBLE. See [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md).
