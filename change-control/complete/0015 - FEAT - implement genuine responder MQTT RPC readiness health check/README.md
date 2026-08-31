# 0015-FEAT - Implement genuine responder MQTT RPC readiness health check

## Type

Feature

## Status

In progress

## Priority

High

## Opened

2026-08-31

## Summary

Replace the responder's false-positive HTTP-based Docker health check with a genuine end-to-end MQTT RPC readiness check. The check must exercise the normal long-lived responder MQTT listener and publisher, perform a live PostgreSQL probe, and return process exit code 0 only when the complete request/response transaction succeeds.

## Background

The responder health checks in `compose.local-docker-build.yaml` and `compose.local-published-smoke.yaml` currently request a deliberately nonexistent HTTP URL without using `curl --fail`. An HTTP 404 therefore normally produces exit code 0 and can mark the responder healthy merely because its static HTTP server is listening.

This does not demonstrate application readiness. The static server starts before database initialization, startup MQTT synchronization, and creation of the responder's long-lived MQTT clients. The Diaries client depends on the MQTT RPC path, while PostgreSQL is the durable source of truth, so readiness must verify both in one end-to-end operation.

The detailed source requirements are recorded in:

`change-control/correspondance/2026-08-31 Improve responder healthcheck/diaries-responder-readiness-codex-spec.md`

## Observed Behaviour

Both local Docker modes currently use the effective responder health command:

```yaml
curl --silent --output /dev/null http://localhost:8081/not-a-responder-path
```

The request returns HTTP 404, but `curl` normally exits successfully because `--fail` is absent. Docker can consequently report a healthy responder while database initialization, MQTT synchronization, or normal RPC listener/publisher startup is incomplete or has failed.

## Expected Behaviour

A responder health check is successful only when a dedicated short-lived MQTT client can:

1. connect and authenticate to Mosquitto using the dedicated `diaries-health` account;
2. subscribe to its client-specific response topic;
3. send a `health` request to `diaries/rpc/request`;
4. have the request dispatched by the responder's normal long-lived listener;
5. have the responder execute a live database query equivalent to `SELECT 1` using a short-lived `EntityManager`;
6. receive the correlated response from the responder's normal long-lived publisher; and
7. validate a successful RPC status and an `UP` payload.

The command must exit 0 only after complete success and non-zero for every connection, authentication, authorization, subscription, publication, timeout, response, RPC-status, payload-validation, or database-probe failure.

Responder readiness must no longer depend on the HTTP/static-file server. Existing `/diaries` and `/files` serving remains unchanged.

## Evidence

- Requirements and current-behaviour analysis: `change-control/correspondance/2026-08-31 Improve responder healthcheck/diaries-responder-readiness-codex-spec.md`
- Current Compose definitions: `compose.local-docker-build.yaml` and `compose.local-published-smoke.yaml`
- Current MQTT authorization rules: `config/mosquitto/aclfile.txt`
- Current responder startup and RPC wiring: `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java` and `MyMessageHandler.java`

## Analysis

The current health check proves only that the embedded HTTP server has accepted a connection. It does not prove that the broker, responder RPC subscription, responder RPC publisher, or database is usable.

The readiness transaction itself should be the source of truth rather than a cached readiness flag. If a correctly correlated `health` reply reaches the short-lived requestor, the request has necessarily passed through the broker, the responder's normal request subscription and dispatcher, and its normal response publisher. Adding a live database probe to the handler completes the readiness path without changing startup sequencing or treating the temporary clients used by startup synchronization as proof of readiness.

## MQTT RPC Contract

Request topic:

```text
diaries/rpc/request
```

Request payload:

```json
{
  "function": "health",
  "args": {}
}
```

Response topic convention:

```text
diaries/rpc/<mqtt-client-id>/response
```

Successful payload:

```json
{
  "status": "UP"
}
```

The response must use the existing `mqtt-rpc` success status. A database-probe failure must use a normal non-success RPC status, preferably `INTERNAL_ERROR`, rather than returning a success payload that reports degraded health. The operation does not require a Diaries user access token; transport access is restricted by MQTT authentication and ACLs.

