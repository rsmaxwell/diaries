# Diaries: implement a genuine responder readiness health check using MQTT RPC

## Purpose

Replace the current false-positive responder Docker health check with a **real end-to-end MQTT RPC readiness check**.

The current checks in:

```text
diaries/compose.local-docker-build.yaml
diaries/compose.local-published-smoke.yaml
```

request a deliberately nonexistent HTTP URL:

```yaml
curl --silent --output /dev/null http://localhost:8081/not-a-responder-path
```

Because `curl` is not invoked with `--fail`, HTTP 404 is treated as a successful process exit. Docker can therefore mark the responder healthy merely because the embedded static HTTP server is listening.

That is particularly misleading because `Responder.main()` starts the static HTTP server **before** database initialization, startup MQTT synchronisation, and creation of the long-lived responder MQTT clients.

The replacement health check must use the same **MQTT RPC request/response path** that the Diaries client depends on. A health check is successful only when a complete RPC transaction succeeds and the responder confirms that the database is usable.

A successful check must therefore demonstrate, in one end-to-end operation, that:

1. Mosquitto is reachable;
2. the health-check MQTT client can connect and authenticate;
3. the responder's long-lived listener client is connected and subscribed to `diaries/rpc/request`;
4. the responder can dispatch an MQTT RPC request;
5. PostgreSQL is currently reachable/usable;
6. the responder's long-lived publisher client can publish the RPC response; and
7. the health-check client receives and validates that response.

Do **not** use the responder HTTP/static-file server as the responder Docker health check after this change.

---

## Source baseline

Implement against the current Diaries source tree.

Relevant current files include:

```text
diaries/
├── compose.local-docker-build.yaml
├── compose.local-published-smoke.yaml
├── config/mosquitto/aclfile.txt
└── diaries-responder/
    ├── build.gradle
    └── src/main/java/com/rsmaxwell/diaries/responder/
        ├── Responder.java
        ├── config/
        ├── handlers/
        ├── sync/Synchronise.java
        └── utilities/
            ├── DiaryContext.java
            ├── GetEntityManager.java
            └── MyMessageHandler.java
```

The current responder uses the separate `mqtt-rpc` libraries. The current responder Gradle dependencies already include:

```text
mqtt-rpc-common
mqtt-rpc-responder
```

The current `mqtt-rpc-requestor` module provides `RemoteProcedureCall` and `Token` and should be reused for the health-check requestor rather than reimplementing MQTT v5 response-topic/correlation-data handling by hand.

### Current MQTT RPC contract

The normal Diaries request topic is:

```text
diaries/rpc/request
```

`MyMessageHandler.connectComplete(...)` subscribes the responder's long-lived listener client to this topic.

The client-side ACL convention uses a response topic of the form:

```text
diaries/rpc/<mqtt-client-id>/response
```

and the current ACL contains:

```text
pattern read diaries/rpc/%c/response
```

for requestor-style clients.

Use this established convention for the health checker.

---

## Existing defect

Both local responder services currently contain the effective health check:

```yaml
healthcheck:
  test: ["CMD-SHELL", "curl --silent --output /dev/null http://localhost:8081/not-a-responder-path"]
  interval: 10s
  timeout: 5s
  retries: 12
  start_period: 20s
```

The `/not-a-responder-path` request returns HTTP 404. Without `curl --fail`, this normally gives `curl` exit code 0.

The static server also starts before the responder is capable of servicing normal RPC calls, so even a successful HTTP 200 against that server would not be a sufficient readiness test.

The new implementation must remove this coupling between responder health and port 8081.

---

# Required design

## 1. Add a dedicated `health` MQTT RPC operation

Register a new responder RPC handler alongside the existing handlers in `Responder`:

```java
messageHandler.putHandler("health", new Health());
```

