# Step 14 revalidation — 2026-09-28 (Europe/London)

Supersedes the 2026-09-27 validation as evidence for the current responder source. Earlier runs and the previous inventory remain preserved. UTC timestamps begin on 2026-09-27 at 23:xx (2026-09-28 locally).

- Complete responder suite/build: **322 discovered, 285 passed, 37 environment-gated skips, zero failures/errors**. Both requested Gradle tasks actually reran.
- Web suite/build: **50 passed**, zero skips; build passed.
- Client: **132 passed**; production build passed.
- Fresh broker ImageCatalogueMqttIntegrationTest: **1 passed**, no skips.
- Fresh broker SynchroniseLargeRetainedTreeMqttIntegrationTest: **1 passed**, no skips. Verifies three synchronisation passes and an exact retained snapshot of 3,000 topics with 2 KiB padding per payload. Broker config uses max_inflight_messages 20 and max_queued_messages 10000.
- Fresh restored PostgreSQL/MQTT lifecycle and attachment/deletion race: **2 passed**, no skips.
- Fresh restored PostgreSQL/MQTT live RPC, restart replay and authoring-gate lifecycle: **2 passed**, no skips.
- Deployed client build 72/web build 5 compatibility probes: **passed again**, using read-only copies of actual running artifacts. Canonical/date Fragment decoders tolerate additive imageId:null.

This is six passing explicitly enabled integration cases in addition to the ordinary suite. Other opt-in integration cases remain skipped in the ordinary suite; this does not represent every possible integration fixture running. All owned integration containers were removed successfully and the database-backed runners verified unchanged application-table row hashes after cleanup.

Logs and XML are in this directory: full-test-build.log, component reports/results, client logs, deployed consumer probes, mqtt-regression/, database-mqtt/, live-rpc-replay-gate/. The ordinary suite reports were copied before later selected Gradle runs could overwrite them. Existing nonfatal Gradle and Angular warnings remain.

The refreshed source-sha256.csv inventories 398 source/test/build/config files, including Synchronise.java, SynchroniseCallback.java, the new large-tree test and broker configuration. The parent Step 14/source-sha256.csv is the active matching copy for the Step 15 runner. Step 14/source-sha256-before-20260928.csv preserves the previous inventory. Git identities/status/diff summaries identify the tested working tree; HEAD alone is insufficient because synchronisation changes are uncommitted.

Commands: gradlew.bat :diaries-responder:test :diaries-responder:build :diaries-web:test :diaries-web:build --rerun-tasks --console=plain; npm.cmd test -- --watch=false --browsers=ChromeHeadless; npm.cmd run build -- --configuration production. run-mqtt-regression.ps1 creates a fresh broker per synchronisation test. Existing Step 11 and Step 13 runners produce the database/MQTT evidence in new directories.

The large-tree regression directly exercises the former startup replay concern. Live fixture assertions still use exact selected topics; no claim is made that an independent observer audited every frozen database retained payload. Production broker ACL/queue rollout is outside this test run; deploy the documented matching broker configuration with the new responder.

No production state, live development database or NAS content was changed. Step 15 must use this regenerated inventory and a clean disposable environment.
