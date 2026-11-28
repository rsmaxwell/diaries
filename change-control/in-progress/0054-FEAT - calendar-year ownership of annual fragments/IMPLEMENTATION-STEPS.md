# 0054-FEAT — Implementation steps

## Step 1 — Verify baseline and freeze year-ownership contract

**CLOSED — 2026-11-27.** Evidence, design, compatibility and rollback contract: [Step 1 baseline and contract](reports/2026-11-27-step-1-baseline-and-contract.md). Verified Git baseline, development/production database inventories, both MQTT retained annual inventories, production schema-2 backup publication and mars verified retained history. Existing responder startup reconciliation is the agreed MQTT rebuild/rollback mechanism; a separate MQTT snapshot/restore tool is **not** required. No application or production changes have been made as part of this step.

**Gate:** baseline and schema/RPC/retained compatibility contract recorded; migration inventory, backup and rollback approach agreed — **CLOSED**.

## Step 2 — Implement integrated calendar-year ownership and EPILOGUE

**CLOSED — 2026-11-28 for the integrated development implementation gate.** Accepted Editor/Reader browser behaviour, annual and DATED Save failure/retry, shared drag-and-drop, EPILOGUE deletion and Windows Angular regression (`289/289` unit tests and successful build) are documented in [Step 2 acceptance](reports/2026-11-28-step-2-acceptance.md). The original Step 2 implementation review predates this acceptance. **No production migration/deployment is claimed.** Step 3 still requires consolidated Java responder and Reader verification, retained-MQTT/SQL evidence, cutover readiness, and explicit production authorisation.

- Verify checked-out branch, parent/submodule revisions and working-tree changes before modifying code; treat the latest user source bundle as the inspection baseline and preserve local work.
- Change Java entity, JPA constraints/migration, DTOs, repositories, RPC handlers, locks and ordering so annual fragments belong to calendar year and placement, with `diary_id`, `page_id`, `month` and `day` null. Keep DATED fragments Page-owned and unaffected. Preserve IDs, version, sequence, content/images and locks.
- Rename every application/API/protocol/constraint use of `POSTAMBLE` to `EPILOGUE`, with legacy values recognised by the migration only. Final enum/DTO/RPC/MQTT paths accept `PREAMBLE`, `DATED`, `EPILOGUE`.
- Produce canonical retained annual topics `diaries/years/{year}/{placement-lowercase}/{id}` in the database-derived topic map used by startup synchronisation. Reuse the existing `Synchronise.java` publish/orphan-tombstone logic; do **not** create a separate export/restore tool. Keep fragment-identity and DATED topics consistent.
- Update Angular Annual editorial content on the physical Diary page, with explicit year and PREAMBLE/EPILOGUE selection, including for empty Diaries. Two physical Diaries covering one calendar year must edit the same annual objects. Preserve Quill, IMAGE, lock and ordering behaviour.
- Update Reader parsing, indexing and views for year-owned annual fragments without implementing the calendar-first URL/navigation changes reserved for 0053. Retain viable existing URLs.
- Add an idempotent feature-local migration script and dry-run/audit manifest under this feature directory; preserve legacy Diary/year/date/placement provenance as evidence. Use PostgreSQL transaction and validate constraint transition. No one-off Playbooks role changes.
- Implement cohesive regression coverage for annual-only years, two Diary entry points, EPILOGUE, locks, order, image/text, RPC replay, retained old-topic cleanup and idempotent migration. Consolidate tests after the integrated change.

**Gate: CLOSED for development implementation and Angular/browser verification** — outstanding cross-component, migration/reconciliation and release checks are tracked in Step 3; no production changes implied.

## Step 3 — Consolidated integration, production cutover and handoff

**OPEN — 2026-11-28.** Development integration PASS: Angular 289/289 and build, Java responder/Reader builds, PostgreSQL annual ownership, retained MQTT reconciliation, deletion checks and Reader verification for 1828/1832/1834. See [Step 3 acceptance and production preflight](reports/2026-11-28-step-3-development-acceptance-and-production-preflight.md). **Production preflight, outstanding special-case integration checks, deployment, rollback evidence and release acceptance remain OPEN.** Record any responder startup Paho shutdown exception separately; no production deployment without explicit authorisation.


- Verify source and build/test Angular, responder and Reader from the inspected checkouts; exercise development PostgreSQL/MQTT with the migrated model.
- Test responder restart from a legacy retained-topic tree: new canonical topics are published, old `diaryId/year` annual topics are tombstoned, fragment identities and DATED records persist, and a second restart converges. Test reverse reconciliation after restoring a pre-migration local database and compatible old responder.
- Browser-check a brand-new empty physical Diary with manual annual year entry; create/edit/delete PREAMBLE and EPILOGUE; verify two Diaries reaching the same year observe one shared set; test existing physical Reader links and annual content.
- Before any authorised production cutover, capture current revisions/image tags and a fresh verified *pre-cutover* matching PostgreSQL/files recovery point; preserve an original-row manifest. Coordinate client, responder and Reader rollout so incompatible protocol versions do not overlap. Let the responder rebuild MQTT on startup.
- Capture builds, SQL checksums, logs, MQTT before/after topic inventories, browser results and rollback verification under this feature's `evidence/` and `reports/`. Do not claim deployment without evidence; do not repeat previously accepted expensive restore tests without a reason.
- Document the final annual fragment contract for 0053 (calendar-first Reader navigation), which is sequenced **after** 0054. Formal feature closure requires acceptance and is separate from Step 1 closure.

**Gate:** accepted integrated functionality and tested recoverability, with production deployment explicitly authorised before executing.
