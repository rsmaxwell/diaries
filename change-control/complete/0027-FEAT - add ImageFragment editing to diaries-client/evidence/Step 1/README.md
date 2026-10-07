# 0027 Step 1 — Freeze the client/responder ImageFragment contract and current regression baseline

## Status

Implemented on 2026-10-03 against `diaries-sources-20261003-190733.zip`.

The wire contract and relevant existing regression coverage are frozen here before any 0027 IMAGE-authoring UI changes. One client characterization test was added to make the current ordinary `updateFragment` serialization rule executable.

The full Angular unit-test baseline could not be run in the implementation sandbox because the source bundle contains no `node_modules` and external npm downloads are unavailable. The exact bootstrap/test attempts and exit codes are retained in `baseline-client-tests.txt`; this is deliberately recorded as an environment limitation rather than reported as a green run. Focused responder Gradle execution is likewise unavailable because the Gradle 9.6.1 wrapper distribution is not cached and `services.gradle.org` is unreachable; see `baseline-responder-tests.txt`.

## Source baseline

See `source-baseline.sha256`.

Primary source locations captured in `contract-source-baseline.txt`:

- `diaries-client/src/app/model/fragment.ts`
- `diaries-client/src/app/mqtt/file-rpc-compatibility.spec.ts`
- `diaries-client/src/app/files-list-dialog/files-list-dialog.compatibility.spec.ts`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragment.java`
- `diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java`

## 1. Retained Fragment payload contract

`FragmentPublishDTO` publishes the same Fragment payload to both:

```text
diaries/fragments/<fragmentId>
diaries/dates/<year>/<month>/<day>/<fragmentId>
```

The payload contains:

```text
id
version
year
month
day
sequence
text
pageId
type
imageId
marqueeId
lock
```

`lock` is null when unlocked. When present it contains:

```text
lockUserId
lockUserName
lockKnownAs
lockTimeStamp
lockSessionId
```

`imageId` is explicitly present and may be null. `marqueeId` is explicitly present and may be null.

Representative payload: `fragment-retained-payload.example.json`.

## 2. `addImageFragment` request/reply contract

The responder accepts an active EDITOR request with:

```text
pageId       required positive integer
year         required integer
month        required integer
day          required integer
sequence     required NUMERIC(10,4)-compatible value
text         required string, maximum 4096 characters
imageId      optional positive integer; null/omitted means no Image reference
```

The operation itself owns IMAGE identity. Caller-supplied Fragment `id`, `type` or `marqueeId` do not override that identity.

Success returns HTTP-style RPC status 200 with the committed `FragmentPublishDTO`. The reply therefore has `type: "IMAGE"`, the resolved/optional `imageId`, and `marqueeId: null`.

Representative files:

- `add-image-fragment-request.example.json`
- `add-image-fragment-reply.example.json`

Important failure semantics already present in the responder:

- 401: inactive/insufficient authentication/role;
- 403: ImageFragment authoring gate disabled;
- 400: malformed arguments or unresolved Page/Image reference;
- 500: persistence/publication failure;
- publication failure after commit reports the committed Fragment identity, so creation must not be retried blindly.

## 3. Current client ordinary `updateFragment` request

Before 0027 UI work, `UpdateFragmentRequest.fromFragment()` serializes exactly:

```text
id
marqueeId
year
month
day
sequence
version
text
```

It does **not** serialize:

```text
pageId
type
imageId
lock
```

This is true even when the source `Fragment` has `type: "IMAGE"` and a non-null `imageId`.

Representative request: `update-fragment-current-request.example.json`.

A characterization test was added to `diaries-client/src/app/model/fragment.spec.ts` to freeze this exact field set. `focused-contract-smoke.txt` records an independent serializer smoke using the bundled source plus the sandbox's global TypeScript tooling.

## 4. Frozen `imageId` wire semantics

The responder contract is intentionally three-state:

| Wire state | Meaning | Gate-disabled behaviour when stored value differs |
| --- | --- | --- |
| `imageId` absent | Preserve the existing Image reference | Allowed |
| `imageId: <positive id>` | Attach or replace the Image reference | 403 |
| `imageId: null` | Explicitly clear the Image reference | 403 |

An explicit Image ID equal to the currently stored ID is treated as no mutation. Explicit null against an already-null IMAGE Fragment is likewise not a mutation.

This distinction is critical for 0027: ordinary text/date/sequence edits and day-view reordering must continue to omit `imageId`. Only an explicit Image selection/clear workflow may add the field.

Representative examples: `update-fragment-imageId-semantics.json`.

## 5. Existing Files RPC additive Image metadata

The existing compatibility tests already prove that File RPC replies may carry Image catalogue metadata additively without breaking generic file handling.

The captured additions include:

```text
uploadFile reply:
  imageId
  image

