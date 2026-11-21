# 0051 Step 2 — writer-invariant regression follow-up (20 November 2026)

**Step 1 CLOSED; Step 2 OPEN. No production changes.**

## Observed run

The Windows owner reran `./gradlew --no-daemon :diaries-responder:test` after the separate test-compilation fix and saved `evidence/Step 2/private/step2-responder-tests-rerun.log`.

- `compileJava` **UP-TO-DATE** and `compileTestJava` **PASS**.
- JUnit: **335 tests completed, 1 failed, 36 skipped**.
- Sole failure: `com.rsmaxwell.diaries.responder.utilities.DiaryContextTest.writerRejectsCrossTypeAndMismatchedRelationships`, line **134**, `AssertionFailedError`.
- Seven deprecation/removal warnings in unrelated existing `ImageWiringIntegrationTest.java` and Gradle compatibility warnings do not explain this failure.

## Root cause and limited fix

The original assertion expects a valid **IMAGE Fragment with a same-Page Marquee** to be rejected. That is deliberately superseded by the owner-approved 0051 Step 1 contract: an IMAGE may have an optional 0..1 Marquee. The Step 2 implementation of `ResolvedFragmentState.validateForWrite()` correctly permits this combination while continuing to reject MARQUEE Fragments with Image references, mismatched Marquee Pages/Fragments and missing Fragment types.

Update only `DiaryContextTest.java` to assert success for IMAGE+Marquee and assert that the type remains `IMAGE`. Rename the test to reflect both its allowed and rejected cases. Preserve the four subsequent rejection assertions and the positive legacy MARQUEE case. This does not change production code, database schema, MQTT state or other tests. The original Step 2 and compilation-fix manifests remain untouched as historical receipts.

## Verification

The patch was checked structurally against the exact `DiaryContextTest.java` in the 20 November source bundle. The assistant environment does not have a cached Gradle distribution, so execution of the Java suite remains **pending**. After applying this incremental ZIP with Beyond Compare, rerun the **full responder tests** (not just the single failing test) and retain a fresh log. If green, continue with the isolated PostgreSQL/MQTT tests described by the Step 2 evidence register; those gates are not yet closed.
