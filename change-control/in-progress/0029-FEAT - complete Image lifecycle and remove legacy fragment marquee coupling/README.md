# 0029-FEAT — Final database integrity and reconciliation

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-09-08

## Scope revised

2026-11-25 — narrowed following review of the 2026-11-25 Diaries source bundle. This revision supersedes the original broad Image lifecycle / legacy Fragment–Marquee coupling implementation scope; the original intent remains traceable in Git history. The feature directory name is retained for continuity until formal closure.

## Objective

**Finish the database integrity and operational reconciliation work left after the direct Fragment-to-Page ownership and Image changes.** Detect and resolve actual data inconsistencies, enforce defensible database constraints, and provide repeatable, read-only reconciliation evidence across PostgreSQL, the Image catalogue/files and retained MQTT objects.

This is **not** another Image authoring, embedded-image migration, or client/reader contract redesign feature. Prefer existing 0024/0025 Image safeguards and reconciliation code. Do not repeat previously accepted migrations or testing solely because they were listed in the original 0029 plan.

## Current baseline and outstanding questions

Source inspected: `diaries-sources-20261125-091848.zip` (2026-11-25). This is source-level evidence, not a live production database or MQTT inspection.

- Fragment has a direct `page` relation; its JPA mapping currently specifies `@ManyToOne(optional = true)` with `@JoinColumn(name = "page_id")`.
- Fragment `type` is mapped without a `nullable = false` declaration.
- Marquee has a unique, non-null Fragment relation but still declares a separate `page` relation mapped to `page_id`.
- `ImageReconciler` exists under responder migration0024, and Image deletion/catalogue guards already exist. Determine whether these cover the operational reconciliation requirement before implementing anything new.
- Final database constraints, stored data, schema migrations and retained-state correctness require evidence from the actual intended environment; do not infer their status from JPA annotations alone.
- The 0028 migration dispositions and any accepted later Image-related feature evidence must be consulted before finalising constraints or treating exceptions as defects.

## In scope

### A. Database integrity

1. **Read-only preflight first.** Inspect actual schema constraints and record counts and offending rows for missing/invalid Fragment Page, Fragment type, Image references, and Marquee-to-Fragment relationships. Compare the Marquee Page, where present, against `marquee.fragment.page`; identify mismatches before changing schema.
2. Resolve any identified anomalies through a documented, reversible procedure; preserve historical migration dispositions and accepted exceptions. Never silently discard records or alter Image content.
3. Enforce validated PostgreSQL constraints for required Fragment Page/type and applicable foreign keys/uniqueness, with corresponding JPA mapping updates. Confirm permitted Fragment types and IMAGE/MARQUEE rules with the current model; IMAGE may have **zero or one Marquee**, and its optional validated image-click link must remain supported.
4. **Retire redundant persistent `marquee.page_id` only if live preflight confirms the relationship is derivable from Fragment and all current responder SQL/JPA/handlers/publishers have been updated.** Treat this as schema integrity cleanup, not a new ownership migration; preserve the direct Fragment Page model already in use. Stage the application/schema change compatibly and document rollback requirements.
5. Keep `Fragment.marqueeId` in retained/client/reader payloads where required. It may be documented as a derived/indexed field. Removing it is outside this feature absent a separately approved contract change.

### B. Operational reconciliation

1. Reuse and assess existing Image reconciliation support. Supply a repeatable **report-only** operation or script if missing, with documented invocation and output suitable for archival under this feature.
2. Report, without mutation: catalogue entries with missing files, untracked files within the defined catalogue scope, metadata/checksum drift, broken Image references, inconsistent Fragment/Marquee/Page relations, and relevant retained-topic mismatches where comparison is supported.
3. Define source of truth and expected coverage. Reconcile PostgreSQL entities against retained MQTT topic-tree state, including stale/orphaned topics and a controlled replay validation. Distinguish expected transient propagation delay from persisted mismatch.
4. Provide clear counts, specific identifiers, explicit exceptions and a nonzero failing exit code for unresolved problems. If fixes are needed, document them separately; **no automatic delete, overwrite or production repair** in report mode.

### C. Verification and evidence

- Verify existing referenced-Image deletion and file-protection safeguards as **regression requirements**, not new implementation goals.
- Run consolidated responder/client/reader tests appropriate to the changed interfaces and any schema migration; verify MARQUEE and IMAGE fragments, optional IMAGE Marquees and links, and retained replay.
- Preserve preflight/postflight data, schema diffs, service and MQTT diagnostics, smoke results, deployment versions, backup/restore evidence and rollback decision in this feature's `evidence/` and `reports/` directories.
- Before any destructive schema migration on production, verify compatible DB backup/restore capability and applicable Files-root recovery points. No destructive backup/snapshot changes are authorised by this feature.

## Explicitly out of scope

- Re-implementing the already adopted Fragment-direct-Page ownership model or migrating Page ownership through Marquee again.
- Building a new Image catalogue, Image authoring UI or replacing implemented 0024/0025 deletion/overwrite protections.
- Repeating 0028 embedded-image conversion or previously accepted migration rehearsals.
- Removing `Fragment.marqueeId` or changing client/reader/MQTT contracts solely for tidiness.
- General Image replacement/versioning functionality, unless a separately evidenced defect is approved.
- Silent automatic repair/deletion of catalogue/files/MQTT state.

## Acceptance criteria

- [ ] Preflight inventory of actual database constraints and relevant rows is archived; 0028 exceptions are reconciled or documented as explicit blockers.
- [ ] Required Fragment Page/type, Image reference, and Marquee–Fragment integrity is enforced by appropriate validated constraints where feasible; remaining cross-row rules have documented service-level checks.
- [ ] No mismatched/independently authoritative Marquee Page relationship remains. If `marquee.page_id` is removed, dependent application code and migrations/rollback notes are updated and tested.
- [ ] A repeatable read-only reconciliation report identifies catalogue/file issues and broken database relations, and retained-state comparison/replay is demonstrated.
- [ ] Existing Image deletion/file guards and optional IMAGE Marquee/link behaviour pass regression verification.
- [ ] Development integration, production preflight/postflight, backup compatibility, controlled deployment and smoke evidence are recorded and accepted.
- [ ] No unresolved discrepancy is silently suppressed or repaired.

## Implementation plan

See [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md). The work is organised into one coherent implementation and consolidated verification sequence, not artificial per-step deployments.

## Deployment and rollback

Validate all proposed schema changes against the current deployed and rollback-target application versions before deployment. Constraint tightening or dropping `marquee.page_id` can make an old responder incompatible; retain a compatible application/DB rollback pair and verified backup. Run the database change and responder update as one controlled operation, followed by retained-state reconciliation and application smoke tests. Production approval is required for destructive migration; feature closure requires recorded acceptance.
