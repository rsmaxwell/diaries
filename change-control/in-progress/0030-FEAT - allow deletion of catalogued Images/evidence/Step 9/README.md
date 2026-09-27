# 0030 Step 9 — End-to-end development verification

Completed 2026-09-27. The authoritative successful run is **verified-run/result.json** (PASSED). The first attempt is preserved in this directory's result.json and logs (FAILED); see the defect below.

## Verified workflow

The real Angular Files dialog and confirmation ran in Chrome Headless. Real RpcService and MqttService sent requests over WebSocket MQTT to the registered Java dispatcher and production handlers, backed by PostgreSQL and temporary image storage. Fresh MQTT subscribers inspected retained state at every checkpoint.

| Check | Result |
| --- | --- |
| Upload disposable.png and protected.png | Created Image IDs 1 and 2, physical files and retained metadata |
| Cancel deletion through Files dialog | Files, Image identities/paths and retained metadata unchanged |
| Confirm deletion through Files dialog | disposable.png, Image 1 and diaries/images/1 absent; file card disappeared without reopening dialog |
| Generic deleteFile against protected.png | 409; Image 2, file and retained metadata unchanged |
| Delete uncatalogued.png through Files dialog | 404 displayed; file preserved, catalogue/retained state unchanged |
| Re-upload disposable.png to deleted path | New Image ID 3, file and retained metadata present; refreshed file card visible |
| Upload to that occupied path again | 409; all inspected state unchanged |

See verified-run/browser-checkpoints.json for seven recorded snapshots and verified-run/client-e2e.log for actual browser/MQTT operation results. The Java integration report records one passing non-skipped test; the nested browser suite records one passing end-to-end scenario.

## Defect discovered and fixed

On Windows, ListFilesResponse(Path, ...) serialized the directory with backslashes. The first run caught the noncanonical path in the confirmation. The DTO now returns forward slashes, consistent with the cross-platform RPC path contract. A focused regression checks nested/root paths. The initial harness also needed to run change detection before reopening the menu after cancellation. Both corrections were made before the successful rerun; the failed evidence was preserved.

## Scope and environment

This is an isolated development verification fixture, not the active local stack or a production deployment. It uses the current source, a checksum-verified frozen 0024 backup restored into disposable PostgreSQL 18, a separate loopback-only Mosquitto TCP/WebSocket broker, and JUnit temporary files. No live database or NAS files were used.

The actual dialog is mounted by Angular TestBed; the application router/sign-in screen and complete responder startup are not exercised. A fixture-issued active EDITOR token supplies authentication. Icons and dialog host are test fixtures. Incoming MQTT requests, handler dispatch, authorization, upload/list/delete, persistence, retained publication and browser confirmation/refresh are real. This is not a mock-RPC component test.

The runner confirmed original diary/page/fragment/marquee/image row digests were unchanged after fixture cleanup. Both owned containers stopped successfully. Generated public/0030-step9-fixture.json (ephemeral fixture credentials) was removed. No persistent volumes or unrelated stack were changed.

## Files added/changed

- Responder ImageDeletionBrowserFixture.java: local HTTP state/file inspection, real MQTT request subscription, temporary client configuration, browser invocation and cleanup.
- ImageWiringIntegrationTest.java: opt-in browser fixture entry using the existing restored-database lifecycle.
- ListFilesResponse.java and ListFilesResponseTest.java: canonical directory separators and regression.
- Client files-list-dialog.e2e-spec.ts: real transport/UI scenario and checkpoint evidence.
- Client tsconfig.spec.json: compile opt-in .e2e-spec.ts files; normal Angular test discovery still selects only .spec.ts.
- Step 9 runner/broker config, documentation, source hashes and evidence.

## Validation

- Browser/database/MQTT integration: 1 Java test and 1 browser scenario passed, zero skipped (verified-run).
- Client regression: 132 tests passed; the opt-in scenario is excluded from normal discovery.
- Responder regression/build: 14 tests passed (13 UploadStagingTest, 1 ListFilesResponseTest); build successful. Existing Gradle/Shadow warnings remain.
- Git diff --check passed.

The production client source did not change in Step 9; Step 8's production client build remains applicable. No release or deployment performed. Step 10 failure-path verification remains next. Nothing committed or pushed.

## Reproduction

Run run-integration.ps1 with a new -OutputDirectory under this evidence directory. Existing result.json is never overwritten. Requires the frozen backup, locally available PostgreSQL/Mosquitto images, Gradle/Java, npm dependencies, and Chrome. The runner grants anonymous access only on its disposable loopback broker. Use the runner rather than invoking the browser scenario alone.
