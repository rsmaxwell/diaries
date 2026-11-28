# 0054-FEAT — Calendar-year ownership of annual fragments

## Change control

- **Type:** FEAT
- **Status:** IN PROGRESS — proposed 2026-11-27; not implemented
- **Priority:** Before 0053-FEAT
- **Primary components:** `diaries-responder`, `diaries-client`, `diaries-web`, PostgreSQL/JPA and canonical retained MQTT projection
- **Dependency:** Complete and verify 0054 before implementing calendar-navigation 0053.
- **Related:** 0053-FEAT (calendar-oriented public Reader); existing 0029 work is background only; avoid repeating accepted migrations.
- **Basis:** `diaries-sources-20261127-203046.zip` (source snapshot; no Git metadata)

## Problem

PREAMBLE and EPILOGUE are editorial content about a historical calendar year, not a physical volume. Currently `Fragment.diary`/`diary_id` owns annual fragments, `AddAnnualFragment` requires `diaryId`, and the Reader requires `diaryId` on annual retained records. When a year crosses physical Diaries (January/February 1830), year-level content is artificially split or tied to an arbitrary volume.

## Objective

Represent annual PREAMBLE and EPILOGUE as **calendar-year-owned Fragments**, independent of physical Diary/Page ownership. Preserve DATED fragments as Page-owned records and preserve existing fragment IDs, content, sequence, IMAGE references and locks. Allow the Reader and editor to handle a year as one logical annual section, and establish a stable contract consumed by 0053.

## Placement naming decision (2026-11-27)

The final annual placement vocabulary is **PREAMBLE / DATED / EPILOGUE**. **EPILOGUE** replaces the previously deployed `POSTAMBLE` enum/placement value, not just its on-screen label. The old string `POSTAMBLE` is a **legacy migration input only**, not a supported final application value. Coordinate the rename across PostgreSQL rows and CHECK constraints, JPA/Java enums, TypeScript types, RPC payloads, retained MQTT topics, Reader projections/templates, tests, and current operating documentation. A production inventory must confirm whether legacy rows exist; the development inventory on 2026-11-27 found zero. Preserve fragment IDs, text, images, order and locks. Migrate existing legacy values transactionally and reconcile old retained topics with tombstones; no permanent alias. Do not deploy a partial enum-only rename ahead of the 0054 integrated migration.

## Proposed model and contracts

1. Reuse `Fragment` for both DATED and annual material; do not introduce a parallel annual text object without evidence it is necessary.
2. `DATED`: `placement=DATED`, mandatory Page; physical Diary is derived via Page; real date remains authoritative. `PREAMBLE`/`EPILOGUE`: mandatory `year`, **no Page, Marquee or owning Diary**; `month/day` are not semantically meaningful. Maintain a valid transitional wire representation if necessary while keeping the data model unambiguous.
3. Define the authoritative year key and order: annual fragments indexed by `(year, placement, sequence, id)`; multiple preambles or epilogues for a year are supported. No arbitrary deduplication; do not enforce one-per-year unless explicitly approved.
4. Preserve **source provenance separately from ownership**, only when grounded in actual data. An optional `sourceDiaryId` may describe the originating physical Diary, but must not affect ownership or sorting. Do not simply rename the old owning `diaryId` without deciding and recording provenance semantics. For migrated annual material, preserve a traceable old `diary_id` mapping in the feature evidence/migration manifest regardless of whether a new provenance field is introduced.
5. Update JPA/database constraints and repositories, creation/update/delete/normalisation, locking, DTOs, validation and responder MQTT publication so year-owned annual fragments work without a Diary. Retain existing fragment topic identity and tombstone semantics; avoid new MQTT topic families unless justified.
6. Update editor annual creation/listing/editing/navigation to use year rather than Diary; retain Quill editing and lock behaviour where currently supported. Ensure annual-only years remain reachable.
7. Update `diaries-web` retained validation, year index/annual resolution and old fragment deep links for the new contract. During 0054 retain existing physical-volume Reader URLs wherever meaningful; no new calendar-first navigation (belongs to 0053).
8. Plan the compatibility order for publication and readers: ensure no window where a deployed consumer rejects all new annual records; use coordinated versions or a deliberately bounded dual-read transition and remove temporary scaffolding once safe. Explicitly plan retained replay of updated records and recovery of old records/tombstones.
9. Migration is **idempotent, backed up, auditable and reversible**: inventory annual records, detect anomalies/conflicting provenance and existing duplicate sequences, preserve original IDs/versions as appropriate, move annual ownership without changing DATED Page relationships, reconcile retained state, and produce counts/checksums and a rollback plan. No destructive production migration or deployment without explicit authorisation.

