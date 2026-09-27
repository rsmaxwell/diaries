# 0030 Step 6 — Add client RPC wrapper

Completed 2026-09-27.

## Changes

- `src/app/mqtt/rpc.service.ts`: adds `deleteImage$(name, subdir?)`, forwarding raw basename and optional directory to the registered responder operation. Uses existing authorisedRpcRequest, reply topic, token refresh/retry, JSON decoding, RpcError and five-second timeout. No independent token handling or state mutation.
- `src/app/model/delete-image-reply.ts`: typed id, relativePath and literal deleted=true acknowledgement. Retained Image topics remain authoritative.
- `src/app/mqtt/file-rpc-compatibility.spec.ts`: nine public-wrapper tests for omitted/empty/nested directory, unencoded spaces, MQTT properties, 400/404/409/500 propagation without retry, 401 shared refresh/retry, and timeout cleanup. Earlier Step 2 synthetic transport tests preserved.
- Client README and implementation steps document the API and completion.

## Validation

- `npm.cmd test -- --watch=false --browsers=ChromeHeadless --progress=false`: 113 passed, zero failures. Initial test compilation identified a fixture union type in an expected result; corrected to the concrete success shape before the passing run.
- `npm.cmd run build`: passed (repository default is development).
- `npm.cmd run build -- --configuration production`: passed. CommonJS optimization warnings for quill-delta and buffer remain.
- Reviewed request and reply against RPC-CONTRACT.md and the Step 5 Java handler. No responder contract changes required. Step 5 already records real PostgreSQL/Mosquitto deletion validation; that integration was not rerun for this client wrapper.
- No live broker/database/NAS actions, UI changes or deployment. Browser end-to-end deletion remains later workflow validation.

The client timeout stays at the existing five seconds as Step 6 specifies. A timeout does not prove that server-side deletion failed; later UI work must reconcile retained state rather than assume rollback or retry blindly. The responder can spend up to ten seconds waiting for a tombstone acknowledgement.

Logs and source-sha256.csv record this validation. Existing uncommitted work was preserved; nothing committed or pushed.
