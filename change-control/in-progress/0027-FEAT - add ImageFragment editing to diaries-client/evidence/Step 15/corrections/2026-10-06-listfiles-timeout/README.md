# 2026-10-06 `listFiles` production timeout correction

The first Step 15 production authoring attempt reached the Image Catalogue but timed out before an Image could be selected. Production responder evidence showed `listFiles` was received and authorised at 14:18:58 and returned HTTP-style MQTT RPC status 200 at 14:19:09, approximately 11.8 seconds later. The Angular RPC transport used its generic five-second timeout, so the client abandoned the request before the successful response arrived.

Production authoring was then disabled again and the Step 15 `rollback-disabled` capture passed before this source correction was prepared.

## Source correction

- `RpcService.listFiles$()` uses a 30-second timeout; ordinary control RPCs keep their existing five-second default.
- Responder `ListFiles` snapshots the Image catalogue once with `findAllOrderedByRelativePath()` and performs in-memory case-insensitive path matches, removing the previous per-file `findByRelativePath()` N+1 query pattern.
- Responder `ListFiles` logs total elapsed time and returned item count.
- Focused client/responder regressions protect the longer `listFiles` deadline and the single catalogue snapshot contract.
- Step 15 production capture now archives an existing same-phase capture into the run-local `history` directory before writing a retry, preserving the failed/earlier attempt.

The responder still performs filesystem metadata and EXIF inspection because that is part of the existing `listFiles` response contract. The longer client deadline therefore remains necessary even after eliminating the N+1 database work.

## Required production retry

Publish corrected images, but keep `diaries_image_fragment_writes_enabled: false`. Redeploy with the gate false and repeat the disabled-gate smoke from the beginning. The Image Catalogue must open successfully; after selecting an Image, the actual Image-reference authoring RPC must then receive the expected 403. Take a fresh `pre-enable` capture before deliberately setting the gate true again.

Do not erase or relabel the first failed enablement attempt. Keep the failed attempt, `rollback-disabled`, correction build/deployment, and fresh gate-false smoke as one audit trail.
