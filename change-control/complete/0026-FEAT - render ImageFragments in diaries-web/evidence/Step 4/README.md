# 0026 Step 4 — reader subscriptions and minimum broker permissions

**Complete locally — 2026-09-28.** The active reader now subscribes to all five canonical lookup families and the shared broker ACL grants the actual `diaries-web` identity read-only Image access. The full web suite/build passed: **107 tests, zero failures, errors or skips**, including six authenticated Docker integration tests. Production deployment remains a later release activity.

## Scope and source attribution

Initial inspection found the supplied Step-4 files under an extra nested `diaries/diaries/` directory, outside the active Gradle source tree. During this task they became available at the correct active paths. The original `test-results.txt` is preserved, but cannot establish that the new ACL test class ran: Gradle can match the other classes in a multi-filter command even when one requested class is absent. The final reports here explicitly contain `MqttReaderAclIntegrationTest` and `MqttSubscriptionTest`.

The supplied package also assumed that Mosquitto file ACLs reject forbidden SUBSCRIBE requests. The first explicit active-tree ACL run failed two of three tests. Those failures are retained in `acl-initial.log` and `initial-test-reports/`. A subsequent check of the reader's own client-ID RPC reply topic exposed a real permission leak from the shared global pattern rule (`rpc-pattern-check.log`, `rpc-pattern-failure.xml`). A web-user deny closes that leak. The implementation/test corrections below were then validated against the active workspace. No existing Step-2/3 source work was discarded.

`source-sha256.csv` identifies the 12 active source/config/documentation files for this step; `package-source-sha256.csv` preserves the original supplied inventory. These are historical inventories, not a claim that later implementation steps must leave their files unchanged.

## Changes and acceptance evidence

| Step-4 requirement | Implementation and evidence |
| --- | --- |
| Canonical Image subscription | `TopicParser.canonicalFilters()` returns exactly diaries/pages/fragments/marquees/images single-level lookup filters under the configured prefix. `RetainedContractTest` checks the exact set. QoS 1 and configured clean-start/reconnect policy are preserved. |
| Check every SUBACK | `MqttProjectionClient` submits the five subscriptions together and requires one successful reason code per filter before acknowledging replay. Missing/truncated/extra/invalid/rejected acknowledgements fail readiness. |
| No partial state after explicit rejection | Acceptance stops on failure/disconnect. A lock serializes callback enqueues with failure/disconnect enqueues so an already-running callback cannot place an upsert after staging is discarded. A local MQTT-5 test peer supplies four grants plus Image rejection with an earlier retained Diary; the real Paho callback path remains unready and the active snapshot stays empty, including after a late callback. |
| Minimum actual reader permission | `config/mosquitto/aclfile.txt` adds `topic read diaries/images/+` and a user-scoped `topic deny diaries/rpc/#` to override the shared client-ID reply pattern. Other users' rules are unchanged. The new Docker suite loads that exact committed ACL, appending only isolated test publisher/negative-control identities. It authenticates as `diaries-web`, not an alias with potentially different permissions. |
| Image replay works | The actual identity receives retained Image metadata. The actual `MqttProjectionClient` also receives malformed retained Image data, counts decoder rejection and reaches ready after replay; this proves the Image subscription path without implementing Step-5 storage. |
| Forbidden reads/writes stay blocked | Authenticated tests verify no retained/live delivery for dates, people, roles, RPC (including the actual reader client-ID response topic), synchronization and nested Image paths, including with a broad subscription; a permitted positive-control message proves delivery is active. Publications to all five entity families, RPC requests and synchronization topics are rejected and not delivered. |
| Guardrail and test fixture alignment | Web `AGENTS.md` permits canonical Image metadata while retaining all read-only restrictions. The existing integration-test reader ACL receives the same fifth read filter. Parent/web/architecture and broker documentation describe five subscriptions. |
| Local mode consistency | All three Compose configurations pass `config --quiet` and mount the same local ACL read-only; see `compose-validation.json`. |
| Production comparison | The supplied production Diaries-role ACL has the same five exact web read rules but needs the new RPC deny. `production-web-acl.patch` supplies that change and passed `git apply --check` against a workspace copy of the package. See `production-acl-comparison.json`. This is a downloaded package comparison, not an active playbooks checkout or inspection of the deployed broker. |