The response must not expose credentials, secret-bearing connection strings, filesystem paths, stack traces, or configuration details.

## Scope

### Diaries Client

No Angular application RPC or presentation change is required. In both local Docker modes, client container startup must depend on the responder becoming healthy. `local-docker-build` must be changed to use `condition: service_healthy`, matching the existing published-smoke semantics.

### Diaries Responder

- Register a dedicated unauthenticated `health` handler on the existing RPC dispatcher.
- Perform a lightweight live database probe equivalent to `SELECT 1`.
- Give the health probe access to the existing `EntityManagerFactory`, or an equivalently small abstraction, so it creates and always closes a separate short-lived `EntityManager`.
- Do not use the shared long-lived `DiaryContext.entityManager` for health probes.
- Add a `ResponderHealthCheck` command-line entry point to the responder fat JAR.
- Reuse the existing responder configuration parsing for broker host and port where practical.
- Reuse `mqtt-rpc-requestor` for MQTT v5 response-topic and correlation-data handling.
- Use a unique, clean-session MQTT client ID such as `diaries-health-<short-random-id>`.
- Read only `DIARIES_MQTT_HEALTH_USERNAME` and `DIARIES_MQTT_HEALTH_PASSWORD` for health-requestor authentication, without logging the password.
- Preserve current responder startup ordering, automatic reconnect, listener re-subscription, business RPC authentication, and HTTP/static-file behaviour.

### MQTT Contract and Retained State

- Add only the `health` RPC function to the normal `diaries/rpc/request` path.
- Preserve existing MQTT v5 response-topic and correlation-data behaviour.
- Add `mqtt-rpc-requestor` as a responder implementation dependency using the existing version-catalog convention.
- Do not modify the retained Diaries topic tree or publish a separate cached readiness topic or flag.
- Do not change the separate `mqtt-rpc` project unless a genuinely blocking defect is found and recorded for a scope decision.

The `diaries-health` ACL must retain its existing broker health access and gain only:

```text
topic read $SYS/broker/version
topic write diaries/rpc/request
pattern read diaries/rpc/%c/response
```

It must not gain access to retained Diaries business-data topics or the responder's broader permissions.

### Database

The health handler must execute a live query equivalent to `SELECT 1`. It must fail when the `EntityManagerFactory` is absent or closed, an `EntityManager` cannot be created, the query fails, or another persistence/database exception occurs.

No schema or data migration is required. Health checking must not modify diary data.

### Images and Static Files

No image, NAS, upload, static routing, or HTTP endpoint changes are required. Static HTTP availability must not influence Docker responder health after this feature.

### Build, Configuration, and Deployment

- Replace the responder HTTP/curl health command in both local Compose modes with execution of `ResponderHealthCheck` from the responder fat JAR.
- Pass `DIARIES_MQTT_HEALTH_USERNAME` and `DIARIES_MQTT_HEALTH_PASSWORD` into both responder containers while preserving existing environment and configuration mounts.
- Keep the current health timing values unless validation identifies a concrete reason to change them.
- Confirm the local and published responder images expose a consistent JAR path/command where practical.
- Do not add `curl` to the local responder image for this feature.
- Preserve the Mosquitto `$SYS/broker/version` service health check.
- Review the published responder Dockerfile only if required to make the same command available in `local-published-smoke`.
- Production/Ansible changes are outside the defined implementation unless inspection shows the same false-positive responder health check is generated there; any such discovery must be reported before broadening scope.

### Documentation

Update responder, configuration, or local-mode documentation only where it describes the previous responder health-check behaviour or needs to document the new health command and environment requirements.

## Implementation Steps

