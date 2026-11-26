# 0029-FEAT — Step 1 source baseline and read-only preflight handoff

**Date:** 2026-11-25  
**Status:** IN PROGRESS — no live database or MQTT inspection yet; this report is not acceptance of Step 1.

## Source provenance

Reviewed `diaries-sources-20261125-091848.zip`, generated 09:18:54 UTC, and the later 0029 documentation revision package `0029-FEAT-revised-integrity-reconciliation-docs-20261125.zip`. The source bundle predates the 0029 documentation revision; the revision package is authoritative for Step 1 requirements.

Source bundle `SOURCE-REVISIONS.txt` records:

- Parent: `fe6b69c7ce04bae073ec266a54bd8d2dd595338d`, `main`; at capture the 0029 relocation was **uncommitted** (`todo` deletion and untracked `in-progress`).
- Client: `1f470618fcd475d871ced79fe9752a99b1111240`.
- Responder: `7aa6296e0c675b3d315e9a46bb0dd70202a8cd55`.
- Reader: `6d1b289bc5a7983cbf36fe771f8c11dc4725813b`.
- No `.git` internals in bundle; verify current Windows checkout and deployment independently.

## Source-confirmed facts

1. `Fragment.java`: direct `Page page` relation is present but `@ManyToOne(optional = true)` and no nonnull `@JoinColumn` restriction. Its `type` has no JPA nonnull declaration; `image` association is optional. These mappings alone do **not** prove the live PostgreSQL schema or data are unconstrained.
2. `Marquee.java`: persistent `page` (`@JoinColumn(name="page_id")`) remains in addition to a non-null unique `fragment` one-to-one mapping. Check actual values and dependencies before proposing removal.
3. `FragmentType.java`: current declared types are `MARQUEE` and `IMAGE`.
4. `Image.java`: catalogue metadata contains canonical `relative_path`, 64-character lowercase hex `checksum`, positive dimensions and service-layer validation.
5. `ImageReconciler.java` under `migration0024`: already has `dry-run` and `apply` modes, CSV/JSON reports, checksum inspection and guarded catalogue insertions. **Do not use `apply` in Step 1.** Establish whether its existing dry-run already covers catalogue/files reporting before implementing a new reconciler.
6. `Migration0028ReviewedFragments.java` provides a separate one-off migration tool including `analyse` and `postflight`; historical evidence and accepted dispositions are not included as a complete `change-control/complete` tree in this source bundle. Do not rerun accepted migrations.

## Read-only database preflight

`tools/step1-database-preflight.sql` records live schema columns, validated constraints, indexes, totals and examples of exceptions for Fragment, Marquee and Image. It uses an explicit `READ ONLY` transaction; **it does not inspect filesystem files or MQTT**.

Suggested first execution: Windows Cygwin, against the existing `diaries-development-db` container. Use the exact commands given in the chat. Record stdout/stderr in `evidence/step-1/`. Do not run against production until the development query results and migration dispositions have been reviewed.

**Interpretation cautions:** A null type/page may be a documented unresolved 0028 exception. Optional IMAGE Marquee is valid; seeing an IMAGE with a Marquee does not imply an error. Checksums in the Image table alone do not demonstrate matching file contents. SQL exception detail queries limit output to 100; any nonzero totals warrant targeted full enumeration. The query references `image_link_url`; update it only if the live schema diverges after inspecting the schema inventory.

## Step 1 remaining checks

- Capture live Windows Git status, current deployed versions and submodule revisions.
- Run database preflight and review exceptions, actual validated constraints and retained `marquee.page_id` values.
- Locate 0028 accepted disposition/journal evidence; reconcile any deferred or intentionally retained content.
- Inspect operational access to 0024 Image reconciler in **dry-run only** and define safe files root/required inputs; capture catalogue-versus-files evidence.
- Inventorise retained MQTT topics and compare stable IDs/relationships with the database after settling any transient startup publication.
- Produce a final discrepancy list separating defects, expected migration exceptions and missing features.

**Step 1 gate: OPEN. No production changes or data mutations were performed during this source-only review.**
