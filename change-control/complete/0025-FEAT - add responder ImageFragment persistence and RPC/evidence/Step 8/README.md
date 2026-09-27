# 0025 Step 8 — Mixed Fragment lifecycle

Completed 2026-09-27. Existing local feature changes preserved; no commit/deployment.

## Audit and implementation

| Path | Result |
| --- | --- |
| LockFragment / UnlockFragment | Already publish optional aggregate state from Step 4. Added Fragment row locking before reading state so a lock update cannot overwrite a concurrently changed Image reference. No Image edit lock is taken. Missing-fragment unlock remains idempotent. |
| FragmentLocking | Common publication already supports both types. Added requireMarqueeCompatible guard for MARQUEE or legacy null type with no Image reference. |
| DeleteFragment | Now resolves state under a Fragment row lock in its own transaction, checks affected row counts, commits before tombstones. Deletes optional Marquee only for compatible fragments; IMAGE+Marquee is a controlled conflict directing repair. Image lifecycle is untouched. |
| AddMarquee | Uses the compatibility guard including imageId=null. Existing legacy null-type adoption remains. |
| UpdateMarquee | Rejects IMAGE or Image-referenced fragments before acquiring the failed-edit recovery target, so invalid geometry edits cannot silently unlock/mutate such a Fragment. |
| DeleteMarquee | Existing code retained as the deliberate lock-authorized repair action. It deletes only the Marquee, clears the Fragment lock and republishes without changing type/Page/Image. |
| FragmentSequenceNormaliser | Ordering remains type-independent. Publication now uses DiaryContext.resolveFragmentState instead of its own Marquee lookup. |
| NormaliseFragments | Existing transaction then publication path needs no further change. |
| Responder stale-lock release | Already uses ResolvedFragmentState/FragmentLocking from Step 4; no remaining FragmentAndMarquee callers. |

## Verification

Full responder tests/build passed: **286 discovered, 254 passed, 32 environment-gated skips, zero failures/errors**. See `final-test-build.log`, `unit-results.json`, `normaliser-tests.xml`.

Focused mixed-type unit test uses MARQUEE/IMAGE/MARQUEE/IMAGE with sequences 4/2/1/3 and 40/20/10/30, verifying one ordered 1..4 sequence and preserved Image IDs. The fake repository was updated to preserve imageId when changing sequence/version, matching the real SQL behaviour. Guard tests cover IMAGE rejection and legacy compatibility.

Separate database integration: **one passed, zero skipped**, authoritative `verified-run/result.json` and `verified-run/integration-test.xml`. `run-01` also passed before final Fragment lock serialization and additional retained-Marquee assertions.

The test uses the real handlers and repositories with disposable PostgreSQL restored from the frozen 0024 backup plus both migrations. A recording MQTT client asserts retained QoS 1 and publication after commit. It verifies:

- all four mixed fragments lock/unlock through the same handlers;
- NormaliseFragments produces one shared chronology and correct IMAGE retained references;
- AddMarquee and UpdateMarquee reject IMAGE relationships;
- seeded invalid IMAGE+Marquee deletion is rejected until DeleteMarquee repairs it;
- repair preserves Fragment type and Image ID;
- Fragment deletion removes associated MARQUEE rows/topics and both Fragment aliases;
- referenced Image row, configured temporary file bytes and Image retained topic remain untouched after each deletion, including the last reference.

Application row counts/hashes match after cleanup and the owned container is removed. No live database, broker, NAS or deployment is modified. The integration client records MQTT calls; this is not a production/broker end-to-end test. Step 6 holds separate real-broker evidence. The final integration run covers the only fixture assertion additions after the final full build.

Client/web payload schemas are unchanged, so their builds were not repeated (Step 5 compatibility evidence remains). Existing Gradle/Shadow/native-query warnings are nonfatal. `git diff --check` passed. Source hashes are in `source-sha256.csv`.

## Remaining work

Step 9 must extend recoverable DeleteImage with transaction-safe reference protection. This step deliberately does not delete reusable Images or enable production IMAGE authoring. No new schema migration is required.