A suitable source file is:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/Health.java
```

The health RPC must be deliberately small and must **not require a Diaries user access token**. MQTT authentication and ACLs protect access to the health RPC transport.

It should accept an ordinary request such as:

```json
{
  "function": "health",
  "args": {}
}
```

A successful response should use the normal `mqtt-rpc` success status and a small payload, for example:

```json
{
  "status": "UP"
}
```

or an equivalent small structure consistent with existing DTO/style conventions.

Do not expose credentials, JDBC URLs containing secrets, filesystem paths, stack traces, or other configuration details in the health response.

### Why the RPC itself proves responder/MQTT readiness

Do not add a separate cached boolean merely saying that MQTT was once connected.

If the health request reaches the `Health` handler and its successful response reaches the health-check requestor, then the transaction has already exercised:

- the broker;
- the responder's long-lived MQTT listener;
- its request subscription;
- the RPC dispatcher;
- the responder's long-lived MQTT publisher; and
- the MQTT v5 response-topic/correlation-data path.

This is stronger and less error-prone than asking the responder to report stored MQTT connection flags.

---

## 2. The `health` RPC must perform a live database probe

A successful MQTT round trip alone does not prove PostgreSQL is usable.

The `Health` handler must perform a lightweight live database query equivalent to:

```sql
SELECT 1
```

and only return an RPC success status if that probe succeeds.

### Do not use the responder's shared `EntityManager` for the probe

`DiaryContext` currently holds a long-lived `EntityManager` used by normal responder operations. JPA `EntityManager` instances are not intended for concurrent use by unrelated operations.

Add access to the existing `EntityManagerFactory` to the responder context, or introduce an equivalently small database-health abstraction, so the health handler can do approximately:

```java
EntityManager entityManager = entityManagerFactory.createEntityManager();
try {
    entityManager.createNativeQuery("SELECT 1").getSingleResult();
} finally {
    entityManager.close();
}
```

A suitable minimal change is to add:

```java
private EntityManagerFactory entityManagerFactory;
```

to `DiaryContext`, set it when `Responder.run(...)` creates the factory, and use it only to create the short-lived health-probe `EntityManager`.

Database health must fail if:

- the factory is unavailable or closed;
- an `EntityManager` cannot be created;
- `SELECT 1` fails; or
- any persistence/database exception occurs.

The handler should return a normal non-success `mqtt-rpc` status, preferably `INTERNAL_ERROR`, when the database probe fails. Do not falsely return success with a payload saying the database is down.

Keep failure logging low-noise because Docker may invoke this every 10 seconds during an outage.

---

## 3. Add a small MQTT RPC health-check command to the responder JAR

Docker needs a command whose process exit code represents readiness.

Add a small Java command-line class in the responder project, for example:

```text
com.rsmaxwell.diaries.responder.health.ResponderHealthCheck
```

Its responsibility is only to:

1. read enough configuration to determine the MQTT broker host/port;
2. read the dedicated MQTT health username/password from environment variables;
3. create a uniquely identified short-lived MQTT v5 client;
4. connect to the broker;
5. subscribe to its response topic;
6. issue the `health` RPC to `diaries/rpc/request` using `mqtt-rpc-requestor`;
7. wait for the correlated response;
8. validate that the RPC status is success and the health payload is `UP` (or equivalent);
9. disconnect/close cleanly; and
10. exit **0 only on complete success**, non-zero for every failure.

### Reuse `mqtt-rpc-requestor`

Add the requestor library as a responder implementation dependency in `diaries-responder/build.gradle`, using the existing version-catalog convention, for example:

```gradle
implementation libs.mqtt.rpc.requestor
```

Use `RemoteProcedureCall`, `Request`, `Response`, and the existing MQTT v5 response-topic/correlation-data semantics rather than creating a second home-grown RPC implementation.

No source change to the separate `mqtt-rpc` project should be required.

### Health-check MQTT client ID and response topic

Use a client ID unique enough to avoid collisions between invocations, while preserving the existing ACL `%c` convention. For example:

```text
diaries-health-<short-random-id>
```

and:

```text
diaries/rpc/<client-id>/response
```

Do not use a fixed `requester` client ID because overlapping or stale sessions could interfere with the check.

Use a clean transient MQTT session for the health checker.

### Timeout behaviour

The check must not be able to wait indefinitely for an RPC response.

The current `mqtt-rpc-requestor` `Token.waitForResponse()` has no timeout. Docker itself has a `timeout: 5s`, so Docker will terminate a hung health-check process, but the implementation should still prefer an explicit bounded wait if this can be done cleanly **without changing the mqtt-rpc library**.

If the current requestor API makes an internal timeout awkward, it is acceptable for the Compose `timeout` to be the outer hard bound for this feature. Do not modify `mqtt-rpc` merely to add timeout support as part of this task.

### Configuration and credentials

Use the responder configuration file for broker host/port, for example:

```text
/config/responder.json
```

Do **not** use the normal `diaries-responder` MQTT credentials for the health requestor: the responder ACL is intentionally oriented in the opposite direction (read request / write responses).

Use the existing dedicated health credentials:

```text
DIARIES_MQTT_HEALTH_USERNAME
DIARIES_MQTT_HEALTH_PASSWORD
```

and expose those two variables to the responder container so its health-check subprocess can use them.

Do not print the password in logs or error messages.

---

## 4. Extend the `diaries-health` MQTT ACL narrowly for RPC health checks

The current ACL is approximately:

```text
user diaries-health
topic read $SYS/broker/version
```

The new health checker must be able to act as an RPC requestor. Extend only this dedicated health user with the minimum additional permissions:

```text
user diaries-health
topic read $SYS/broker/version
topic write diaries/rpc/request
pattern read diaries/rpc/%c/response
```

Retain the `$SYS/broker/version` permission because it is still used by the existing Mosquitto service health check.

Do not give `diaries-health` read/write access to retained Diaries business-data topics.

Do not give it the responder's broader ACL.

The response topic used by `ResponderHealthCheck` must include the MQTT client ID exactly where `%c` expects it, otherwise the ACL will reject the subscription.

---

## 5. Update both responder Compose health checks to execute MQTT RPC

Update:

```text
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
```

Remove the HTTP `curl` responder health command completely.

Expose the existing health credentials to the responder service:

```yaml
environment:
  DIARIES_MQTT_HEALTH_USERNAME: ${DIARIES_MQTT_HEALTH_USERNAME}
  DIARIES_MQTT_HEALTH_PASSWORD: ${DIARIES_MQTT_HEALTH_PASSWORD}
