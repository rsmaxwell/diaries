# 0024 Phase 9 - automated validation

Implementation and validation date: 2026-09-14. The repeatable runner is
`scripts/windows/validation/test-image-catalogue.ps1`. The final run's machine-readable
results are in `run/validation-summary.json`, with per-suite Java counts and the
SQL, Gradle and Angular logs beside it.

**Result: passed.** 237 responder tests, 50 web tests, 81 Angular tests and 24 SQL
scenarios passed; no tests were skipped. Responder and web builds and the client
production build passed. All four `git diff --check` checks passed and all owned
fixtures were removed. Existing Gradle deprecation and Angular CommonJS
(`quill-delta`, `buffer`) warnings remain non-fatal.

## Reproduce

From the `diaries` directory, in PowerShell 7:

```powershell
.\scripts\windows\validation\test-image-catalogue.ps1 `
  -BackupFile .\data\database-backups\development-infrastructure\diaries-development-20260912-203528.dump `
  -EvidenceDirectory .\diaries-responder\build\phase9-new-run
```

Prerequisites: Docker, the project's Java and Node build tools, installed Angular
dependencies, and Chrome/Edge (or an explicit `CHROME_BIN`). Each evidence directory
must be new. The runner enables all three Image integration environment variables,
forces the Java tasks to rerun, rejects failures and skips, builds both Java
components and the production client, checks all four Git diffs, and cleans up
only its own uniquely named containers. Failures also produce a summary and hashes.

The supplied backup is restored into a new disposable PostgreSQL database. The
separate SQL negative-test container has no network and uses tmpfs. JPA and MQTT
fixture ports bind only to loopback. Tests use temporary file trees; no live
database or production Files root is supplied. The MQTT fixture uses the current
application ACL and its `max_queued_messages 10000` setting. The web integration
suite creates its own Mosquitto fixture through Testcontainers.

## Coverage

| Requirement | Evidence |
| --- | --- |
| Image model, DTO and repository behavior | `ImageDtoTest`, `ImageRepositoryIntegrationTest`, `DiaryContextImageTest`, `ImageWiringIntegrationTest` |
| Shared paths, byte inspection and catalogue orchestration | `ImagePathPolicyTest`, `ImageMetadataInspectorTest`, `ImageCatalogueServiceTest` |
| Upload staging, conflicts, compensation, reply compatibility and replay | `UploadStagingTest`, `ImageWiringIntegrationTest`, client `file-rpc-compatibility.spec.ts` and `pageheader.component.spec.ts` |
| Protected and generic DeleteFile | `DeleteCatalogueTest`, PostgreSQL wiring guard tests, captured client transport replies and conflict handling |
| Existing-file reconciliation | `ImageReconcilerTest`, `ImageReconciliationIntegrationTest`; the actual-copy proof remains frozen in Phase 8 |
| SQL preflight, schema and postflight | 24 disposable-database scenarios in `run/sql/test-results.json`, including repeat application, schema drift rejection and chronology preservation |
| Startup with zero, one and multiple Images | Three parameterized `ImageWiringIntegrationTest` cases use production persistence wiring and `Synchronise.perform`, then compare late-subscriber QoS 1 retained Image payloads with committed rows; all chronology-table hashes remain unchanged |
| Retained updates, no-op replay and tombstones | `ImageCatalogueMqttIntegrationTest`, including stale canonical topics, orphan removal, alias removal and fresh subscribers |
| Snapshot completion and failure | `SynchroniseCallbackTest` checks UTF-8, tombstones, marker exclusion, distinct checkpoints, timeouts and disconnection |
| Web chronology unchanged | `MqttProjectionIntegrationTest` compares exact HTML for the index, diary, month/selected-fragment and page routes over zero, one and three Images, reader restarts and live Image creation/deletion |

The client regression exercises its real upload handler and shared RPC transport
with captured/synthetic replies. There is currently no public DeleteFile client
method or DeleteFile UI; those replies and 409 errors are checked through the
shared transport. These automated regressions do not replace Phase 10's complete
local application smoke test.

## Startup defect exposed by validation

The restored baseline produces 10,572 chronology topics. The former startup
subscriber requested overlapping QoS 1 subscriptions and treated a quiet interval
as a complete snapshot. Mosquitto reported dropped outgoing messages when the
replay exceeded its finite QoS 1/2 queue. This occurred even with the application's
10,000-message setting, and left stale retained Images after reconciliation.
Removing the overlapping subscriptions alone did not fix it.

`Synchronise` now uses one temporary `diaries/#` subscription at QoS 0 and an
explicit non-retained drain marker at each checkpoint. The marker is unique for
every synchronization run and checkpoint, uses the already-authorized
`diaries/diaries/_sync/{run}/{checkpoint}` hierarchy, and is excluded from the
snapshot. Startup fails on a missing marker or disconnected snapshot. The
temporary connections use unique IDs and are closed on success and failure.
Ordinary object publications remain retained QoS 1; unchanged objects are still
not republished. No ACL, RPC payload or canonical Image topic changed.

The broker queue distinction is documented in the
[Mosquitto configuration reference](https://mosquitto.org/man/mosquitto-conf-5.html)
(`max_queued_messages`); subscriber QoS behavior is described in the
[Mosquitto MQTT reference](https://mosquitto.org/man/mqtt-7.html).

## Evidence and remaining work

`SHA256SUMS.txt` freezes this document, the successful run and the source hash
manifest. `source-sha256.json` records the application source, test, build and
fixture inputs used for validation. Hashes establish identity, not approval to
deploy. Existing Phase 1/0022 and Phase 8 evidence has not been rewritten.

Phase 10 full-stack smoke testing and Phase 11 deployment/live reconciliation
remain separate work. The previously recorded twelve rejected images and
thirteen ambiguous candidate references remain data-review items. This phase
does not repair source images or apply reconciliation to development or production.
