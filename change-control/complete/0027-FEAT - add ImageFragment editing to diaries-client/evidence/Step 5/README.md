# Step 5 close-out — explicit `addImageFragment` client request and RPC support

**Status:** Complete — 2026-10-03

Step 5 introduces the client creation transport required by later authoring UI work, without exposing any new UI action yet.

Implemented:

- dedicated `AddImageFragmentRequest` with the responder's exact creation fields;
- preserved omitted / explicit-null / positive `imageId` JSON semantics;
- no caller-controlled Fragment `id`, `type` or `marqueeId` in the request API;
- narrowed `ImageFragment` response type (`type: 'IMAGE'`, `marqueeId: null`);
- `RpcService.addImageFragment$()` using function `addImageFragment` and the existing authorised MQTT RPC transport;
- focused tests for exact creation payload, omitted/null Image reference, 400/401/403/500 error paths and unchanged MARQUEE `addFragment$()` payload.

Validation available in this sandbox:

- strict TypeScript compile of the Fragment request model: PASS;
- executable serialization smoke for positive/omitted/null `imageId`: PASS;
- TypeScript parse/transpile check of all changed client source/spec files: PASS;
- full Angular/Karma command: BLOCKED because the supplied source bundle contains no installed Angular CLI/dependencies (`ng: not found`).

No responder, HTML, styling, configuration or deployment files are changed in this step.