```

Preserve any existing responder environment such as `CONFIG_FILE`.

Use the responder fat JAR to invoke the dedicated health-check main class. A suitable form is:

```yaml
healthcheck:
  test:
    [
      "CMD-SHELL",
      "java -cp /opt/diaries/diaries-responder.jar com.rsmaxwell.diaries.responder.health.ResponderHealthCheck --config /config/responder.json",
    ]
  interval: 10s
  timeout: 5s
  retries: 12
  start_period: 20s
```

Adjust the exact JAR path only if the published Dockerfile uses a different final path. The local inline image currently uses:

```text
/opt/diaries/diaries-responder.jar
```

Make the local and published responder images support the same command/path where practical.

The checker must return process exit code:

```text
0     RPC health transaction succeeded and DB probe succeeded
non-0 any connection, authentication, subscription, publish, response, RPC-status, payload or DB-health failure
```

Keep the current health timing values unless testing demonstrates a concrete need to change them.

### Remove the previous `curl` requirement

Because responder health no longer uses HTTP, do **not** add `curl` to the local-docker-build responder image for this feature.

If `curl` is already present in the published responder Dockerfile for unrelated operational/debugging reasons, it may remain; removing it is outside this task.

---

## 6. Make `local-docker-build` client wait for responder health

`compose.local-published-smoke.yaml` already contains:

```yaml
depends_on:
  diaries-responder:
    condition: service_healthy
```

`compose.local-docker-build.yaml` currently has only:

```yaml
depends_on:
  - diaries-responder
```

Change the local-docker-build client to match published-smoke exactly in semantics:

```yaml
depends_on:
  diaries-responder:
    condition: service_healthy