- [x] Reconfirm the current health commands, responder JAR location, startup sequence, handler conventions, RPC DTO/status APIs, and requestor-library API against the active source tree.
- [x] Add focused failing tests for the health handler's successful and failed database-probe paths, short-lived `EntityManager` cleanup, isolation from the shared context manager, and non-sensitive response.
- [x] Add a proportionate `EntityManagerFactory` or database-probe seam to the responder context.
- [x] Implement and register the unauthenticated `health` RPC handler.
- [x] Add `mqtt-rpc-requestor` to the responder runtime/fat-JAR dependencies.
- [x] Factor and test the health-check command's success and exit-failure mapping without requiring a real broker or database.
- [x] Implement `ResponderHealthCheck` with a unique client ID, matching response topic, clean transient session, bounded execution, complete response validation, and quiet normal output.
- [x] Extend only the `diaries-health` MQTT ACL with the minimum RPC requestor permissions.
- [x] Update both responder Compose health checks and expose the two dedicated health credential variables.
- [x] Change the local-docker-build client dependency to `condition: service_healthy` and confirm published-smoke retains that condition.
- [x] Update affected documentation.
- [x] Run responder unit tests and build the fat JAR; confirm it contains the required requestor classes.
- [x] Validate both Compose configurations.
- [ ] Perform local Docker startup and healthy-path verification.
- [ ] Verify MQTT outage/recovery and database outage/recovery do not produce false healthy states.
- [ ] Verify the dedicated ACL permits only the intended broker-health and RPC requestor operations.
- [x] Review the final Git diff for unrelated changes and record actual validation evidence.

## Acceptance Criteria

- [x] A responder MQTT RPC function named `health` is registered on `diaries/rpc/request` without requiring a Diaries user access token.
- [x] The handler performs a live database probe equivalent to `SELECT 1`.
- [x] The probe creates and always closes a separate short-lived `EntityManager`; it never uses the shared long-lived `DiaryContext.entityManager`.
- [x] An unavailable/closed factory, entity-manager creation failure, failed query, or persistence exception produces a non-success RPC response.
- [x] A successful request returns the normal RPC success status with a small `UP` payload containing no sensitive details.
- [x] `ResponderHealthCheck` is present in the responder fat JAR and uses the existing `mqtt-rpc-requestor` implementation.
- [x] The command uses a unique MQTT client ID and subscribes to `diaries/rpc/<client-id>/response`, compatible with the `%c` ACL rule.
- [x] The command exits 0 only for a correlated successful `health` response with a valid `UP` payload.
- [x] The command exits non-zero for connection/authentication, subscription, publish, missing/timeout response, non-success RPC status, or malformed/unexpected payload failures.
- [x] The health-check execution has an explicit or Docker-enforced hard timeout and cannot wait indefinitely.
- [x] Both local Compose responder health checks execute `ResponderHealthCheck` and no longer use HTTP/curl to determine responder health.
- [x] Both responder containers receive `DIARIES_MQTT_HEALTH_USERNAME` and `DIARIES_MQTT_HEALTH_PASSWORD` without exposing their values.
- [x] `diaries-health` retains `$SYS/broker/version` read access and gains only write access to `diaries/rpc/request` plus `%c`-scoped read access to its own response topic.
- [x] `diaries-health` cannot read or write retained Diaries business-data topics.
- [x] `local-docker-build` and `local-published-smoke` clients both depend on `diaries-responder` with `condition: service_healthy`.
- [x] Startup synchronization's temporary MQTT clients are not used as readiness evidence; success traverses the responder's normal long-lived listener and publisher.
- [x] Existing responder startup ordering, automatic reconnect/re-subscription, business RPC authentication, HTTP `/diaries` and `/files` serving, and retained state remain unchanged.
- [x] Focused unit tests cover database health handling and health-check command result semantics without requiring real credentials, Mosquitto, or PostgreSQL.
- [x] `gradlew.bat :diaries-responder:test` passes.
- [x] `gradlew.bat :diaries-responder:shadowJar` passes and the fat JAR contains its requestor dependencies.
- [x] `docker compose config` succeeds for both affected local modes with the intended environment supplied safely.
- [ ] Manual Docker validation proves the responder stays starting/unhealthy until the complete RPC and database check succeeds.
- [ ] Manual MQTT and database outage tests do not produce a false healthy state, and recovery behaviour is recorded.

## Validation

### Responder Tests and Build

Commands:

