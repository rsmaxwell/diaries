# Step 15 fixture signing-secret correction

This patch replaces the Step 15 disposable responder fixture signing secret with a valid Base64-encoded 34-byte key.

The responder's Authorization.getTokenWithClaims() Base64-decodes the configured secret before creating JWTs. The previous Step 15 runner supplied plain text, so `health` passed but the first `signin` RPC returned HTTP/RPC status 500 when token generation attempted to decode the secret.

Copy `deployment/run-deployment.py` over the existing file under the feature's `evidence/Step 15` directory, remove/archive the failed `deployment/final-run` if necessary, then rerun `./run-step15.ps1 -ApplyDocumentation`.
