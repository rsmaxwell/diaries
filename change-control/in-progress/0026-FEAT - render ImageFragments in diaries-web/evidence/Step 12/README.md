# Step 12 — Real MQTT replay, permissions and HTTP projection

## Status

**Complete locally — 2026-09-29.**

No production runtime source changed for Step 12. The step adds real-broker integration coverage and deterministic retained fixtures around the production MQTT decoder/projection client and HTTP server.

## Completion evidence

The focused Java 25/Docker command was rerun from **PowerShell 7.6.6** and selected `Step12MqttHttpIntegrationTest` and `MqttReaderAclIntegrationTest`. It completed successfully:

```text
BUILD SUCCESSFUL in 1m 16s
7 actionable tasks: 7 executed
```

The complete web test/build gate also completed successfully:

```text
BUILD SUCCESSFUL in 1m 35s
15 actionable tasks: 15 executed
```

The exact operator-supplied PowerShell 7.6.6 console transcript is preserved in `test-results.txt`. The focused command executed the Gradle `:diaries-web:test` task with the real-MQTT/Testcontainers classes selected; no skipped-test count is inferred from the console because Gradle's plain output does not enumerate individual test cases.

## Coverage verified

`Step12MqttHttpIntegrationTest` owns a fresh Mosquitto 2.0.22 container per scenario. The broker uses the committed Diaries ACL plus test-only publisher/negative-control identities. Its flow-control settings match the application broker assumptions:

```text
max_inflight_messages 20
max_queued_messages   10000
```

The verified scenarios cover:

1. **Late retained replay → live Image lifecycle → reconnect generation swap**
   - canonical Diary/Page/MARQUEE Fragment/Marquee/Image plus IMAGE Fragments are retained before the reader starts;
   - the real `MqttProjectionClient`, `ProjectionService` and `WebServer` reach readiness from retained replay;
   - shared Image metadata updates are reflected through immutable resolutions and HTTP;
   - Image tombstone/restore preserves Fragment chronology while media degrades/recovers;
   - Fragment-before-Image arrival repairs when metadata appears later;
   - a fresh broker generation replaces stale state atomically after reconnect.

2. **Permission-loss and RPC-free/read-only behavior**
   - a negative-control reader without `diaries/images/+` access preserves the IMAGE Fragment as missing metadata instead of dropping it;
   - the web projection subscriber emits no responder RPC during connect/replay;
   - the committed `diaries-web` identity remains unable to publish RPC or Image writes.

3. **Production-sized retained replay**

```text
diaries     10
pages       683
fragments   2329
marquees    2269
images      85
----------------
topics      5376
```

   - the retained tree uses current production-scale counts;
   - the reader uses the runtime replay values `quiet=1500 ms`, `timeout=30 s`;
   - projection counts/diagnostics and an actual IMAGE Fragment are verified through HTTP.

## Step boundary

Step 12 verifies the real broker → decoder → immutable projection → HTTP path and reader ACL behavior. It does not perform the controlled cross-component development deployment, exact published-artifact verification or production rollout. Those remain Steps 13–16.

**Next:** Step 13 — Run controlled cross-component development verification.
