# 0030 Step 4 — recoverable physical-file deletion

Completed 2026-09-27. Final validation: **32 focused tests and responder build
passed, no failures/errors/skips**. See `result.json` and `integration-test.xml`
for the separate database-backed run against the frozen 0024 fixture.

## Changes

`ImageCatalogueService` retains Step 3's locked ordering: atomic move into the
private same-filesystem staging directory, database commit, tombstone callback,
then backup cleanup. It now has a narrow package-private filesystem interface
for deterministic failure injection; normal callers use Java NIO operations.
Restoration creates a hard link without replacing an existing target.

A failed move no longer uses backup size to guess whether bytes were moved.
It conservatively retains both paths and reports recovery required, even for
an empty file or an exception reported after the move. No database deletion or
tombstone follows a failed staging operation.

Recovery exceptions and ERROR logs identify Image ID/path, database outcome,
operation phase, original path and backup location. Phases distinguish staging,
commit uncertainty, restoration, publication and cleanup. Errors do not report
success or silently discard a backup. Internal paths must remain out of RPC
responses when the handler is implemented.

## Failure coverage

| Case | Verified outcome |
| --- | --- |
| Existing file | Stage, commit, tombstone, cleanup in order |
| Missing file or directory target | Conflict; catalogue row preserved |
| Staging move rejected | Original preserved; no database mutation/publication |
| Move reports failure after moving empty bytes | Only copy retained in backup; explicit staging recovery |
| Database rollback | Original restored; no tombstone |
| Unknown commit | Backup preserved; no speculative restore or tombstone |
| Restore denied | Hard recovery error; original backup preserved |
| External replacement during restore | Replacement never overwritten |
| Cleanup fails after rollback | Restored original and backup retained |
| Tombstone callback fails after commit | Committed outcome recorded; backup retained |
| Cleanup fails after commit/publication | No resurrection; backup retained and cleanup failure logged |

The 14 `ImageCatalogueDeletionTest` tests include all these cases, invalid and
unowned paths, repeat deletion and shared-lock serialization. Eleven existing
catalogue tests and seven generic-delete guard tests also passed.

## Commands and evidence

```text
gradlew.bat :diaries-responder:test --tests *ImageCatalogueDeletionTest --tests *ImageCatalogueServiceTest --tests *DeleteCatalogueTest :diaries-responder:build --console=plain
```

`service-tests-build.log` and `unit-reports/` archive the final successful run.
Expected injected failures generate ERROR logs; these are verified test outcomes,
not failing tests. `recovery-log-excerpts.txt` records the structured diagnostics,
including `COMMITTED/CLEANUP` and `UNKNOWN/COMMITTING`.

`run-integration.ps1` restores the hash-verified frozen 0024 backup to a new
disposable PostgreSQL database and runs
`ImageWiringIntegrationTest.catalogueDeletionCommitsAndRejectsStaleSnapshots`.
It verifies real transactional deletion and stale-row rejection; before/after
database digests check fixture cleanup. The runner archives runtime identity,
test report, preparation logs and container cleanup. Current modified source is
used against the frozen database fixture; source hashes are recorded separately.

The previous day's run passed before a final diagnostic refinement; its rerun
was blocked by approval-review usage limits. This evidence contains the completed
validation of the final source after resuming, not the earlier partial result.

## Recovery and limits

Stop writers and inspect the actual row, target, backup and retained topic before
manual recovery. An UNKNOWN commit requires independent database verification.
Do not restore bytes for a committed deletion; reconcile the retained topic if
publication failed, then review the preserved backup for cleanup. For rollback
or staging failures, verify the original bytes and never replace an unexpected
target. No automatic backup purge or blind delete retry is introduced.

No development/production data or NAS content was mutated. Filesystem failure
tests use temporary local files and injected exceptions; they do not prove every
NAS/provider behaviour or power-loss durability. The tombstone callback is tested
without a live broker. RPC registration, status mapping and real publication
remain Step 5, with full workflow verification later. No ImageFragment reference
check is added. No new migration or deployment setting is required.
