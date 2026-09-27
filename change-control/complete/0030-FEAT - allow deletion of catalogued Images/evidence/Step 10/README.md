# 0030 Step 10 — Failure-path verification

Completed 2026-09-27. All selected tests passed; no production code changes were necessary.

## Failure matrix

| Scenario | Verification and resulting state |
| --- | --- |
| DB failure after staging, rollback known | Existing recovery test confirms original bytes restored, Image row retained, no tombstone, and staging backup cleaned. Handler test confirms safe 500. |
| DB commit outcome unknown | Existing fault injection produces UNKNOWN/COMMITTING recovery exception with Image identity and preserved original backup. No blind restoration or tombstone. |
| MQTT tombstone publication fails after commit | Existing injected publication failure confirms row/file removed but original backup preserved, COMMITTED/PUBLISHING recovery exception, and safe 500. Handler test explicitly retains stale metadata, so partial completion is reported rather than mistaken for success. |
| Upload/delete same path, delete wins first | New latched race blocks upload through deletion publication. Afterwards upload succeeds with new identity 86; bytes, row and retained-map entry all describe the new image. Old topic identity absent; no backup left. |
| Upload/delete same path, upload wins first | New latched race blocks deletion through upload publication. Afterwards deletion removes the new file, row and retained-map entry; no backup left. |
| Simultaneous duplicate delete | New latched race yields exactly one commit/tombstone and one ImageNotFoundException; file/row/topic absent and no backup left. Existing handler repeat test maps not-found to 404. |
| Restart after completed deletion | Real PostgreSQL/Mosquitto test deletes an Image, disconnects its publisher, creates a fresh persistence factory/context, runs the actual startup Synchronise path and queries with a fresh MQTT subscriber. Deleted image stays absent from file, database and retained topics; the survivor remains intact. |

The focused recovery suite also covers staging failure, restoration failure, external replacement protection, cleanup failure and shared-lock contention. All cases that deliberately leave divergent state assert a typed recovery exception and preserved bytes. The service logs recovery phase/outcome/identity/paths; no tested partial failure returns success. Test logs include expected injected errors.

## Changes

- `ImageDeletionConcurrencyTest.java`: two upload/delete orderings and one concurrent duplicate-delete test, with bounded latches/futures and final file/row/retained-map/backup assertions.
- `ImageCatalogueDeletionTest.java`: explicitly asserts PUBLISHING phase for tombstone failure; existing failure scenarios rerun.
- `ImageWiringIntegrationTest.java`: completedDeletionStaysAbsentAfterRestart integration test using durable deletion, fresh factory/context, actual reconciliation and a fresh subscriber.
- Step 10 runner, fixture broker configuration, evidence and implementation completion record.

## Validation

`gradlew.bat :diaries-responder:test --tests '*ImageCatalogueDeletionTest' --tests '*ImageDeletionConcurrencyTest' --tests '*DeleteImageTest' --tests '*DeleteCatalogueTest' :diaries-responder:build --console=plain`

31 tests passed: 14 recovery, 3 concurrency, 7 handler and 7 generic-delete protection. Zero failures/errors/skips. Build successful. See unit-build.log and unit-reports. Existing Gradle/Shadow warnings remain.

`run-integration.ps1` ran completedDeletionStaysAbsentAfterRestart once: 1 passed, zero failures/errors/skips. See result.json, integration-test.xml and gradle-test.log. Frozen 0024 backup checksum verified; original database row digests unchanged after cleanup; both owned containers stopped successfully.

## Boundaries

Concurrency and injected DB/MQTT failures use controlled doubles with real temporary filesystem operations. Restart uses real PostgreSQL/MQTT and production startup reconciliation with newly created persistence/context and MQTT clients in the same JVM; it is not an OS-process crash/kill test. These match Step 10's controlled-double/integration-fixture scope. Cross-process lock behavior and production outages were not injected.

No live database, NAS content, active stack, client or deployment changed. The client suite was not rerun for these responder-only test additions. Step 9 already records browser-to-responder integration, and Step 11 production deployment remains outstanding. Nothing committed or pushed.

source-sha256.csv identifies tested source. Token-shaped strings are redacted in stored reports. Existing result.json prevents accidental overwriting/repetition of the integration run.