```text
gradlew.bat :diaries-responder:test :diaries-responder:shadowJar --no-daemon
```

Result: Passed on 2026-08-31 using the repository wrapper with a workspace-local Gradle user home. All 21 tests passed with no failures, errors, or skips. `shadowJar` completed successfully. The resulting fat JAR contains `ResponderHealthCheck`, `Health`, `RemoteProcedureCall`, and `Token`. Existing Shadow service-file duplicate warnings remain and are unrelated to this change.

### MQTT and Database Verification

Method: Exercise the health command against the local stack, verify its RPC request/reply contract, stop and restore Mosquitto, stop and restore PostgreSQL, and observe responder Docker health transitions. Confirm the database probe is live rather than cached.

Result: Unit coverage passed for successful and failed live-probe semantics and for connection, subscription, request, timeout, RPC-status, and payload result mapping. Live MQTT/database outage and recovery verification remains pending because the available development configuration targets the user's NAS, database, and retained MQTT state and was not authorized for that operational test.

### Docker or Application Smoke Test

Modes: `local-docker-build` and `local-published-smoke`.

Method:

- validate both rendered Compose configurations;
- start each applicable mode from a stopped state;
- run the exact health command inside the responder container;
- confirm exit code 0 only on complete readiness;
- confirm the client waits for responder health;
- confirm an HTTP 404 from `/not-a-responder-path` has no bearing on responder health.

Result: Both Compose files rendered successfully. An additional rendered-config assertion verified the expected JAR path, `ResponderHealthCheck` command, absence of curl from responder health, both health environment variables, and `condition: service_healthy` for both clients. `local-published-smoke` reported pre-existing warnings that its database variables are unset. Container startup was not performed because the development database and broker containers already occupy the default ports, and using the available live responder configuration requires separate authorization.

### ACL Verification

Method: With `diaries-health` credentials, verify broker-version read, request publication, and client-ID-matched response subscription succeed. Verify subscriptions/publications against retained diary, page, fragment, and marquee topics are denied.

Result: Static validation passed: the complete `diaries-health` ACL section exactly contains the existing `$SYS/broker/version` read plus request-topic write and `%c`-scoped response-topic read. Runtime positive/negative ACL verification remains pending with the live Docker smoke test.

## Deployment and Rollback Notes

No database migration or data backup is required because the feature performs only a read-only probe. The dedicated health credentials must already be present in the selected environment source and Mosquitto password file; their values must remain outside version control.

Deployment must keep the responder JAR, Compose health command, environment-variable wiring, Mosquitto ACL, and password-file account aligned. A partial deployment can leave the responder unhealthy even when normal processing is otherwise available.

Rollback consists of reverting the responder handler/command/dependency, ACL additions, Compose health commands, health environment wiring, and local client dependency change as one coherent unit. Reintroducing the known false-positive HTTP command is not an acceptable long-term health design; if rollback is necessary, record the temporary operational risk.

## Non-goals

- An HTTP readiness endpoint or web framework.
- Prometheus metrics, Kubernetes probes, or a broader observability redesign.
- A separate liveness check.
- Database schema or retained-topic-tree changes.
- Changes to Angular RPC payloads or existing business RPC authentication.
- Changes to `/diaries` or `/files` HTTP behaviour.
- Changes to the MQTT RPC protocol or separate `mqtt-rpc` project unless a blocking defect is found and separately assessed.

## Git References

Record only repositories actually changed during implementation.

### Diaries Parent Repository

- Branch: `main`
- Commits:
- Pull request:

### Diaries Responder

- Branch: `main`
- Commits:
- Pull request:

## Completion Summary

Implementation is complete in source: the responder exposes a database-backed `health` RPC, the fat JAR contains a bounded MQTT RPC requestor command, the dedicated ACL is narrowly extended, both Compose health checks use the command, and both clients wait for responder health. Automated tests, fat-JAR inspection, Compose rendering, and static ACL validation passed. The change remains in progress until authorized live startup, outage/recovery, and runtime ACL verification are completed.

## Completed Date

Not complete.
