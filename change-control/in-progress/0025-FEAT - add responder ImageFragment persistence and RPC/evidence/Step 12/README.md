# 0025 Step 12 - Live MQTT RPC and retained replay

Completed 2026-09-27. **Authoritative evidence is `final-run/result.json` and
`final-run/integration-test.xml`**: one integration test passed, zero failures/skips.
The directory named `verified-run` is an earlier failed attempt, not the final result.

## Live path and scenarios

`ImageWiringIntegrationTest.liveImageFragmentRpcAndRestartReplay` sends actual MQTT 5
requests through disposable Mosquitto to the registered responder dispatcher. Separate
requestor, subscriber and publisher connections carry access-token properties, response
topics and per-request correlation data. Replies are checked for status 200 and matching
correlation. Each server callback owns its persistence context.

- Create an IMAGE Fragment through addImageFragment. Verify committed Page/type/Image,
  no Marquee, both retained Fragment aliases and the unchanged Image catalogue topic.
- Lock and edit text, sequence, date, Image replacement, explicit-null clearing and
  reattachment. Compare both retained aliases with DTOs reloaded through fresh database
  contexts; check old-date tombstone, version advancement and successful lock release.
- Create IMAGE and MARQUEE neighbours via RPC, reorder and normalise the shared date.
  Check database sequence 1..3 and the same retained sequence values.
- Delete the IMAGE Fragment via RPC. Check row/aliases absent, Image row/topic and
  physical file preserved.
- Close request connections, deliberately remove/corrupt survivor retained entries and
  restore a stale deleted-Fragment topic. Recreate the persistence factory and context,
  run production `Synchronise.perform`, and reconnect the RPC endpoint. Fresh exact-topic
  subscriptions prove survivor Image references and aliases are restored, stale topics
  removed, both Images preserved and no synthetic Marquee introduced. Lock/unlock still
  succeeds through MQTT after rebuilding the endpoint.

This exercises a persistence/connection restart and actual startup reconciliation in
one test JVM. It does not restart a packaged responder process or test an Angular browser.
Production synchronization loads the complete frozen baseline; post-replay assertions
cover the controlled fixture topics using bounded exact-topic subscriptions.

## Defect found and required fix

The first real-wire test failed when clearing selection: mqtt-rpc-common 0.0.8's
`Request` compact constructor uses `Map.copyOf(args)`, rejecting `imageId:null` before
UpdateFragment is reached. Direct handler tests could not expose this transport error.

`ImageFragmentMessageHandler`, installed in `Responder`, preserves explicit-null
imageId requests for addImageFragment and updateFragment. It calls the same registered
handlers with unchanged authentication/validation and retains response-topic,
correlation, status-property and QoS 1 reply conventions. Other requests still use the
library dispatcher. The existing 20 MiB transport limit and required correlation/response
properties are preserved. No dependency repository or published library was modified.
Remove the adapter when the dependency gains null-preserving request arguments.

Four unit contracts verify explicit null for both operations, absent/non-null behavior,
handler authorization failure and missing-correlation rejection. The integration verifies
actual clear/reattach over the broker. Existing client compatibility tests still pass.

## Validation and safety

- Live integration: **1 passed, 0 skipped**, final-run.
- Full responder tests/build: **315 discovered, 280 passed, 35 environment-gated skips,
  0 failures/errors**; `final-test-build.log`, `unit-results.json`.
- Client RPC/Files-dialog tests: **59 passed**; production build passed. Existing
  CommonJS optimization warnings remain; no client source changed.
- Disposable PostgreSQL restored from the hash-verified frozen 0024 dump plus migrations;
  Hibernate schema validation enabled. Temporary files only, no production or NAS access.
- Database table row hashes match before/after cleanup. Both containers removed successfully.
- Source hashes in `source-sha256.csv`; changes remain uncommitted. No production deployment.

## Earlier attempts and observation limits

run-01 exposed the explicit-null request defect. run-02 passed the live mutation flow
but the full-tree observer snapshot differed from the 10,580-topic baseline. The earlier
`verified-run` timed out at its drain marker. run-04 used the production snapshot callback
and still received an incomplete bulk snapshot (375 topics missing), while production
synchronization logged `synchronise: ok`. These attempts are preserved for diagnosis.
The final run uses exact-topic subscriptions for the controlled replay assertions to
avoid bulk replay queue pressure; it does not claim an independent complete-baseline
snapshot audit. No broker production limits or synchronization code were changed.

## Files and reproduction

- Responder.java and utilities/ImageFragmentMessageHandler.java: scoped transport fix.
- ImageWiringIntegrationTest.java: live broker harness, lifecycle/replay scenario and
  bounded snapshot helper. Existing Step 11 helper can still use its default wildcard.
- ImageFragmentMessageHandlerTest.java: transport regression contracts.
- run-integration.ps1 / fixture-mosquitto.conf: disposable one-test runner and broker.
- Feature plan/README and responder README: completed status and operational notes.

Run `run-integration.ps1 -EvidenceDirectory <new-directory>` in PowerShell 7 with Docker
and the frozen backup available. Existing evidence directories are rejected. The runner
restores prior test environment variables and cleans only its owned containers.

Step 13's production authoring gate remains to be implemented before rollout.
