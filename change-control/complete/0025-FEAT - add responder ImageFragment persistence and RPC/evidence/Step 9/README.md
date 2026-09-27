# 0025 Step 9 - Reference-aware Image deletion

Completed 2026-09-27. Source implementation and local verification; no deployment or commit.

## Changes

- `ImageCatalogueService`: advisory reference check before staging; authoritative indexed `existsByImageId` check after acquiring the Image's exclusive row lock inside the deletion transaction. Reuses Step 3 repository query and Step 4 attachment lock.
- `ImageReferencedException`: deliberate known-rollback service conflict. A rollback failure still becomes an unknown-outcome deletion failure, not 409.
- `DeleteImage`: maps the clean conflict to 409 without exposing provider errors. Request, success response and retained Image contract unchanged.
- Deletion service/handler tests: already-referenced files are not staged; references found after staging restore bytes, preserve metadata and return 409.
- Database integration: two references, removing each reference, eventual recoverable deletion, and both actual concurrent lock orderings.
- Responder and feature documentation updated. No client source, schema, DeleteFile or deployment changes.

## Recovery and serialization

The existing catalogue/filesystem lock, same-filesystem staging, rollback compensation,
acknowledged post-commit tombstone and cleanup protocol are retained. The early query is
advisory only. Deletion locks the Image with PESSIMISTIC_WRITE and checks references
again before deleting. Attachment's PESSIMISTIC_READ lock serializes against deletion.
The FK remains mandatory final protection; no constraint-message parsing is used.

A reference discovered after staging follows normal clean rollback: restore bytes,
clean the backup, then return 409 without publishing a tombstone. Actual restoration
or cleanup failure still requires recovery. Unknown commit/rollback outcomes preserve
the backup and remain 500. Successful deletion retains the existing post-commit
publication/cleanup failure behaviour.

## Validation

- Full responder tests/build: **290 discovered, 257 passed, 33 environment-gated skips; zero failures/errors**. `final-test-build.log`, `unit-results.json`.
- Unchanged 0030 `DeleteCatalogueTest` generic DeleteFile guards passed, alongside deletion concurrency and recovery tests. XML reports are preserved here.
- Dedicated PostgreSQL integration: **1 passed, 0 skipped**, `verified-run/result.json` and `integration-test.xml`.
- Client RPC/Files-dialog compatibility tests: **59 passed**, `client-compatibility.log`.
- Client development and explicit production builds passed. Production emitted CommonJS optimization warnings for quill-delta and buffer; see `client-production-build.log`.

The database runner restores the SHA-verified frozen 0024 dump into a new loopback-only
PostgreSQL container and applies the 0024/0025 schema. It never uses the live database
or NAS. Fixture row counts/hashes match before and after cleanup; container removal
succeeded.

The integration test verifies:

1. Two Fragments reference one Image; deletion returns 409. Removing the first reference
   still produces 409. Removing the second leaves the Image intact, and explicit
   deletion then removes row/file and invokes the post-commit tombstone.
2. Attachment holds its row lock with an uncommitted reference. The deletion precheck
   cannot see it; deletion stages the file and waits on the lock. After attachment
   commits, deletion returns 409 and restores the original bytes without a tombstone.
3. Deletion holds the exclusive row lock first. Concurrent creation waits; after
   deletion commits, creation reports a missing Image without persisting a reference.
4. No deletion backup remains after successful operations/clean conflicts.

Race synchronization uses PostgreSQL's observed lock waits and a test-only
EntityManager wrapper that pauses after a real, asserted PESSIMISTIC_WRITE lock.
Each thread owns its EntityManager. MQTT tombstones are recorded through the handler's
existing publication seam and checked against a fresh committed database read; this
run does not connect a broker or browser. Existing client contract/flow tests cover
409 handling. Full deployed end-to-end verification remains a later feature step.

`run-01` and `run-02` are preserved failed test-development attempts: the deletion-first
checkpoint matched a specific find overload too narrowly and never fired. The corrected
checkpoint asserts the actual acquired lock mode. `verified-run` is authoritative.

## Reproduction

Run `run-integration.ps1 -EvidenceDirectory <new-directory>` from PowerShell 7 with
Docker and the repository Gradle prerequisites available. The runner refuses an
existing evidence directory. Source hashes in `source-sha256.csv` identify this
uncommitted implementation; the recorded HEAD alone does not identify it.
