# 0030 Step 1 — database-backed delete guard verification

**Result: PASS.** Run once on 2026-09-26, 08:56:19–08:56:39 UTC.
Exactly one integration test executed: zero failures, errors or skipped tests.

## Test and command

```powershell
.\gradlew.bat :diaries-responder:test --tests com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest.deleteGuardUsesLiteralPostgresPrefixesAndPreservesCatalogue --rerun-tasks --console=plain
```

`DIARIES_IMAGE_WIRING_TEST_URL` pointed exclusively to a new loopback-bound
`image_wiring_test` database in a disposable PostgreSQL container. The test used
the production JPA factory/repository and actual `DeleteFile` handler, with
temporary local files. It was not skipped by its environment-variable condition.

The test verifies:

- exact catalogue-owned file and parent-directory deletion requests return 409;
- case, separator and Unicode aliases remain protected;
- SQL wildcard/escape characters in directory prefixes are treated literally;
- rejected deletion preserves original file bytes and catalogue metadata;
- catalogue ownership still protects a directory when its file/directory is absent;
- unrelated empty directories can be deleted and missing generic paths remain
  idempotent without creating directories.

## Frozen 0024 environment

The fixture was recreated using the database setup from the completed 0024
Phase 9 runner, narrowed to this one test instead of the full multi-component suite.

- Backup: `diaries-development-20260912-203528.dump`.
- SHA-256: `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`,
  verified against the frozen Phase 9 validation summary before restoration.
- Applied the archived 0024 `migration/schema.sql` to the restored disposable database.
- Schema, integration-test source and `DeleteFile` source hashes match the frozen
  Phase 9 source manifest; see `frozen-source-comparison.json`.
- Current responder commit: `d12df1484f89452b8cee45f337a4c428de6ece30`;
  its working tree was clean before the run.
- Used the locally available `postgres:18-alpine` image, pinned to its resolved
  image ID for this run. The exact ID and server version are archived. This
  recreates the frozen database fixture; it does not claim that every tool or
  container binary is identical to the September 14 run.

No development/production database or NAS content was used as a mutation target.
The frozen backup was read only. Before/after database counts and row digests
match, including the empty Image table after test cleanup. The temporary
container was stopped and automatically removed successfully.

## Evidence

- `result.json`: invocation count, timing, source/backup identity and test totals.
- `integration-test.xml`: JUnit result for the single executed test.
- `gradle-test.log`: complete Gradle output (existing deprecation warning only).
- `restore.log`, `schema.log`: disposable database preparation.
- `database-before.txt`, `database-after.txt`: counts and row digests.
- `postgres-image-id.txt`, `postgres-version.txt`: actual database runtime identity.
- `responder-commit.txt`, `responder-status.txt`: source revision and clean status.
- `frozen-source-comparison.json`: comparison with frozen 0024 source hashes.
- `container-start.txt`, `cleanup.log`: fixture lifecycle.
- `run-integration.ps1`: focused runner adapted from 0024's existing runner.
  The overwrite guard was moved outside its try/finally after the successful run
  so an accidental second invocation cannot replace the recorded result. No test
  was rerun after this evidence-only safeguard.
- `SHA256SUMS.txt`: hashes of this evidence package, excluding the manifest itself.

## Scope and remaining work

This establishes the database-backed Step 1 regression baseline: generic
`DeleteFile` is not a supported way to delete a catalogued Image. It does not
implement or validate `deleteImage`, exercise a live MQTT transport/broker, or
claim completion of later 0030 steps. The handler returns a 409 conflict for
protected paths; transport compatibility fixtures and broader regression runs
remain separate evidence.
