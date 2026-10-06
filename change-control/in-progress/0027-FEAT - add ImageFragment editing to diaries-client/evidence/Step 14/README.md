# Step 14 — full client/responder/reader regression and rollout rehearsal

**Status: IMPLEMENTED / WORKSTATION EXECUTION PENDING — 2026-10-05.**

Step 14 is implemented as a repeatable verification/rehearsal harness. It does not claim acceptance merely because the scripts exist. The real run must execute on the Windows development workstation with Angular dependencies, Java 25, Docker/Testcontainers, Chrome/Edge and the disposable 0026 reader fixture prerequisites available.

Step 14 deliberately verifies the three live application surfaces together:

- `diaries-client`: full Angular/Karma regression and production build;
- `diaries-responder`: full Java regression/build, including ImageFragment create/update/delete chronology, authoring gate and Image delete-reference guard contracts;
- `diaries-web`: full Java regression/build plus the existing 0026 disposable browser/MQTT/HTTP reader verification against the current responder/web source candidate.

It also performs a read-only rehearsal of the production rollout ordering while `imageFragmentWritesEnabled` remains false. No Step 14 tool enables production authoring, mutates production, runs Ansible, or copies credentials into evidence.

## Prerequisite

Step 13 must be closed before Step 14 can be closed. The Step 14 tooling may be installed earlier, but a green Step 14 run is not a substitute for Step 13's live editor/responder/database/MQTT/Files lifecycle evidence.

In particular, Step 13 proves that the client actually emits and consumes the authoring contract. Step 14 then proves that the complete regression surface and reader remain compatible with that contract.

## Implemented tooling

All feature-specific tooling remains under this evidence directory, not in the live `scripts/` tree:

- `tooling/step14-begin.ps1` creates an ignored `build/0027-step14/runs/<timestamp>/` evidence run;
- `tooling/step14-preflight.ps1` checks workstation prerequisites, Docker, Angular dependencies, Java 25, the disposable reader-verification prerequisites and the authoring-gate default;
- `tooling/step14-run-regression.ps1` invokes the permanent disposable `scripts/windows/validation/test-image-catalogue.ps1` gate so the responder's environment-gated JPA/MQTT tests execute rather than skip, validates required named contracts in JUnit/Karma output, reruns the disposable 0026 reader browser verification using the current source candidate, renders both local Compose modes with `config --quiet`, and writes a machine-readable summary;
- `tooling/check-step14-test-reports.py` verifies that the required responder/web test classes and named lifecycle/reader cases actually executed without failures/errors/skips rather than merely relying on a successful Gradle exit code;
- `tooling/step14-rollout-rehearsal.ps1` performs a non-destructive source/configuration rehearsal of the Step 15 production order and, when given the Playbooks repository, verifies the actual Diaries role keeps `imageFragmentWritesEnabled=false`, preserves the static `files` reader path, validates before pull/start, waits for service health, and only then activates the shared Nginx route;
- `tooling/step14-finalize.ps1` is the closure guard: it refuses to produce a passing final summary unless Step 13 is marked closed, the regression/report/reader summaries pass, the source hash inventory exists, and the production-role rehearsal proves the gate stayed false;
- `validate-step14-tooling.py` statically validates the committed Step 14 harness.

`RUNBOOK.md`, `CHECKLIST.md` and `MANUAL-EVIDENCE.md` define the operator sequence and closure evidence.

## Regression mapping

Step 14 also repairs one permanent regression-tooling dependency discovered during implementation: `scripts/windows/validation/test-image-catalogue.ps1` no longer reads a deleted 0024 historical-evidence Mosquitto file. Its broker fixture is now the permanent `scripts/windows/validation/image-catalogue-test-mosquitto.conf`, keeping the reusable regression gate independent of completed-feature evidence cleanup. That fixture is deliberately authentication-neutral and loopback-published because it is a functional disposable broker shared by credential-bearing responder MQTT clients and the anonymous browser fixture; production password/ACL policy is not weakened. The permanent gate also provisions its MQTT WebSocket listener and browser-test environment so the opt-in Files-dialog deletion integration case executes instead of being reported as skipped.

Step 14 maps the implementation-plan work to executable evidence as follows:

1. **Normal client tests/build** — full Karma run in ChromeHeadless followed by the production Angular build.
2. **Responder ImageFragment regression** — full responder test/build plus named report assertions for gate semantics, create/update/delete chronology, shared Image references, cross-type rejection and `DeleteImage` conflict protection.
3. **0026 reader compatibility** — full `diaries-web` test/build plus the existing disposable browser-level `verify-imagefragment-reader.ps1` runner against the current responder/web candidate.
4. **Legacy MARQUEE regression** — full client/responder/web suites plus named MARQUEE creation/mixed chronology/reader tests; the disposable reader runner starts from the supplied pre-IMAGE backup and adds owned fixture data rather than converting legacy content.
5. **Restart/replay** — named MQTT projection/reconnect tests plus responder/web restart inside the disposable reader verification.
6. **Static Files URL resolution** — web `RenderingSafetyTest`, HTTP checks and real disposable Image-byte/browser verification.
7. **Image delete guard** — responder `DeleteImageTest`, shared-reference lifecycle test and disposable reference-aware delete check.
8. **Production-order rehearsal with gate false** — read-only Step 15/order checks, optionally bound to the current Playbooks role source.

## Safety properties

- No production database, broker, Files tree or host is contacted by the regression runner.
- The 0026 reader browser verification creates isolated Docker containers/network and records that live development/production datasets were not modified.
- The production rehearsal reads source/templates only; it does not run a playbook or SSH to `pluto`.
- Gate enablement is explicitly outside Step 14. The rehearsal fails if the supplied production responder template does not keep `imageFragmentWritesEnabled` false.
- Evidence contains command/test/build output, source hashes and configuration assertions, not MQTT/database/application credentials.

## Completion gate

Step 14 may be closed only when one workstation run records:

- full client tests and production build PASS;
- full responder tests/build PASS with the required named lifecycle/delete-guard contracts executed and not skipped;
- full web tests/build PASS with required projection/restart/static-URL contracts executed and not skipped;
- disposable reader browser verification PASS against the current candidate;
- both local Compose configurations render successfully;
- rollout rehearsal PASS with the production authoring gate false;
- client, responder and reader source/config hashes captured for the same run;
- no unresolved regression or skipped required test.

A source-package environment without `node_modules`, Docker/Chrome or the Java toolchain may validate the Step 14 tooling, but it must not mark Step 14 complete. The authoritative closure signal is `build/0027-step14/runs/<id>/step14-final-summary.json` produced by `step14-finalize.ps1`.