```

This change is explicitly part of this implementation.

After the change, in both local Docker modes the client must not be started merely because the responder container process has started. It must wait until the responder successfully completes the MQTT RPC health transaction.

---

## 7. Preserve normal responder lifecycle behaviour

Do not restructure startup unnecessarily.

The current lifecycle is broadly:

1. read configuration;
2. start the static HTTP/file server;
3. create JPA resources/context/repositories;
4. perform `Synchronise.perform(...)` using temporary MQTT clients;
5. create/connect the long-lived responder publisher and listener clients;
6. subscribe listener to `diaries/rpc/request` from `MyMessageHandler.connectComplete(...)`;
7. wait for and process RPC requests.

The health RPC naturally remains unavailable until step 6/7 because no long-lived listener is servicing the request topic before then.

This is desirable. Do not artificially publish a separate `ready=true` state during startup.

### Important: temporary synchronisation clients are not readiness

`Synchronise.perform(...)` uses temporary MQTT clients and disconnects them before normal responding starts.

Do not base Docker responder health on successful startup synchronisation alone.

Only a successful health RPC serviced by the normal long-lived responder clients counts as ready.

---

# Failure semantics

The resulting Docker health behaviour must be approximately:

| Situation | MQTT RPC health result | Docker responder state |
|---|---|---|
| Java process/static HTTP server started, DB initialization still running | no successful RPC response | starting/unhealthy |
| Startup synchronisation still running | no successful RPC response | starting/unhealthy |
| Long-lived listener not connected/subscribed | request times out/fails | unhealthy |
| Mosquitto unavailable | checker cannot connect / request fails | unhealthy |
| MQTT ACL/authentication failure | checker fails | unhealthy |
| Responder listener connected but publisher unavailable | no valid response | unhealthy |
| Database unavailable | `health` handler returns non-success RPC status | unhealthy |
| DB healthy + complete MQTT RPC request/response succeeds | RPC success + `UP` | healthy |
| Later MQTT outage/reconnect period | health RPC fails | unhealthy |
| MQTT recovers and responder re-subscribes | health RPC succeeds again | healthy |
| Later DB outage | health RPC returns failure | unhealthy |
| DB recovers | health RPC succeeds again, assuming responder persistence remains usable | healthy |
| Static HTTP `/diaries` or `/files` responds | irrelevant | does not by itself imply health |

The responder process does **not** need to exit merely because readiness is temporarily false. Existing Paho automatic reconnect behaviour should remain intact.

---

# Tests to add

Add focused tests at the responder level. Do not require a real Mosquitto or PostgreSQL instance for ordinary unit tests.

## Health handler tests

At minimum verify:

1. successful `SELECT 1` returns normal RPC success and an `UP` payload;
2. inability to create the health-probe `EntityManager` returns non-success;
3. failed database query returns non-success;
4. the short-lived health `EntityManager` is closed after success;
5. it is also closed after failure;
6. the normal shared `DiaryContext.entityManager` is not used for the health probe;
7. health response contains no credentials or connection details.

Make the DB probe testable with a small abstraction/factory seam if mocking `EntityManagerFactory` directly becomes awkward. Keep the design proportionate.

## Health-check command tests

Factor the command so important exit-code/result mapping can be tested without a real broker.

At minimum verify that the command reports failure for:

1. MQTT connection failure;
2. response-topic subscription failure;
3. request publish failure;
4. missing/no response;
5. non-success RPC status;
6. malformed/unexpected health payload;

and success only for a valid successful `health` RPC response.

Do not make tests depend on real passwords.

## Compose/config checks

Where existing project test conventions allow, add a lightweight regression check or document manual verification that:

- both responder health checks invoke `ResponderHealthCheck` rather than `curl`;
- both responder services receive `DIARIES_MQTT_HEALTH_USERNAME/PASSWORD`;
- `local-docker-build` client uses `condition: service_healthy`;
- `local-published-smoke` retains `condition: service_healthy`;
- `diaries-health` ACL permits only the required RPC request/response topics plus its existing `$SYS` read.

---

# Manual/integration verification

## Build/test

From the `diaries` project root:

```text
./gradlew :diaries-responder:test
./gradlew :diaries-responder:shadowJar
```

Use `gradlew.bat` on Windows as appropriate.

Confirm the fat JAR contains the requestor classes required by `ResponderHealthCheck`.

---

## Direct health-check command

With the local stack running and the health environment variables set inside the responder container, run the same command Docker uses, for example:

```text
docker exec diaries-local-responder \
  java -cp /opt/diaries/diaries-responder.jar \
  com.rsmaxwell.diaries.responder.health.ResponderHealthCheck \
  --config /config/responder.json
