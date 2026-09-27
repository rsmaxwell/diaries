# 0025 Step 6 — Implement and register addImageFragment

Completed 2026-09-27. Earlier uncommitted feature work preserved; no deployment or commit.

## Files and behaviour

- `handlers/AddImageFragment.java`: active EDITOR authentication; exact numeric parsing, positive IDs, calendar-valid dates, string text <=4096 characters, NUMERIC(10,4) sequence without rounding. Uses the same four-decimal insertion chronology as AddFragment, with no immediate sequence normalisation. Missing/invalid references return controlled 400 responses. Missing, malformed, expired, inactive and insufficient-role credentials return 401.
- `Responder.java`: registers `addImageFragment` beside unchanged `addFragment` registration.
- The operation fixes type=IMAGE, ignores unexpected identity/type/marquee fields, uses `saveImageFragment` (transaction-scoped Image lookup/lock), creates no Marquee, publishes only after commit and returns FragmentPublishDTO.
- Synchronous publication failure returns 500 identifying the already-committed Fragment; retries are not idempotent. Other internal errors use generic messages. Publication remains asynchronous QoS 1 like AddFragment, without waiting for PUBACK.
- `AddImageFragmentTest.java`: five tests covering auth, valid/omitted/null Image references, authoritative type, malformed input, missing Page/Image, persistence failure and publication failure.
- `ImageWiringIntegrationTest.java`: dispatches requests through the registered MessageHandler against actual PostgreSQL and Mosquitto, checks response correlation/status and committed DB rows, unchanged Marquee count, and late-subscription retained payloads on both aliases.
- Responder README and feature tracking record the contract and scope.

The new handler explicitly rejects invalid calendar dates and values outside schema bounds as requested. AddFragment's parsing/error handling is unchanged; its validation is less strict in some cases. Decimal scale and creation ordering remain compatible.

## Validation

`gradlew.bat :diaries-responder:test :diaries-responder:build --console=plain` passed:
**278 discovered, 248 passed, 30 environment-gated skips, zero failures/errors**.
See `final-test-build.log`, `unit-results.json`, `handler-tests.xml`.

Separate integration: **one passed, zero skipped** in `verified-run/result.json` and
`verified-run/integration-test.xml`. `run-01` was the earlier successful integration.
The fixture restores the frozen 0024 dump, applies 0024 and 0025 schema migrations,
and starts owned PostgreSQL/Mosquitto containers with random loopback-only ports.
It uses direct registered dispatch and real MQTT replies/retained subscriptions;
it does not test the production listener connection. The broker allows anonymous
fixture traffic only and is never used as production configuration.

Before/after hashes of all Diary/Page/Fragment/Marquee/Image rows match after cleanup.
Both fixture containers were removed. No live database, broker or NAS content changed.
The first regression run exposed uncaught malformed JWT exceptions; the new handler
was corrected to use the controlled 401 convention from DeleteImage before final checks.
Existing Gradle/Shadow and deprecated native-query warnings remain nonfatal.

Client and web source/contracts are unchanged; Step 5 already verified their builds
and compatibility with the Fragment reply/retained shape. No client wrapper was added
or consumer builds rerun for this additive server RPC.

## Remaining scope

Step 7 implements Image-aware UpdateFragment semantics. Reference-aware DeleteImage
and later concurrency/workflow checks are still required. The registered operation
is available in this source build, so do not enable production IMAGE authoring until
the remaining safeguards and consumer deployment requirements are met. No new database
migration is needed for Step 6.
