# 0030 Step 5 — Add and register DeleteImage handler

Completed 2026-09-27.

## Implementation

- `handlers/DeleteImage.java`: active EDITOR-or-stronger authorization, strict arguments, shared path policy, recoverable deletion service, safe 400/401/404/409/500 errors and 200 identity/path/deleted payload.
- `Responder.java`: registers the handler on the existing dispatcher.
- `ImagePublishDTO.java`: acknowledged empty QoS 1 retained tombstone, with ten-second timeout and broker rejection handling.
- `ImageCatalogueService.java`: typed unsafe/inaccessible-path error for 400 mapping; existing backup and transaction recovery remain authoritative.
- `DeleteImageTest.java`: success/repeat, root default, authorization, arguments/paths, generic-file protection, conflicts, rollback and publication failure.
- `ImageWiringIntegrationTest.java`: real database and broker test through the registered dispatcher.
- Responder README and feature documentation updated; Step 5 marked complete.

## Validation

`gradlew.bat :diaries-responder:test --tests '*DeleteImageTest' --tests '*ImageCatalogueDeletionTest' --tests '*DeleteCatalogueTest' :diaries-responder:build --console=plain`

28 tests passed (7 handler, 14 recovery, 7 generic-delete protection), zero failures/errors/skips. Build successful. See unit-reports and unit-build.log. Existing Shadow duplicate-resource and Gradle deprecation warnings remain.

`run-integration.ps1` ran registeredDeleteImageRemovesRowFileAndRetainedTopic once: 1 passed, zero failures/errors/skips. See result.json, integration-test.xml and gradle-test.log.

The runner verified the frozen 0024 backup checksum, restored it to disposable PostgreSQL 18, and used a separate loopback-only anonymous Mosquitto fixture. Image bytes were temporary test files. Original diary/page/fragment/marquee/image row digests matched after cleanup. Both owned containers stopped successfully. No live database, production broker or NAS files were used.

The integration test injects the request into the actual registered dispatcher directly; outgoing reply and retained publication use the real MQTT broker. It verifies reply correlation/payload, row/file removal, and absence of retained image metadata for a fresh subscriber. This is not an incoming MQTT subscription or browser end-to-end test.

Client contract shape is unchanged. Step 2 synthetic client compatibility fixtures remain applicable; client tests were not rerun. Client wrapper/UI and broader workflow verification remain subsequent steps.

## Evidence integrity

source-sha256.csv identifies implementation/test sources. Logs redact token-shaped strings. The runner refuses to overwrite existing result.json.
