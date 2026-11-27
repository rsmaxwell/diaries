# 0054 Step 1 — source baseline and year-ownership contract (2026-11-27)

**Status: PARTIAL — source baseline inspected; live checkout/database/MQTT preflight and migration approval outstanding. Do not mark Step 1 CLOSED.**

## Evidence and precedence

- Inspected `diaries-sources-20261127-204710.zip` and overlaid the user-accepted `0054-calendar-year-editor-design-docs.zip` (documentation only). Neither bundle includes `.git` metadata; source revision/branch/status and matching deployment remain **unverified**.
- No access to the user's current PostgreSQL database, retained MQTT broker, or Windows/mango checkout from this source bundle. No migration, deployment, schema modification or runtime tests performed.
- Source review is static, not evidence of runtime success. The latest local checkout and database inventory must take precedence over this snapshot if newer.

## Existing code audit

| Area | Verified source behaviour | Required change |
| --- | --- | --- |
| Diary entry | `diaries-client/src/app/diary/diary.component.html` displays `<app-annual-editor>` whenever a Diary object exists, independently of whether `dataSource.data` has Pages | Keep physical-Diary entry and empty-Diary accessibility |
| Annual editor | `annual-editor.component.ts/html` exposes manual year and placement selectors, Quill TEXT and IMAGE controls, locks and reorder; its subscription and create operation bind `diaryId`; `ngOnChanges` resets year on Diary switch | Retain UI facilities; year-only group/subscription/CRUD; avoid overwriting explicit year on navigation switch |
| Client model | `annual-fragments.ts` filters topic and items by `(diaryId,year,placement)`; `annual-fragment-request.ts` requires Diary | Change keys and requests to `(year,placement)` |
| Responder model | `model/Fragment.java` has nullable Page and Diary links, `year/month/day` non-null; `FragmentOwnership` requires Diary for all placements | DATED: Page only; annual: year, placement, neither Page nor owning Diary |
| Responder RPC | `handlers/AddAnnualFragment.java` requires `diaryId`, stores it, uses `month=day=1` | Remove ownership input; enforce year-only annual creation |
| Publication | `dto/FragmentPublishDTO.java` currently requires Diary and emits `diaries/years/{diaryId}/{year}/{placement}/{id}` | Publish canonical year-only group with consistent retained deletion/replay |
| Ordering | `FragmentSequenceNormaliser.normaliseAnnual` and repository use Diary+year+placement | Group by year+placement, deterministic `(sequence,id)` and normalize across prior Diary groups |
| Reader | `model/FragmentItem.java` rejects annual without Diary; `projection/DiaryYearPlacementKey.java` keys by Diary+year+placement; `WebServer.java` renders annual within physical month pages | Accept year-only, index by year+placement, preserve physical URLs where meaningful until 0053 |

## Proposed frozen target contract for 0054 Step 2

1. DATED: `placement=DATED`, `page_id` required; Diary derives from Page. Year/month/day are a valid actual date. Annual: `placement in (PREAMBLE,POSTAMBLE)`, `year` in 1..9999, `page_id=NULL`, `diary_id=NULL`, no Marquee; no owning physical Diary. Multiple records per group allowed.
2. Canonical annual grouping is `(year,placement)`; order is `sequence ASC, id ASC`. Retain stable fragment ID, type, text, image/link, lock and version; preserve all former Diary associations in the migration manifest. Do **not** introduce `sourceDiaryId` in the deployed contract merely to retain the old owner; audit-only provenance is sufficient unless live inventory identifies a genuine product requirement.
3. Canonical retained annual topic proposal: `diaries/years/{year}/{placement-lowercase}/{fragmentId}`. Stable detail topic `diaries/fragments/{id}` remains. No new topic family is introduced; instead the existing `diaries/years` family changes shape. Publisher and subscriber must be updated together, with explicit old-topic tombstones. DATED topic stays `diaries/dates/{year}/{month}/{day}/{id}`.
4. Annual `month/day`: choose **null** semantically in storage and new wire payload, not synthetic 1 January. Make entity, DTO and reader validation placement-aware; do not call `LocalDate.of` for annual rows. This is a proposed target choice, subject to actual schema inspection. Legacy 1/1 values may be accepted only by an explicitly bounded read transition; do not normalize annual as a DATED fragment.
5. Annual create/normalise/list by `year,placement`; update/delete/lock by stable `fragmentId` with server-side ownership validation; optional sequence normalization must target the complete year group. The editor's selected `diaryId` is UI navigation only; do not submit it in annual creation or infer provenance from it. An empty Diary can open the editor, manually select any year, and create annual material.
6. Reader during 0054 retains physical Diary routes and DATED content. An annual-only year must remain accessible via the editor and canonical MQTT collection even if the current physical Reader cannot display a month with no dates; calendar-first public navigation is 0053. Direct annual fragment resolution must not require an owning Diary.
7. Deployment compatibility: old Reader rejects missing `diaryId`; old client subscribes to old annual topics. Therefore **do not switch the responder to year-only publication while either old consumer is active**. Use coordinated client/Reader/responder rollout plus migration/replay, or implement and test an explicitly temporary dual-read bridge. At cutover remove old retained `diaries/years/{diaryId}/...` topics with tombstones; test reconnect/restart and stale topics. No production cutover before approval.
8. Migration: read-only inventory and independent backup first; write feature-local idempotent migration with dry-run, duplicate-sequence checks, orphan/ambiguous rows, pre/post counts, ID/content/lock/image checksums, former Diary mapping, and rollback (database backup plus retained topic inventory). Preserve DATED records. No destructive operations approved.

## Outstanding verification required to close Step 1

- **Checkout:** capture exact Windows Cygwin parent/submodule Git status, commit hashes and `.gitmodules`; compare changed source against this ZIP and any newer local work.
- **Database:** for each chosen environment, capture `information_schema`/`pg_catalog` column and constraint definitions for `fragment`, annual counts by `(year,placement,diary_id)`, duplicate sequences, null/invalid ownership, year-only candidate groups and counts of annual IMAGE/locks. Verify runtime DB connection and whether schema management is automatic.
- **MQTT:** retain a read-only inventory/count of `diaries/years/#` and representative `diaries/fragments/{id}` annual records (no sweeping deletions); validate publisher/subscriber/topic behaviour against deployment versions.
- **Prior work:** locate accepted 0029 records and cross-check assumptions; no 0029 directory was identified by name in this bundle's `change-control` tree.
- **Rollout & restore:** identify actual consumer build versions and a verified recent DB backup/restore path; record safe MQTT retained-state recovery and migration rollback method.
- **Approval gate:** confirm target schema, annual topic change, nullable month/day, audit-only provenance, exact migration inventory and rollback plan before advancing. Until then Step 1 remains OPEN.

## Read-only checkout commands (Windows 11 Cygwin terminal)

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
printf '\nPARENT\n'; git branch --show-current; git rev-parse HEAD; git status --short
printf '\nMODULES\n'; cat .gitmodules; git submodule status
for module in diaries-client diaries-responder diaries-web; do
  printf '\n%s\n' "$module"
  git -C "$module" branch --show-current
  git -C "$module" rev-parse HEAD
  git -C "$module" status --short
done
```

Do not run a migration or retained-topic cleanup as part of these checks. Live DB/MQTT commands must be tailored to the verified target connection and container names rather than guessed from the source bundle.
