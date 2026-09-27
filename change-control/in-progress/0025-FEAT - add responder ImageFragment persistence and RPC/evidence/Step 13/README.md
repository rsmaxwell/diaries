# 0025 Step 13 - Safe deployment/authoring gate

Completed 2026-09-27. Default-disabled responder gate implemented and verified.

## Configuration and behavior

Top-level responder JSON property: `imageFragmentWritesEnabled`.
Missing, null and false disable authoring. Explicit true enables it. No environment
variable overrides this property, and changing the file requires responder restart.

| Operation while disabled | Result |
| --- | --- |
| addImageFragment, with/without Image selection | 403 after normal active-editor authorization, before Page lookup or persistence |
| IMAGE update attaches, replaces or clears imageId | 403 inside the existing transaction; rollback preserves row, lock, version and retained state |
| IMAGE update omits imageId | Preserves reference; ordinary edit remains allowed |
| IMAGE update echoes current ID, including null-to-null | Allowed as a no-op reference selection |
| MARQUEE creation/edits | Existing validation and behavior unchanged |
| Read/replay, Fragment lock/unlock, text/date/sequence edits and normalisation | Unchanged |
| Fragment deletion | Allowed; Image remains independently owned |
| Referenced Image deletion | Still 409 |
| Unreferenced Image deletion | Existing recoverable lifecycle remains allowed |

The creation service is independently gated as well as the RPC entry point. Existing
Page/type/version/ownership validation still applies. Rejection does not silently unlock
an edit or partially apply its text changes. Invalid IDs retain normal 400 validation.

## Changed files

- `config/Config.java`: nullable JSON property plus fail-closed effective accessor.
- `utilities/ImageFragmentWritePolicy.java`: shared gate check and controlled 403.
- `handlers/AddImageFragment.java`: check after authorization, before any authoring work.
- `handlers/UpdateFragment.java`: compare requested/current reference inside its transaction;
  gate actual mutations while preserving omitted/unchanged selections.
- `utilities/DiaryContext.java`: gate direct saveImageFragment creation.
- Config/creation/update unit tests: default/null/false/true, rejection ordering, preserved
  references and direct-service protection. Authoring fixtures explicitly enable the gate.
- `ImageWiringIntegrationTest.java`: live gate test and expected-status support in MQTT
  harness; other disposable authoring tests explicitly opt in.
- Step 13 runner/broker fixture/evidence, feature documentation, responder README and
  `config/environments/local.env.example`: configuration and mode/deployment guidance.

## Validation

**Full responder tests/build passed:** 320 discovered, 284 passed, 36 environment-gated
skips, no failures/errors. See `final-test-build.log`, `unit-results.json` and saved XML.

**Live PostgreSQL/Mosquitto integration: 2 passed, 0 skipped**, authoritative
`verified-run/result.json` and `integration-test.xml`:

1. `authoringGateRejectsMutationsButPreservesLifecycle`: missing flag rejects creation
   (including explicit-null requests); explicit enable permits selected/unselected
   creation; false rejects attach/replace/clear with unchanged row and actual retained
   snapshots. Text edits, lock/unlock, mixed lifecycle infrastructure, normalisation,
   fresh-context replay and Fragment/Image deletion safeguards continue working.
2. `liveImageFragmentRpcAndRestartReplay`: full enabled create/edit/clear/reattach,
   mixed normalisation/deletion and startup reconciliation regression from Step 12.

The live test uses the scoped explicit-null adapter from Step 12, so clearing while
disabled is proved to return 403 through MQTT rather than being rejected by decoding.
Unit tests separately verify same-reference requests and MARQUEE creation compatibility.

Disposable PostgreSQL uses the frozen 0024 backup plus migrations and Hibernate schema
validation. Fresh observer subscriptions check actual Mosquitto retained state. Database
row counts/hashes match after cleanup; both owned containers were removed successfully.
No production database or NAS content was accessed. Existing Gradle warnings are non-fatal.
Source hashes are recorded; prior uncommitted feature work is preserved. No commit/deploy.
Client tests/build were not repeated: no client source or request/reply format changed;
actual MQTT 403 handling is asserted by the integration requestor.

## Deployment examples and scope

All modes use the same JSON property. Add to the configuration object:

```json
"imageFragmentWritesEnabled": false
```

Use true only in deliberately enabled development/test configuration or the approved
production authoring rollout. The committed local environment example documents that
the flag belongs in the mounted responder JSON, not the env file.

For an external Ansible JSON template, the corresponding safe-default expression is:

```jinja2
"imageFragmentWritesEnabled": {{ diaries_image_fragment_writes_enabled | default(false) | bool | to_json }}
```

This is deployment guidance, not an edit to the separate Ansible repository. Existing
deployments that omit the property are already safely disabled with this responder.
Private Windows config files and production-generated JSON were not modified.

Production should remain disabled until the 0025 responder is validated, the
0026-capable reader is deployed/verified, and 0027 authoring rollout is explicitly
approved. Disabling does not remove or hide existing IMAGE rows. No new migration,
Docker image publication or deployment is performed by this step.
