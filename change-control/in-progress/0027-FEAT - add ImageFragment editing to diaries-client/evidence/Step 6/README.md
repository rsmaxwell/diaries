# Step 6 — Make `updateFragment` Image mutation explicit and tri-state

**Status:** Complete

Step 6 preserves the existing safe ordinary-update contract and adds a separate deliberate Image-reference mutation path.

Implemented:

- `UpdateFragmentRequest.fromFragment()` remains the preserve path and omits `imageId`.
- `UpdateImageFragmentRequest.fromImageFragment()` emits a positive `imageId` for attach/replace or explicit `null` for clear.
- the explicit request rejects MARQUEE-shaped Fragments and invalid Image IDs before RPC.
- `RpcService.updateImageFragment$()` uses the existing responder `updateFragment` function and existing authorised transport.
- neither ordinary nor explicit requests carry `pageId` or `type`.
- TextPanel IMAGE text saves remain on `updateFragment$()`.
- day-view IMAGE reorder remains on `updateFragment$()`.
- focused RPC tests cover preserve/set/clear wire forms.

No responder production code, UI controls, lock workflow, deployment configuration or database/file state is changed by this step. The lock-taking replacement/clear UX is implemented later in Step 8.

## Validation

The standalone TypeScript compile/runtime serialization check passes, as does syntax parsing of every changed TypeScript file. Static contract checks against both client and responder pass.

The complete Angular test command cannot run in this sandbox because the source bundle intentionally has no `node_modules` and therefore no local Angular CLI. The focused responder test cannot run because the Gradle wrapper needs Gradle 9.6.1 from `services.gradle.org`, which is inaccessible in this environment. The exact outputs are retained alongside this README.
