# 0030 close-out — Step 12

Completed 2026-09-27. Feature 0030 is complete and archived under change-control/complete.

## Delivered behaviour

Active EDITOR-or-stronger users can choose Delete image in the Files dialog, confirm the named image and delete it. The responder canonicalizes the path, stages the bytes, deletes the catalogue row transactionally, awaits a QoS 1 retained tombstone acknowledgement and removes the backup. The dialog refreshes without closing. Generic DeleteFile remains protected. Invalid, uncatalogued and duplicate requests return controlled failures.

## Acceptance mapping

| Criteria | Evidence |
| --- | --- |
| Editor authorization, menu, confirmation, cancel | Steps 5, 7, 8; Step 9 real browser cancellation; Step 11 explicit production confirmation |
| File, database and retained-topic removal; refreshed Files list | Step 9 verified-run; Step 11 Image 84 pre/post evidence and 200 OK deletion/listing log |
| Uncatalogued/invalid paths and generic-delete protection | Steps 5, 9 and 10 |
| Rollback restoration and explicit uncertain-outcome failures | Steps 4 and 10, including committed publication failure and preserved backups |
| Client/responder contract and existing file compatibility | Steps 2, 5, 6, 9 and 10 |
| Passing tests/builds | Validation summary below and per-step reports |

## Exact changes

[changed-files.csv](changed-files.csv) records every path in the user-committed client and responder feature commits (e18da84 and 810444e, full identities in the CSV).

Responder changes: DeleteImage registration/handler, recoverable ImageCatalogueService deletion and JPA adapter, acknowledged ImagePublishDTO tombstone, portable ListFilesResponse directory separators, deletion/concurrency/handler/path tests, database/broker/browser fixtures and documentation. Existing ImageRepository methods were reused, so the repository interfaces required no edits. build.gradle's Eclipse source-resource exclusion is the separately requested PackagedInspectionProbe fix delivered alongside this work.

Client changes: typed DeleteImageReply, authenticated wrapper, synthetic RPC fixtures/compatibility tests, CDK context menu and confirmation, guarded operation/refresh/error flow, component and opt-in browser tests, test compilation configuration and documentation.

Parent changes: RPC contract, implementation tracking, Steps 1–12 evidence and this close-out; feature directory moved to complete and current 0024 links repaired. Historical evidence retains original paths and wording as captured.

## Validation

- Step 12 full default responder suite/build: 264 discovered, **238 passed, 26 skipped**, zero failures/errors; build successful. Environment-gated integration tests are skipped in this default run, not counted as passed. See responder-reports and responder-build.log.
- Step 10: 31 focused tests passed and one real PostgreSQL/MQTT restart-reconciliation test passed without skips.
- Step 9: one browser/database/MQTT scenario passed, plus 132 regular client tests and 14 responder regression tests/build.
- Step 8: 132 client tests and explicit production build passed. Subsequent client changes were opt-in test configuration/scenario only.
- Earlier step-specific database, recovery, RPC and UI results remain under their numbered evidence folders. Step 9's failed first attempt is preserved; verified-run is the successful corrected run.
- Existing Gradle/Shadow and Angular CommonJS warnings remain. No test claims are inferred solely from deployment status.

## Production evidence

Richard reports pluto deployed from top-level commit a8e70962898f52ac5db8baaab2e951b2bb884c36 with client 0.0.9-build-72, responder 0.0.9-build-80 and web 0.0.9-build-5. Supplied status shows healthy services and active shared nginx route.

Controlled deletion of Image 84 (img2230.jpg) succeeded: Richard confirmed file/database/topic absence and client refresh; the supplied console shows deleteImage and listFiles both returning 200 OK. Richard explicitly confirmed database and Files-root backups before deletion and acceptance of the confirmation dialog. Step 11 preserves the records and registry references.

Production observations and backups are user-confirmed, not independently re-inspected. Deployment ordering and running-container digest matching were not independently evidenced. These provenance limits are retained; no production actions were performed during close-out.

## Implementation differences and limitations

- Restore uses a no-overwrite hard link followed by backup cleanup rather than an unconditional move back, protecting unexpected replacement files. Unknown DB outcomes, failed restoration/publication/cleanup preserve recovery material and explicit diagnostics.
- Client API is deleteImage$(name, subdir?), matching optional-root file operations, rather than the original illustrative subdir-first signature.
- Client timeout remains five seconds; responder tombstone acknowledgement can wait ten seconds. A timeout is an unconfirmed outcome, not rollback; the UI offers refresh and does not blindly retry deletion. Existing shared authentication retry remains.
- The UI uses extension eligibility only; authorization/catalogue ownership remain server-authoritative. No bulk deletion, recycle bin or automatic resurrection is provided.
- Step 9 corrected Windows backslashes in the listing response. Controlled concurrency tests use one JVM; restart verification creates fresh persistence/context/MQTT clients and runs actual startup reconciliation, not an OS crash/kill test.
- **ImageFragment reference protection is deferred to feature 0025. It must reject referenced Images with 409 before production ImageFragment authoring is enabled.** This feature does not establish reference safety for that future workflow.
- Restoring deleted content requires a deliberate database/file-backup recovery operation; rolling back application images does not restore deleted data.

Step 12 completes the file-based change record only. Nothing was committed or pushed by the assistant.
