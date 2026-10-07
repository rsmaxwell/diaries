# Step 15 production correction — Image catalogue `listFiles` timeout

During the first deliberately enabled production authoring attempt on 2026-10-06, the Image Catalogue dialog timed out before an Image could be selected. The client had successfully published `listFiles`; responder evidence showed that the request was authorised and completed successfully, but took about 11.8 seconds on the production NAS-backed Files tree. The generic client RPC timeout was 5 seconds, so the successful responder reply arrived after the client had already abandoned the request.

The production authoring gate was returned to `false` and the Step 15 `rollback-disabled` capture passed before this correction was prepared.

## Correction

1. `RpcService.listFiles$()` now uses a deliberate 30-second timeout. The generic five-second deadline remains unchanged for ordinary control RPCs.
2. Responder `ListFiles` snapshots the Image catalogue once per request using `findAllOrderedByRelativePath()` and matches filesystem entries in memory. It no longer calls `findByRelativePath()` once per listed file. Matching remains case-insensitive to preserve the previous repository lookup semantics.
3. `ListFiles` logs the returned item count and elapsed listing time, making future production timing evidence explicit.
4. Focused regressions cover the 30-second client timeout contract and the responder single-snapshot/no-per-file-query contract.

## Retry rule

After publishing corrected images, redeploy them with `diaries_image_fragment_writes_enabled: false`. Repeat the disabled-gate smoke test from the beginning: confirm the Image Catalogue opens, select a catalogued Image, and prove the subsequent Image-reference authoring RPC is rejected with the expected 403 while the gate is false. Only then recapture `pre-enable`, deliberately set the gate to `true`, redeploy, recapture `post-enable`, and restart the controlled production IMAGE lifecycle.
