# 0030 Step 3 — repository/service deletion primitives

Completed 2026-09-26. **PASS: 27 focused tests, responder build and one
database-backed integration test; no failures, errors or skips.**

## Implementation

- `ImageCatalogueService.java`: adds fail-closed Catalogue lookup/delete
  primitives and a JPA adapter using a fresh EntityManager per operation. The
  adapter locks the row, checks its metadata against the expected snapshot,
  deletes exactly one row through the existing repository, commits before
  returning, and distinguishes definitive rollback from uncertain commit.
- `delete(path, tombstone)` canonicalizes input and shares the catalogue process
  and filesystem lock with upload/reconciliation. It resolves the stored path,
  requires a regular file, atomically stages bytes in a private backup, commits
  deletion, calls the tombstone publisher under the lock, then removes the backup.
  Its immutable `DeletedImage` result contains the id and canonical relative path.
- Known rollback restores bytes without overwriting a replacement. Unknown
  commit, failed restoration or post-commit failure preserves the backup and
  returns a typed recovery exception with the outcome and internal paths. A
  missing catalogue entry and missing/non-file bytes have distinct exceptions
  for later 404/409 handler mapping.
- `ImageCatalogueDeletionTest.java`: nine focused unit tests for success ordering,
  canonical identity, unowned/missing/directory targets, rollback, uncertainty,
  replacement safety, failed publication, path validation and shared locking.
- `ImageWiringIntegrationTest.java`: new PostgreSQL test verifies case-folded
  lookup, stale-snapshot rejection, deletion visible to a fresh reader before
  publication, missing-row rollback, and chronology preservation.

The existing ImageRepository path lookup and delete-by-ID operations were
sufficient; no new repository query or schema migration was added. Generic
DeleteFile protection is unchanged. No RPC registration or client/UI change.

## Validation

```text
gradlew.bat :diaries-responder:test --tests *ImageCatalogueDeletionTest --tests *ImageCatalogueServiceTest --tests *DeleteCatalogueTest :diaries-responder:build --console=plain
```

Result: 9 new deletion tests + 11 existing catalogue tests + 7 existing generic
delete guard tests passed; build passed. Full output: `service-tests-build.log`;
JUnit reports: `unit-reports/`. Existing Gradle deprecation warning remains.

`run-integration.ps1` adapts the Step 1 isolated fixture runner and executes only:

```text
ImageWiringIntegrationTest.catalogueDeletionCommitsAndRejectsStaleSnapshots
```

It restored the hash-verified frozen 0024 backup into a new disposable
PostgreSQL 18 container, applied the archived Image schema and ran the current
modified responder/test source. This is the frozen database fixture, not a claim
that the new implementation matches the frozen source. `result.json` records
the source hash, base commit, actual image ID/version and one successful invocation.

Before/after database row counts and digests matched, including an empty Image
table after fixture cleanup. No production/development database or NAS files
were mutated. The disposable container was removed. `gradle-test.log` and
`integration-test.xml` record the passing database-backed run.

## Remaining work

Step 3 includes the core recoverable protocol required by its implementation
plan; Step 4 still needs controlled staging-move/cleanup failure tests and
operational recovery logging/review. Unknown commits and failed publications
are deliberately not automatically retried or compensated as known rollbacks.

The tombstone callback was tested through assertions, not a real MQTT broker.
Step 5 must authorize, map exceptions safely, supply actual retained tombstone
publication and register the handler. Internal backup/target paths must not be
returned to clients. No ImageFragment reference guard is added until 0025.

This is focused validation, not a rerun of the full responder integration suite
or production smoke test. The full failure matrix and live workflow remain
assigned to the later steps. Step 1 and Step 2 evidence is preserved.