listFiles reply:
  catalogueVersion
  items[*].imageId
  items[*].image
```

The Image metadata exercised by compatibility tests includes the persisted Image identity and fields such as `relativePath`, `mimeType`, `originalFilename`, dimensions, checksum, caption and alt text. Directory entries use null Image identity/metadata.

Representative shape: `files-rpc-image-metadata.example.json`.

These fields are currently exercised as additive/dynamic compatibility data; later 0027 steps can promote them into first-class TypeScript interfaces without inventing a new wire shape.

## 6. Client regression baseline

Attempted commands and outputs are in `baseline-client-tests.txt`.

The source bundle intentionally contains no `node_modules`. In this sandbox:

```text
npm ci --offline
```

fails because `zone.js@0.15.1` is not present in the npm cache, and:

```text
npm test -- --watch=false --browsers=ChromeHeadless
```

cannot start because the local Angular CLI is therefore unavailable.

This is an execution-environment limitation, not a recorded product-test failure. No green full-suite claim is made here.

The focused serializer smoke does pass and proves the key current client request shape independently of Angular dependencies.

## 7. Responder authoring-gate baseline

`responder-authoring-gate-baseline.txt` captures the existing tests that already freeze the required gate behaviour.

### `addImageFragment` while disabled

`AddImageFragmentTest.disabledGateRejectsBeforePageLookupPersistenceOrPublication` proves that a missing/null/disabled gate rejects an active editor with 403 before Page lookup, persistence or retained publication.

### Changing `imageId` while disabled

`UpdateFragmentImageTest.disabledGateAllowsPreservationButRejectsAttachReplaceAndClear` proves:

- omitted `imageId` preserves and is allowed;
- unchanged explicit Image identity is allowed;
- attach/replace is rejected with 403;
- clear is rejected with 403 when it changes the stored reference.

`UpdateFragmentImageTest.absentPreservesNullClearsAndValueReplaces` freezes the preserve/set/clear semantics when authoring is enabled.

### Ordinary IMAGE edits while disabled

`ImageWiringIntegrationTest.authoringGateRejectsMutationsButPreservesLifecycle` is the live MQTT/database gate regression. With `imageFragmentWritesEnabled=false` it:

- rejects Image-reference mutation through `updateFragment` with 403;
- performs an ordinary text edit through `updateFragment` successfully when `imageId` is omitted;
- verifies the Image reference is unchanged;
- continues lock/unlock, normalisation and Fragment deletion lifecycle behaviour.

This is the responder-side proof required by Step 1 that disabling IMAGE authoring does not disable ordinary editing of existing IMAGE Fragments.

## Step 1 acceptance assessment

- **Wire contract frozen:** yes.
- **Representative request/reply JSON stored:** yes.
- **Preserve/set/clear semantics documented:** yes.
- **Current client omission of `imageId` guarded by a characterization test:** yes.
- **Files RPC additive Image metadata captured:** yes.
- **Responder gate behaviour identified in existing regression tests:** yes.
- **Full existing Angular suite green in this sandbox:** not established; dependency bootstrap is blocked and the failure evidence is stored.

No 0027 production/UI behaviour has been changed by Step 1.
