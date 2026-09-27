# 0025 Step 14 — Full responder regression and compatibility verification

**Current evidence: [2026-09-28 revalidation](revalidation-20260928/README.md).** Synchronisation source changed after the original run; the new full regression, six integration cases, compatibility probes and regenerated SHA inventory supersede the results below for current-source readiness. Original evidence remains historical.

Completed 2026-09-27 against the assembled Step 1–13 working tree. No application implementation changes were needed. Existing uncommitted work was preserved; no commit, deployment, production migration or authoring-gate change was performed.

## Results

| Check | Result | Evidence |
| --- | --- | --- |
| Full responder suite | 320 discovered; 284 passed; 36 environment-gated skips; zero failures/errors | `diaries-responder-results.json`, `diaries-responder-reports/` |
| Responder build | Passed, all tasks rerun | `full-responder-web-test-build.log` |
| Step 11 database/MQTT lifecycle and attachment/deletion race | 2 passed, zero skips | `database-mqtt/result.json`, `integration-test.xml` within that directory |
| Step 12 live RPC/restart replay plus Step 13 gate/lifecycle | 2 passed, zero skips | `live-rpc-replay-gate/result.json`, `integration-test.xml` within that directory |
| Web suite/build | 50 passed, zero skips; build passed | `diaries-web-results.json`, `diaries-web-reports/`, full build log |
| Client suite/production build | 132 passed; production build passed | `client-tests.log`, `client-build.log`, `client-result.json` |
| Deployed web build 5 | Actual deployed decoder produces equal MARQUEE objects for absent and explicit-null imageId | `deployed-web-compatibility.log` |
| Deployed client build 72 | Actual compiled canonical and date-alias decoder callbacks accept absent and explicit-null imageId, preserving all other fields | `deployed-client-compatibility.log` |

The 36 skips in the ordinary responder run are ImageWiringIntegrationTest (24), ImageRepositoryIntegrationTest (10), ImageReconciliationIntegrationTest (1), and ImageCatalogueMqttIntegrationTest (1). The four explicitly selected integration cases above were executed separately; this does not claim that every optional integration case was rerun with its environment enabled. This meets Step 14's explicit Step 11/12 fixture requirement.

## Regression focus

All executed tests passed. Relevant coverage reviewed includes:

- MARQUEE creation/editing and cross-type invariants: AddFragmentContractTest, FragmentLifecycleContractTest, ResolvedFragmentStateTest and UpdateFragmentImageTest; mixed-type live RPC/retained fixture.
- Lock ownership/lifecycle and lock handling: FragmentLifecycleContractTest, DiaryContextTest and the live RPC fixtures.
- Canonical/date alias payloads, date moves and tombstones: RetainedStateDtoContractTest and liveImageFragmentRpcAndRestartReplay.
- Mixed sequence normalisation: FragmentSequenceNormaliserTest and the database/live fixtures.
- Startup replay: DiaryContextTest, SynchroniseCallbackTest and fresh-context live replay.
- Image upload/reconciliation: UploadStagingTest, ImageCatalogueServiceTest, ImageReconcilerTest and DiaryContextImageTest.
- 0030 physical deletion recovery: ImageCatalogueDeletionTest, ImageDeletionConcurrencyTest, DeleteImageTest; both attachment/deletion race orders on PostgreSQL.
- Generic DeleteFile catalogue protection: DeleteCatalogueTest.
- Authentication/status and nullable RPC arguments: AuthenticationHandlerTest, AuthorizationTest, ImageFragmentMessageHandlerTest, handler contracts and live gate rejection.

Live replay asserts the controlled fixture's exact canonical/date topics after production synchronisation. It is not a complete independent audit of every frozen baseline retained topic; the Step 12 bulk-observer limitation still applies.

## Deployed consumer compatibility

Read-only SSH inspection on pluto confirmed `rsmaxwell/diaries-client:0.0.9-build-72` and `rsmaxwell/diaries-web:0.0.9-build-5`. `production-containers.txt` records actual image IDs; embedded build metadata is preserved separately. Client metadata identifies pipeline commit a0247cfdc17eb2d63661a416341fe3e2dcef95df; web identifies e8d3470d6e65cf126319625a16fb308d7729454b. These are artifact metadata, not an assumption that the current source matches those commits.

The running web container's JAR was copied over SSH to ignored local build output. DeployedWebCompatibilityProbe.java executed against that JAR using Java 25 and the existing MARQUEE retained fixture. Both payload forms decoded to equal UpsertFragment events. Its SHA-256 is recorded in deployed-artifact-sha256.json.

The client JavaScript was copied read-only from the running container. deployed-client-probe.cjs extracts the real JSON.parse callbacks from getLiveFragment$ and the date-based fragments$ subscription in main-5L2A2TMF.js, runs them with both payload forms and verifies the parsed fields. The log records the exact callbacks and bundle SHA-256. This is a deployed parser compatibility check, not an interactive production UI test or a claim of IMAGE rendering support. Production retained topics were not modified.

The first client probe incorrectly matched a method call rather than its declaration. That probe failed before exercising the decoder; the extraction pattern was corrected and the final probe passed. The initial log is preserved as deployed-client-probe-initial.log. No application fix was required.

## Commands and reproducibility

From the diaries root:

```powershell
.\gradlew.bat :diaries-responder:test :diaries-responder:build :diaries-web:test :diaries-web:build --rerun-tasks --console=plain
```

From diaries-client:

```powershell
npm.cmd test -- --watch=false --browsers=ChromeHeadless
npm.cmd run build -- --configuration production
```

The existing `../Step 11/run-integration.ps1` and `../Step 13/run-integration.ps1` were used without modification, with -EvidenceDirectory pointing respectively to this step's database-mqtt and live-rpc-replay-gate directories. For another run, use new evidence directories. Runner hashes and source/config hashes are recorded in source-sha256.csv. Each result.json contains exact Gradle selection, container identities, schema/backup hashes and cleanup results.

Both runs restored the SHA-verified frozen 0024 backup into disposable PostgreSQL 18, applied the 0024/0025 schemas, and used isolated loopback Mosquitto containers. All five application-table row counts/hashes matched before/after fixture cleanup. Both brokers and both databases were removed successfully. No live database or NAS files were used.

To repeat the consumer probes after copying artifacts read-only to an ignored local build directory:

```powershell
java -cp <deployed-web.jar> <Step14>/DeployedWebCompatibilityProbe.java diaries-web/src/test/resources/fixtures/fragment.json
node <Step14>/deployed-client-probe.cjs <deployed-main.js> diaries-web/src/test/resources/fixtures/fragment.json
```

The read-only acquisition commands were `ssh pluto "docker exec diaries-web cat /opt/diaries-web/diaries-web.jar"`, `ssh pluto "docker exec diaries-client tar -C /usr/share/nginx/html/diaries -cf - ."`, and reading `/usr/share/nginx/html/diaries/assets/build-info.json` in that container. Binary output was captured with Python subprocess, avoiding text conversion. Artifacts themselves remain in ignored local build output; hashes, probes and results are preserved here.

Gradle deprecation/Shadow resource warnings and Angular CommonJS warnings remain nonfatal. Logs are redacted for JWT-shaped tokens. Component Git status/HEAD and SHA-256 inventory identify the tested dirty working tree. Diff whitespace checks passed (Git emitted existing line-ending conversion warnings).

Step 14 is complete. Step 15 development deployment/controlled validation and close-out remain outstanding. Production IMAGE authoring must remain disabled until the documented reader/rollout prerequisites are met.
