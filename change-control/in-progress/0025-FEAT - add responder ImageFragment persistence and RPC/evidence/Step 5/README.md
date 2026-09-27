# 0025 Step 5 — Retained Fragment imageId contract

Completed 2026-09-27. Existing Step 3/4 work preserved; no commit or deployment.

## Implementation

- `FragmentPublishDTO.java`: removes the temporary JsonIgnore from imageId. Constructor copying added in Step 3 now reaches JSON, including explicit nulls. Publisher itself remains ignored.
- `RetainedStateDtoContractTest.java`: exact MARQUEE/IMAGE field sets, nullable Image reference, null IMAGE marqueeId, identical canonical/date payloads, JSON byte serialization, QoS 1 retained publication and zero-byte tombstones on both aliases.
- `FragmentRepositoryImplTest.java`: updates the temporary Step 3 boundary assertion to require explicit null imageId.
- `DiaryContextTest.java`: replays IMAGE fragments with valid/null Image references and no Marquee, verifying both aliases. Existing degraded-reader coverage remains.
- `ImageWiringIntegrationTest.java`: commits IMAGE fragments with/without a reference, opens a fresh EntityManager and production context wiring, then checks exact replay JSON and explicit imageId on every Fragment, including legacy MARQUEE rows.
- Responder README and feature tracking document the now-public contract.

`DiaryContext.loadFromDatabase()` needs no additional code change: Step 4 already resolves Image metadata and constructs FragmentPublishDTO for every Fragment independently of Marquee presence. No new topic hierarchy or authoring RPC was added.

## Verification

- Responder: **243 passed, 29 environment-gated skips**, zero failures/errors (272 discovered); build passed.
- Web consumer: **50 passed**, zero skips/failures; build passed. Existing retained fixtures explicitly cover nullable and numeric imageId.
- Angular consumer: **132 passed**; production build passed. Existing Fragment interface permits nullable imageId; no client source changes were necessary.
- Separate database replay integration: one passed, zero skipped. Authoritative evidence: `final-replay-run/result.json` and `final-replay-run/integration-test.xml`.

Commands and logs: `final-responder-web-test-build.log`, `diaries-responder-results.json`, `diaries-web-results.json`, `client-tests.log`, `client-build.log`, and `run-integration.ps1`.

The database runner uses a disposable PostgreSQL 18 container, the frozen 0024 backup, and the 0024/0025 schemas. Its before/after application row hashes match after fixture cleanup; the container is removed. No live database, broker or NAS was modified. This checks fresh-context database replay, not a deployed responder process restart or a live-broker subscription. MQTT publication flags, both aliases and tombstones are verified with a recording client.

The initial compile attempt used try-with-resources for Paho's non-AutoCloseable test client; corrected to explicit finally/close. The first replay attempt (`verified-run`, retained as failed evidence) found JSON numeric representation differences from an integer-scale fixture sequence; corrected to the application's four-decimal sequence format. These were test fixture issues, not suppressed application failures.

Existing Gradle/Shadow deprecation/resource warnings and Angular CommonJS/budget warnings remain nonfatal. The final integration rerun validates the only test-fixture edit made after the full builds.

## Next

Step 6 adds/registers addImageFragment. Reference-aware deletion and later authoring safeguards remain required before enabling production IMAGE creation. No additional database migration is needed for Step 5. No commit or push performed.
