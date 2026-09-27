# 0030 Step 8 — Confirmation and operation flow

Completed 2026-09-27.

## Changes

- `delete-image-confirmation.component.ts`: CDK modal displaying the captured relative image path and clear Cancel/Delete image buttons. Cancel is initially focused; Escape/backdrop dismissal is cancellation. Uses existing theme tokens.
- `files-list-dialog.component.ts`: menu selection opens confirmation; explicit confirmation calls the Step 6 wrapper. Confirmation/pending guards prevent duplicate submission. Captures the original basename and directory. Prevents closing/selecting a file during a pending request, restores close behaviour on completion, and tears down subscriptions/confirmation on destruction.
- Listing now combines the current path with an explicit refresh signal, so a successful operation reloads even when the directory has not changed. It does not remove rows optimistically or mutate retained Image state.
- Template/styles show busy status and controlled error messages with a Refresh folder action. Failed/uncertain outcomes never claim rollback and are not retried by the dialog. The shared wrapper retains its existing authentication refresh behaviour.
- Component tests add ten cases covering confirmation/cancellation, Escape, destruction cleanup, duplicate protection, successful refresh and 400/401/404/409/500/unknown failures.

## Validation

- `npm.cmd test -- --watch=false --browsers=ChromeHeadless --progress=false`: all 132 tests passed.
- `npm.cmd run build -- --configuration production`: passed; existing quill-delta and buffer CommonJS warnings remain.
- `git diff --check`: passed.

Tests exercise actual CDK confirmation/menu overlays in headless Chrome with mocked RPC. Step 5 retains real database/broker evidence and Step 6 verifies the wrapper contract; no responder contract changed here. Live application end-to-end deletion is Step 9 and was not run. No NAS files or live database records were changed. No deployment, commit or push.

The five-second client timeout is unchanged. Timeout/500 errors report an unconfirmed outcome and offer a refresh; administrator checking is advised for 500 before retrying. Files listing comes from the responder; retained-topic lifecycle remains server-owned.

Logs and source-sha256.csv record validation of the current sources.
