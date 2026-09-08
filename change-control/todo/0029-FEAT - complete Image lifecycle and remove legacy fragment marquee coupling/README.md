# 0029-FEAT - Complete Image lifecycle and remove legacy fragment/marquee coupling

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-08

## Summary

Complete operational Image lifecycle behaviour, validate the live migration, enforce final Fragment constraints, remove redundant persistent Page ownership from Marquee, and retire compatibility contract fields only after every application and retained-state path uses the target model.

This is the destructive contract stage. It must not be combined operationally with the first deployment of Image authoring or the 0028 legacy data conversion.

## Preconditions

- 0022–0027 application capabilities are deployed and stable.
- 0028 has recorded a disposition for every legacy embedded-image candidate.
- all Page ownership/type anomalies are resolved or explicitly documented as blockers.
- no deployed or rollback-target binary requires the columns or payload fields selected for removal.
- fresh database and Files-root backups have passed a restore rehearsal.

## Final Invariants

```text
Fragment.page_id is non-null and valid
Fragment.type is non-null and valid
MARQUEE => fragment.image_id is null
IMAGE   => no Marquee exists for the Fragment
non-null fragment.image_id => Image exists
Marquee.fragment_id is valid and unique
Marquee has no persistent page_id
catalogued files cannot be altered outside Image lifecycle operations
```

`KEEP_LEGACY` HTML from 0028, if any, is an explicitly documented rendering exception; it does not create a `Fragment.imageId` relationship on a MARQUEE Fragment.

## Image Lifecycle Completion

Retain and harden the protections introduced in 0024 and 0025:

- `DeleteImage` rejects referenced Images;
- generic file deletion cannot bypass Image ownership;
- catalogued files cannot be silently overwritten;
- deleting an IMAGE Fragment never deletes its Image;
- reconciliation reports missing files, untracked files, metadata drift and checksum drift;
- replacement, if supported, is an explicit versioned operation which recomputes MIME, dimensions and checksum and republishes retained metadata;
- partial filesystem/database/MQTT failure remains visible and recoverable.

Add periodic/admin reconciliation suitable for operational use, but do not let it silently repair or delete production data without an explicit apply mode and audit report.

## Final Database Migration

Preflight must prove all final invariants and reconcile counts against 0022/0024/0028 evidence. Add final constraints using PostgreSQL-safe staged practices where appropriate, such as adding foreign keys `NOT VALID`, validating them separately, and applying `NOT NULL` only after validation.

Remove `marquee.page_id` only after proving:

```text
marquee.fragment_id -> fragment.page_id
```

provides every required Page relationship and no application query still reads the old column.

Update JPA so Marquee contains only:

```text
id
fragment
x/y/width/height
version
```

Page/Diary context is derived through `marquee.fragment.page` wherever needed.

## Retained Contract Cleanup

Audit all deployed consumers before removing `Fragment.marqueeId`. If it is retained, document it as a denormalized compatibility/index field and define how replay verifies it. If removed:

- consumers derive Marquee by `Marquee.fragmentId`;
- old retained Fragment payloads are replaced/tombstoned deliberately;
- replay from PostgreSQL yields only the canonical shape;
- no mixed old/new retained tree can shadow database truth.

Do not remove an additive field merely for tidiness when an operational consumer still requires it.

## Production Runbook

1. Confirm exact deployed client, web and responder versions.
2. Disable writers and verify no edit sessions remain.
3. Take and verify database and Files-root backups.
4. Run final preflight and archive results.
5. Confirm 0028 disposition/journal reconciliation.
6. Apply safe constraints and validate them.
7. Deploy responder/JPA changes coordinated with dropping `marquee.page_id`.
8. Rebuild/replay retained state through the normal controlled process.
9. Compare database entities, retained topics and relationship diagnostics.
10. Smoke-test MARQUEE, IMAGE, missing-media and any KEEP_LEGACY case.
11. Record completion evidence and rollback decision deadline.

## Detailed Implementation Steps

- [ ] Add final Image reference and file/catalogue reconciliation reports.
- [ ] Decide and document Image replacement policy.
- [ ] Test DeleteImage and generic-file guards under concurrent operations.
- [ ] Reconcile all 0028 dispositions and unresolved exceptions.
- [ ] Write final integrity preflight and postflight SQL.
- [ ] Prove every deployed consumer uses `Fragment.pageId`.
- [ ] Enforce final Fragment Page/type/FK/check constraints.
- [ ] Refactor Marquee JPA/repository/DTO code to derive Page through Fragment.
- [ ] Drop `marquee.page_id` only after code/data preconditions pass.
- [ ] Decide and implement retirement or documented retention of `Fragment.marqueeId`.
- [ ] Clean stale retained messages through explicit replay/tombstones.
- [ ] Run responder, client and web tests/builds.
- [ ] Run a full database-to-retained-tree replay test.
- [ ] Execute the mixed-type end-to-end smoke dataset.
- [ ] Rehearse and then execute the production runbook.

## Acceptance Criteria

- [ ] All final database invariants are enforced or explicitly documented where cross-row validation remains service-level.
- [ ] Referenced Images cannot be deleted or overwritten through any supported operation.
- [ ] Reconciliation exposes missing/untracked/drifted files without silent mutation.
- [ ] `marquee.page_id` is absent from the final schema.
- [ ] No application or replay path relies on that column.
- [ ] Retained state exactly reflects database entities and relationships after replay.
- [ ] Every 0028 candidate has durable disposition evidence.
- [ ] Existing and new content remains readable/editable after restart.
- [ ] Production preflight, postflight and smoke evidence is preserved.

## Dependencies

Requires successful completion and production deployment of 0022–0028.

## Deployment and Rollback

This is intentionally destructive. Rolling application images back after dropping `marquee.page_id` or enforcing new constraints may fail because old binaries expect the old schema or do not populate required columns. Rollback therefore requires the compatible pre-migration application versions together with restoration of the immediately preceding database backup and, if affected, Files-root snapshot.

