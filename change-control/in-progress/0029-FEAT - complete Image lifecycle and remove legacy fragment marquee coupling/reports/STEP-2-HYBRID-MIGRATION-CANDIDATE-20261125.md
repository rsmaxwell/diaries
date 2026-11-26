# 0029 Step 2 — guarded database migration candidate (2026-11-25)

**State: CANDIDATE, NOT EXECUTED.** Based on the authoritative 2026-11-25 12:32 Diaries bundle. ZIP package deliberately contains no deployment automation and must not be applied to a live database yet.

## Scope

The transactional SQL performs the production-shaped data conversion for the **reviewed** 11 Page-less records, converts `MARQUEE`/NULL to `TEXT`, establishes explicit Diary/year ownership and conditional Page ownership, and introduces database checks, FK and indexing. Nine editorial records become PREAMBLE; 1738 and 2061 become DATED on Pages 1005 and 1078. No content is deleted or transformed. POSTAMBLE is supported in constraints but has no existing rows. The 49 additional development-only embedded-image HTML records are **intentionally rejected** by the exact row-set guard until the 0028 disposition is established.

## Critical integration requirements

- This is **not** a deployable standalone change. Current responder repositories do not read/write `diary_id` or `placement`, existing clients still emit/consume `MARQUEE`, and the reader ignores Page-less fragments. Run only alongside a tested application/contract migration with a restorable backup.
- **Do not drop `marquee.page_id` yet**: current Java code still reads/writes that column. Retire it only together with responder repository/handler changes.
- Current retained `diaries/dates/<year>/<month>/<day>/<id>` aliases cannot be reused for PREAMBLE/POSTAMBLE. Replace with appropriately scoped Diary/year/placement retained topics and explicitly delete old aliases; retain `diaries/fragments/<id>` identity topics. Verify reader and editor subscriptions and startup replay before rollout.
- Existing draft Step 2 no longer uses a blanket `fragment.page_id NOT NULL`; only DATED requires a Page. Diary FK is explicit for all Fragments, and its consistency with Page's Diary is validated before commit (cross-table consistency also needs responder write validation).
- `fragment.year` for annual Fragments must be the target year; `month/day` are historical placeholders for annual records, and must not be used to emit dated entries. Dates should be nullable for annual content in a future coordinated schema update if the permanent contract no longer needs them; this candidate deliberately preserves existing columns/data.
- TEXT with optional Marquee and IMAGE with optional Marquee are valid. Catalogue-owned captions/alt text remain unchanged.

## Validation and rollback

The candidate SQL aborts if the exact 11 Page-less IDs or their expected dates/types are absent, if any annual Fragment has a Marquee, or if resulting ownerships are inconsistent. Production table versions and actual data must be rechecked immediately before use. The paired rollback is a **limited baseline reversal**, not a substitute for PostgreSQL backup: it rejects POSTAMBLE or extra annual content and must not run after further writes. Capture a current database backup and rollback/replay plan, test on a production-shaped restored development DB, then deploy components and schema together.

**Next integrated implementation:** complete Java responder repository/entity/DTO and MQTT topic contract changes, Angular authoring/dayview and reader projection, then consolidate tests. No acceptance gate is closed by this package.
