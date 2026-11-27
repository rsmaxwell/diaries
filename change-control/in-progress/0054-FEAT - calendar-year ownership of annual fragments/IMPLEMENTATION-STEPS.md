# 0054-FEAT — Implementation steps

## Step 1 — Verify baseline and freeze year-ownership contract

**Progress (2026-11-27):** static source audit and proposed contract documented in [Step 1 baseline and contract](reports/2026-11-27-step-1-baseline-and-contract.md). **OPEN:** checkout revisions, live PostgreSQL/MQTT inventories, rollback validation and approval are outstanding.

- In Windows Cygwin at the **Diaries parent repository**, capture parent branch/revision/status, `.gitmodules`, submodule status and independent client/responder/web revisions. Compare with the 2026-11-27 bundle. Verify live database schema/annual row counts and current retained MQTT state before planning a migration; **do not assume the bundle is the deployed version**.
- Audit annual paths: `Fragment` JPA, `FragmentDBDTO`/`FragmentPublishDTO`, `AddAnnualFragment`, `UpdateFragment`, delete/lock, `FragmentSequenceNormaliser`, startup reconciliation, client service/dialogs/state, Reader `FragmentItem`/projection and HTTP links. Confirm how the existing physical Diary page opens the annual editor, including empty-Diary behaviour.
- Decide the precise year-owned shape and database constraints; preserve existing IDs and distinguish optional *source* Diary provenance from ownership. Determine how transitional `month/day` values are represented on wire and in the database. Decide ordering and potential duplicate sequences.
- Document rollout/version compatibility between responder, editor, Reader and MQTT retained payloads. Confirm relationship to old 0029 change-control work; reuse existing accepted evidence instead of redoing migrations.

**Gate:** baseline and schema/RPC/retained compatibility contract recorded; migration inventory, backup and rollback plan approved for the target environment.

## Step 2 — Implement integrated ownership change

- Change JPA schema/repository and DTO/model rules to make annual ownership `year + placement`, not `diary_id`. Preserve DATED Page ownership. Keep nullable `diary_id` only if it has a documented other purpose, or remove it from annual ownership after transition.
- Implement year-based responder CRUD, validation, lock, sequence normalisation and retained publication; retain stable IDs/topics/tombstones and atomic update behaviour.
- Update Angular annual editing/lists and links to year-based operations, maintaining existing rich-text and IMAGE behaviour. Keep annual editing accessible from the selected **physical Diary page** via a discoverable Annual editorial content panel/dialog; expose explicit calendar-year and PREAMBLE/POSTAMBLE selection. Use the Diary only as navigation context or a source of grounded year suggestions, never as ownership or filtering. Permit manual year entry for Diaries with no dated fragments; do not infer a mandatory year from a Diary title or create placeholder Pages. Opening the same year from two different Diaries must expose the same records. Do not populate `sourceDiaryId` merely from the navigation Diary.
- Update public Reader parsing/indexing/links to accept year-owned annual fragments while continuing to serve its existing physical routes safely. Do not implement 0053 routes here.
- Build a **feature-local**, idempotent migration tool under `tools/` with preflight inventory, dry-run, transaction control, audit output and recovery. Do not add one-off migrations to permanent Playbooks roles. Test against disposable/appropriately backed-up data first.
- Add tests for year-only annual fragments, annual-only years, multiple pre/postambles, two Diaries in one year, all fragment kinds, sequence and lock update, protocol consistency, replay/tombstone, old URLs and idempotent migration. Include UI/service tests for explicit year selection from an empty physical Diary and for identical year collections reached through different Diaries. Implement as one coherent functional increment before consolidated regression.

**Gate:** integrated code and repeatable migration runbook ready; no production changes implied.

## Step 3 — Consolidated verification, release and handoff to 0053

- Run relevant client, responder and Reader tests/builds from verified checkouts; exercise a complete local system against compatible MQTT and PostgreSQL state. Verify editor create/update/delete, Quill, images, locking, Reader annual and dated links, retained replay and source provenance. Browser-check annual editing reached from a new empty physical Diary using a manually selected year, and the same year reached from two different physical Diaries (shared list and edits).
- Capture command output, row-level migration counts/checksums, test reports, versions, retained snapshots, browser checks and rollback receipts under `change-control/in-progress/0054-FEAT - calendar-year ownership of annual fragments/evidence/` or `reports/`.
- Deploy only when explicitly authorised, in the agreed safe component/migration order; check successful publication and rollback feasibility. Do not repeat unrelated accepted expensive testing.
- After accepted migration and verification, document the final annual payload/URLs/order for **0053 Step 1**. Request formal closure separately; do not mark CLOSED until accepted.

**Gate:** accepted year-owned annual fragment contract and verified integration. 0053 may then proceed.