```

Expected:

```text
exit code 0
```

when the responder is genuinely usable.

The normal successful invocation should be quiet or very concise so Docker health polling does not flood logs.

---

## Startup window

Start `local-docker-build` from a stopped state.

Confirm:

1. PostgreSQL becomes healthy;
2. Mosquitto becomes healthy;
3. responder process starts;
4. responder remains `starting` while responder initialization/synchronisation is incomplete;
5. the responder becomes `healthy` only after its normal long-lived MQTT RPC listener/publisher can service the `health` request and the database probe succeeds; and
6. `diaries-client` starts only after responder health becomes healthy.

This directly verifies the requested `condition: service_healthy` change.

---

## MQTT failure/recovery

With the responder initially healthy:

1. stop or make Mosquitto unavailable;
2. verify responder Docker health becomes unhealthy because the MQTT RPC checker fails;
3. restore Mosquitto;
4. allow existing Paho automatic reconnect/re-subscription to run;
5. verify the responder becomes healthy again once the `health` RPC completes successfully.

This test must exercise the real RPC request/response path rather than an MQTT broker-only `$SYS` query.

---

## Database failure/recovery

With the responder initially healthy:

1. make PostgreSQL unavailable;
2. verify the MQTT request can no longer produce a successful `health` result and Docker marks the responder unhealthy;
3. restore PostgreSQL;
4. verify health returns to success if the existing persistence resources recover;
5. if the existing responder persistence model requires a restart after a DB outage, it is acceptable for the responder to remain unhealthy until restart—the critical requirement is that it never falsely reports healthy while `SELECT 1` fails.

---

## ACL verification

Using `diaries-health` credentials, verify it can:

- publish to `diaries/rpc/request`;
- subscribe only to its own matching `diaries/rpc/<client-id>/response` topic through `%c`;
- continue reading `$SYS/broker/version` for the broker service health check.

Also verify those credentials do **not** gain access to retained Diaries content topics such as:

```text
diaries/diaries/#
diaries/pages/#
diaries/fragments/#
diaries/marquees/#
```

---

## False-positive regression check

Verify that the embedded HTTP server may still respond on port 8081 while responder health is not yet ready, but this has no effect on Docker responder health.

For example, a request such as:

```text
http://localhost:8081/not-a-responder-path
```

may still return 404 exactly as before. That response must now be completely irrelevant to Docker responder health.

---

# Files expected to change

The implementation will likely change/add approximately:

```text
diaries/compose.local-docker-build.yaml
diaries/compose.local-published-smoke.yaml
diaries/config/mosquitto/aclfile.txt

