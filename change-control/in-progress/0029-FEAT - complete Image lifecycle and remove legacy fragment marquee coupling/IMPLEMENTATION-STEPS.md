# 0029-FEAT — Implementation steps (revised 2026-11-25)

**Scope:** final database integrity and reconciliation only. See [README.md](README.md) for exclusions, dependencies and acceptance criteria. Statuses below are planning items, **not claims of execution**.

## 1. Baseline and non-destructive preflight

- [ ] Record Git branch/revision, submodule revisions, uncommitted changes and current deployed client/responder/reader versions.
- [ ] Review existing 0024/0025 Image reconciliation/guard code, relevant migration evidence (including 0028), and the current database schema; avoid repeating accepted work.
- [ ] Create and execute read-only diagnostics for Fragment Page/type/Image consistency, Marquee uniqueness and Page agreement, catalogue-to-files checks and MQTT retained-state inventory.
- [ ] Archive raw outputs and an explicit discrepancy/exception list under this feature.

**Gate:** actual anomalies and missing safeguards distinguished from already-satisfied constraints.

## 2. Coherent integrity/reconciliation implementation

- [ ] Implement only missing report-only reconciliation coverage, with usable invocation, structured output, meaningful exit status and no mutation.
- [ ] Correct data exceptions only through an explicitly reviewed, reversible migration if required.
- [ ] Add/validate PostgreSQL Fragment and relationship constraints and corresponding JPA mappings.
- [ ] Remove redundant persistent `marquee.page_id` and dependent responder code only after proving it can be derived from Fragment and confirming compatible deployment/rollback strategy.
- [ ] Preserve `Fragment.marqueeId` contract where current consumers need it; preserve optional IMAGE Marquees and image-click links.
- [ ] Add focused regression tests for actual uncovered invariants or report errors.

**Gate:** integrated change is ready for a single consolidated verification cycle.

## 3. Consolidated verification and production migration

- [ ] Run appropriate responder/client/reader tests and compile/build checks after the integrated changes.
- [ ] Verify database postflight, Image file/catalogue integrity, retained-tree replay/comparison and edit/read smoke paths (MARQUEE, IMAGE, optional Marquee/link).
- [ ] For production: verify current restorable database backup and relevant Files-root backup; record compatibility and rollback method before any destructive SQL.
- [ ] Deploy as one controlled responder/schema update; archive service, database, MQTT and functional evidence. Repeat only affected tests after fixes.
- [ ] Record unresolved exceptions, acceptance decisions, Git commits and deployment revisions. Mark steps CLOSED only after evidence is accepted; move feature to `complete` only after formal approval.

**Gate:** production acceptance and formal closure decision.