## Accepted editor navigation design (2026-11-27)

The editor **continues to be entered through a physical Diary**. On that Diary's page, expose an **Annual editorial content** panel or dialog (exact presentation can follow the existing component layout), with an explicit **calendar-year selector** and PREAMBLE/EPILOGUE selection. The physical Diary supplies navigation context and, where supported by actual dated content, suggested years. It **does not own or filter** the annual fragments.

- Identify annual fragment lists and create/update/delete/reorder/normalise operations by **calendar year and placement**, with fragment ID where an individual record is targeted. Do not substitute the currently selected `diaryId` as an ownership key. Preserve lock behaviour and current editing facilities, including Quill where already supported.
- Allow a user to **type/select a year manually**, even when the chosen physical Diary has no Pages, dates or DATED fragments. Creation and subsequent editing of an **annual-only year** must not require creation of a dummy Page, dated fragment or physical year association.
- When two physical Diaries cover one calendar year, opening the annual editor through **either Diary** and choosing that year shows and changes **the same shared annual fragment collection**, without cloning or implicit duplication. Switching Diaries must not change the underlying year-owned contents.
- Derive convenient year suggestions from actual data only. Do not derive a mandatory year from a Diary title, filename or first Page; do not restrict the editable year set to years occurring in the selected Diary.
- A compact/collapsible panel or separate dialog is acceptable; keep the existing physical-Diary-first workflow, rather than introducing a global calendar-first editor. The final UI choice must preserve discoverability and empty-Diary use.
- Keep any optional `sourceDiaryId` strictly informational/auditable. The Diary through which a user *happens* to enter the editor must not silently become annual-fragment provenance or ownership.

This editor decision is **in scope for 0054**, not 0053. The public Reader remains calendar-first under 0053 after 0054's data and editor contract has been accepted.

## Boundaries

**In scope:** persisted annual ownership, DTO/RPC/MQTT representation, client annual editing and list views, Reader compatibility, one-time migration tools and integrated tests.

**Out of scope:** 0053 calendar navigation/route redesign; rewriting dated archival ownership; new editorial publishing policy; bulk image catalogue migrations; unrelated backup/Ansible changes.

## Acceptance criteria

- [ ] Annual Fragment creation, editing, normalisation, locking, deletion and MQTT publication work using **year alone**, with no owning `diaryId` or Page/Marquee.
- [ ] DATED fragments still require valid Page ownership, and are unaffected in rendering, editing and MQTT projection.
- [ ] Multiple annual fragments per year, both placements, annual-only years and content spanning two physical Diaries behave deterministically.
- [ ] From a physical Diary page, annual editing can explicitly select any calendar year (including without dated Pages); opening the same year from either of two physical Diaries edits the same shared PREAMBLE/EPILOGUE records. No annual CRUD operation requires the navigation Diary as owner.
- [ ] Migration inventory/receipts show no lost IDs/text/IMAGE links/locks and map all former annual Diary associations; repeat runs are safe, anomalies are reported not silently discarded.
- [ ] Existing editor and Reader deep links remain meaningful, including annual `/fragments/{id}`; physical volume links and provenance behave under a documented compatibility policy.
- [ ] A compatible deployed Reader accepts new retained records; replay/reconnect, update, delete/tombstone and recovery cases pass.
- [ ] Schema/RPC/DTO/Reader/unit and end-to-end regression results, revisions, deployment and rollback evidence are recorded under this feature.
- [ ] Only after 0054 is accepted as complete may 0053 implementation use year-owned annual fragments as its baseline.

## Status

**IN PROGRESS — DESIGN/TERMINOLOGY UPDATED; IMPLEMENTATION NOT STARTED.** Implementation gates and evidence are in [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md). 0053 stays independently IN PROGRESS but is blocked on this feature's accepted completion.