diaries/diaries-responder/build.gradle
diaries/diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java
diaries/diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java
diaries/diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/Health.java                         # new
diaries/diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/health/ResponderHealthCheck.java           # new
diaries/diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/...                                         # new/updated tests
```

Depending on the current version catalog, the root Gradle catalog file may also need a small change if `libs.mqtt.rpc.requestor` is not already defined.

If the published responder Dockerfile uses a different JAR location or launcher arrangement, update it only as required to make the same health-check command available in `local-published-smoke`.

No source change to the separate `mqtt-rpc` repository should be necessary.

---

# Non-goals

Do not turn this into a broader health/observability redesign.

This work does **not** require:

- an HTTP `/health/ready` endpoint;
- Spring Boot, Micronaut, Quarkus, or another web framework;
- Prometheus metrics;
- Kubernetes probes;
- a database schema change;
- changes to retained topic-tree structures;
- changes to the Angular application RPC contract;
- changes to existing business RPC authentication;
- a separate liveness check;
- changing `/diaries` or `/files` static HTTP behaviour;
- changing the MQTT RPC protocol; or
- changes to the `mqtt-rpc` project unless Codex discovers a genuinely blocking defect and clearly reports it rather than silently broadening the task.

---

# Acceptance criteria

The work is complete when all of the following are true:

- [ ] A new unauthenticated responder MQTT RPC function named `health` is registered on the normal `diaries/rpc/request` path.
- [ ] The health handler performs a live database probe equivalent to `SELECT 1`.
- [ ] The DB probe uses a separate short-lived `EntityManager`, not the responder's shared long-lived `EntityManager`.
- [ ] A failed DB probe produces a non-success RPC response.
- [ ] A successful health RPC returns a small `UP` payload with no sensitive information.
- [ ] A `ResponderHealthCheck` command exists in the responder fat JAR.
- [ ] The command performs a genuine MQTT v5 RPC request/response transaction using the existing `mqtt-rpc-requestor` implementation.
- [ ] The health-check MQTT client uses a unique client ID and a response topic `diaries/rpc/<client-id>/response` compatible with the `%c` ACL pattern.
- [ ] The command exits 0 only after a valid successful `health` RPC response is received.
- [ ] The command exits non-zero for MQTT connection/authentication/subscription/request/response failures, non-success RPC status, or invalid health payload.
- [ ] Both local Compose responder health checks execute `ResponderHealthCheck`; neither uses HTTP/curl to determine responder health.
- [ ] Both responder containers receive `DIARIES_MQTT_HEALTH_USERNAME` and `DIARIES_MQTT_HEALTH_PASSWORD` for the health-check subprocess.
- [ ] The `diaries-health` ACL retains `$SYS/broker/version` read access and gains only the minimum RPC requestor permissions required for health checking.
- [ ] `diaries-health` is not granted access to retained Diaries business-data topics.
- [ ] The existing temporary MQTT clients in `Synchronise.perform(...)` are not treated as proof of readiness.
- [ ] A successful check necessarily traverses the responder's normal long-lived MQTT listener and publisher clients.
- [ ] `compose.local-published-smoke.yaml` continues to make its client depend on `diaries-responder: condition: service_healthy`.
- [ ] `compose.local-docker-build.yaml` is changed so its client also depends on `diaries-responder: condition: service_healthy`.
- [ ] The client therefore does not start in either Docker mode until responder MQTT RPC readiness succeeds.
- [ ] Existing responder HTTP `/diaries` and `/files` serving continues unchanged.
- [ ] Existing Paho automatic reconnect and `MyMessageHandler` re-subscription behaviour remains intact.
- [ ] Focused automated tests cover the DB health handler and health-check command result semantics.
- [ ] `:diaries-responder:test` passes.
- [ ] `:diaries-responder:shadowJar` builds successfully.
- [ ] Manual Docker verification confirms startup, MQTT outage, and DB outage do not produce a false healthy state.

---

# Implementation quality guidance

Prefer the MQTT RPC transaction itself as the readiness truth rather than maintaining duplicated cached readiness state.

Keep the health RPC cheap. One `SELECT 1` per Docker health interval is sufficient.

Keep the health request unauthenticated at the Diaries application-token level, but tightly constrained by the dedicated Mosquitto `diaries-health` account and ACL.

Reuse existing configuration parsing and MQTT-RPC classes where possible. Avoid duplicating broker URL construction, JSON request/response parsing, correlation handling, or response-topic conventions.

Keep successful health-check output minimal because it runs every 10 seconds.

Preserve current responder/client behaviour unless a change is directly required for accurate readiness.

When finished, Codex should report:

1. files changed;
2. exact MQTT RPC health request/response contract implemented;
3. ACL changes;
4. Compose health-check and dependency changes;
5. automated test results;
6. manual Docker verification performed; and
7. any assumptions or follow-up concerns discovered.
