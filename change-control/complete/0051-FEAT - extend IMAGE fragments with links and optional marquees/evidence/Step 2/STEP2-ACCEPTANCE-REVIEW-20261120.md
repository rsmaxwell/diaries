# 0051 Step 2 — owner-run acceptance evidence review

Date: 20 November 2026 (UTC)  
Status: **verification PASSED — formal owner acceptance pending**

## Evidence and historical progression

1. First responder test run: `:diaries-responder:compileJava` passed, `compileTestJava` failed in `FragmentSequenceNormaliserTest` (missing JUnit `assertDoesNotThrow` static import) and `ImageLinkWritePolicyTest` (mixed `Map.of` generic inference). Corrective source package applied.
2. Second run: tests compiled; 335 completed, one failure, 36 skipped. The sole failing `DiaryContextTest.writerRejectsCrossTypeAndMismatchedRelationships` assertion expected valid IMAGE+Marquee to be rejected. Test updated to new approved invariant.
3. Third run, local Windows Cygwin (`note(20261120-114337).txt`): `:diaries-responder:test` **BUILD SUCCESSFUL in 11s**, after `compileJava`, `compileTestJava` and `test`. Gradle 10 deprecation is a non-blocking warning. Do not infer a final executed-test count from the summary log alone.
4. Backup fixture verification: frozen `diaries-development-20260912-203528.dump`, expected SHA-256 `fe0e187eda4fe4c7923590f7ec5e36871ced87e2ba8fa6d3f882e0b0992d6b86`, **PASS**.
5. First disposable integration run `3e52218d5880`: failed before 0051 migration because 0025 preflight and migration ran in separate `psql` sessions. Historical failed receipt/logs retained. Runner corrected to use one session.
6. Successful disposable integration run `c1759df22f5f` (`note(20261120-122716).txt`): migration twice, schema assertion, unchanged data hashes, two actual PostgreSQL/MQTT integration tests; runner **PASSED**.
7. Owner independently reviewed the receipt and checksums (`note(20261120-123025).txt`): `result.json` status `PASSED`, started `2026-11-20T12:25:17.0796264Z`, finished `2026-11-20T12:27:02.3767596Z`; migration idempotent `true`, existing values preserved `true`, JUnit 2 tests/0 skipped/0 failures/0 errors. JUnit suite `com.rsmaxwell.diaries.responder.ImageWiringIntegrationTest` ran in 88.519 seconds. `sha256sum -c SHA256SUMS.txt` **PASS**.

## What the isolated tests exercise

- Default-off extension gate and existing IMAGE-authoring preservation.
- Real MQTT-RPC IMAGE creation and link storage/retained publication, invalid URL rejection without retained-state changes, and old-client omission preserving URL.
- Optional same-Page IMAGE Marquee attach/geometry edit/delete; duplicate rejection, IMAGE identity/reference/link preservation.
- Startup-style retained replay from persisted data; canonical Fragment/date aliases, Marquee publication and tombstones.
- Explicit `clearImageLinkUrl` and Fragment deletion without deleting the shared catalogue Image.
- Additive schema migration run twice and schema assertion against the disposable restored fixture, preserving existing values.

The broader synthetic Java suite covers further lock/version/type/schema corner cases; the two isolated integration cases should not be described as exhaustive production E2E coverage.

## Safety, acceptance and handoff

- Database restoration took place only in disposable, loopback-bound containers. No live `pluto` schema or data were changed, no production service was restarted, and the new `imageFragmentExtensionsWritesEnabled` gate has not been enabled in production.
- `migration/README.md` documents a backup/rollout requirement and the rollback limit: after new IMAGE link/Marquee writes, old binaries are not safe rollback targets. The nullable schema itself is additive; do not downgrade schema or remove data as part of rollback.
- Steps 3–5 remain OPEN. Step 3: editor, web reader and Day reader, including UI accessibility/test coverage; Step 4: 0028 migration-handoff and controlled rollout; Step 5: feature acceptance/resume 0028.
- **Requested decision:** owner formally accepts Step 2 responder/persistence verification and authorises marking the Step 2 gate CLOSED. Until that decision is given, record verification as PASSED and gate as acceptance pending.

## Evidence locations

Original run logs, migration outputs and checksums remain under `evidence/Step 2/private/` in the owner's Windows working copy. Those private folders are not part of this public-ready report; filenames and IDs above provide a traceable reference without embedding production content.