## Mosquitto readiness limitation and deployment requirement

**A successful SUBACK does not establish read authorization with Mosquitto's file ACL.** Mosquitto 2.0.22 grants the subscription but silently withholds unauthorized retained and live messages. The negative-control identity without Image permission confirms this behavior. The original expectation that this ACL would produce a failed SUBACK was incorrect.

Explicit SUBACK rejection is handled and tested separately with the wire-level peer. Silent filtering is indistinguishable from an empty catalogue to this read-only subscriber: readiness alone cannot certify deployed ACL correctness. This is not addressed by broadening permissions, publishing a probe from the reader, or treating a legitimately empty catalogue as failure.

Before production reader rollout, add the web RPC deny as well as Image read access, deploy/reload the ACL, and verify controlled Image delivery and forbidden RPC delivery with the actual production reader identity. That check remains in the production release step. Neither this task nor the evidence claims it has happened. The production `imageFragmentWritesEnabled` setting was not changed.

## Validation performed

Run from the parent `diaries` directory with Windows Java 25 and Docker:

```powershell
.\gradlew.bat :diaries-web:test --tests '*MqttReaderAclIntegrationTest' --tests '*MqttSubscriptionTest' --rerun-tasks --console=plain
.\gradlew.bat :diaries-web:test :diaries-web:build --rerun-tasks --console=plain
```

- Focused corrected ACL/SUBACK run: passed (`acl-suback-tests.log`).
- Final full run: **107 passed; zero failures/errors/skips**, build successful in 48 seconds (`gradle-test-build.log`, `test-summary.csv`, `test-reports/`).
- `MqttReaderAclIntegrationTest`: 4 tests against authenticated Mosquitto 2.0.22 and the committed application ACL.
- `MqttSubscriptionTest`: 9 checks, including an actual Paho connection to the explicit-rejection peer.
- Existing `MqttProjectionIntegrationTest`: 2 real-broker replay/update/tombstone/reconnect tests passed.
- Other 92 tests cover the existing reader and Steps 2/3 contracts.
- All three Compose configurations pass; no resolved configuration secrets were recorded.
- Existing deprecated-API compiler note remains non-fatal.

The full build was rerun after the final test/source changes. XML reports were copied only after completion. No Angular or responder tests were needed because their source/contracts were unchanged.

## Resources, deployment and remaining steps

Tests use disposable brokers with test-only credentials and a loopback wire peer. No development/production retained topics, database, NAS files or real credentials were used. Testcontainers owns broker cleanup. Existing development PostgreSQL/Mosquitto containers remain running; the current development broker was not restarted or reloaded.

The production ACL reference is `playbooks/roles/diaries/files/sync/config/mosquitto/aclfile.txt` in the downloaded Step-4 package. Only its web rules were compared; unrelated production health/admin differences were not copied into local ACLs. The prepared patch adds the missing RPC deny to that reference; if the actual deployment also lacks Image read access, add both rules. No external repository or deployed configuration was modified.

Image storage/upsert/tombstone application remains Step 5. Image rendering, mixed-type browser checks and deployment remain later steps. No production authoring or legacy conversion is enabled by this completion.

## Changed files

Paths relative to the parent repository:

- `diaries-web/src/main/java/com/rsmaxwell/diaries/web/mqtt/{TopicParser,MqttProjectionClient}.java`: five subscriptions, complete SUBACK validation and safe failure/callback ordering.
- `diaries-web/src/test/java/com/rsmaxwell/diaries/web/mqtt/{RetainedContractTest,MqttReaderAclIntegrationTest,MqttSubscriptionTest}.java`: exact filters, actual-identity ACL delivery/denial checks and explicit rejected/malformed SUBACK coverage.
- `diaries-web/src/test/resources/mosquitto/acl`: fifth read filter for existing integration tests.
- `config/mosquitto/{aclfile.txt,README.md}`: minimal reader permission, reload instructions and silent-filtering limitation.
- `diaries-web/{AGENTS.md,README.md}`, parent `README.md`, `ARCHITECTURE.md`: canonical Image subscription boundaries.
- This feature's README/implementation plan, Step-3 historical verification wording and Step-4 evidence: completion status, actual validation and deployment limitations.
