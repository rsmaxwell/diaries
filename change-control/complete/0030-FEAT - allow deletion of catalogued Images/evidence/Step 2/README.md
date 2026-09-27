# 0030 Step 2 — deleteImage RPC contract

Completed 2026-09-26. **Validation passed.**

The [contract](../../RPC-CONTRACT.md) fixes the request fields, MQTT properties,
active EDITOR authorization, path rules, required success fields, error status
mapping, tombstone semantics, repeat deletion and partial-failure behaviour.
The feature README and implementation steps link this definition.

## Changed client files

- `src/app/testing/delete-image-rpc.fixture.ts`: 17 synthetic contract examples,
  including nested/root success, malformed paths/fields, authentication failures,
  not found, conflicts and coordination/publication failures. These are designed
  examples, not captured server replies; exact error prose is not normative.
- `src/app/mqtt/file-rpc-compatibility.spec.ts`: runs the examples through the
  existing shared RPC transport with a fake broker. Checks JSON request, token
  property, response topic, correlation data, QoS/non-retained request, successful
  decoding, RpcError status/raw payload and handler cleanup.

## Validation performed

From `diaries-client`:

```text
npm.cmd test -- --watch=false --browsers=ChromeHeadless --progress=false
Result: 104 SUCCESS, including 17 new deleteImage contract cases.

npm.cmd run build -- --configuration production
Result: passed; existing quill-delta and buffer CommonJS warnings.
```

Full outputs: `client-tests.log`, `client-build.log`.
Parent and client `git diff --check` passed. Source identities are recorded in
`source-sha256.json`; evidence hashes are in `SHA256SUMS.txt`.

The existing responder Authorization, ImagePathPolicy and DeleteFile code and
the 0024 captured response fixtures were inspected for compatibility. In
particular, current authorization helpers return 401 for insufficient roles,
so the contract preserves that convention. The captured 0024 fixture is unchanged.

## Scope limits

No responder handler, registration, service mutation, public client RPC wrapper
or UI was added. No ImageFragment reference checks were implemented. The 409
referenced-image example reserves the later 0025 behaviour.

No database-backed test or live broker test was rerun for this step, and no files,
database rows or retained topics were deleted. Tests validate client transport
compatibility with the defined examples, not server enforcement or end-to-end
deletion. Step 1's database-backed guard evidence remains unchanged. Subsequent
steps must validate the real handler/service and retained tombstone publication.
