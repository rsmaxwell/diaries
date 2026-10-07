# Step 13 live regression — ordinary IMAGE Fragment update rejected with 400

Date: 2026-10-04

## Symptom

With `imageFragmentWritesEnabled=false`, editing the transcription of disposable IMAGE Fragment `2332` acquired the Fragment lock successfully but `updateFragment` returned HTTP-style RPC status 400. The client correctly rolled the editor back and released the lock, so the typed text disappeared.

This is **not** the intended authoring-gate behaviour. The frozen contract allows ordinary IMAGE Fragment text/date/sequence edits while the gate is disabled; only creation and actual Image-reference mutation are gated.

Live browser evidence is preserved in `image-fragment-ordinary-update-400-browser-log-20261004.txt`. The relevant sequence is: lock succeeds, `UpdateFragmentRequest.fromFragment` is built with IMAGE `marqueeId:null`, `updateFragment` returns 400, then failed-edit unlock succeeds.

## Root cause

The client `UpdateFragmentRequest` still serialized `marqueeId`. IMAGE Fragments necessarily have `marqueeId:null`, producing a request body containing an explicit null relationship field.

The current `mqtt-rpc` `Request` record defensively copies request arguments with `Map.copyOf(args)`. Java `Map.copyOf` rejects null values, so the request failed in the MQTT-RPC request-decoding path before `UpdateFragment.handleRequest()` could execute.

The responder itself does not use `marqueeId` when updating a Fragment. It reloads the persisted Fragment, preserves server-authoritative `pageId`, `type`, Image relationship and lock state, and reads only `id`, `version`, `sequence`, `year`, `month`, `day`, `text`, plus optional guarded `imageId`. Existing responder integration coverage already proves that an IMAGE text edit with `imageId` omitted is permitted while the authoring gate is disabled.

## Correction

`UpdateFragmentRequest` now omits all relationship/identity fields that are responder-authoritative:

- `pageId`
- `type`
- `marqueeId`
- `imageId`

Its ordinary wire shape is now only:

```json
{
  "id": 2332,
  "year": 1828,
  "month": 1,
  "day": 1,
  "sequence": 2,
  "version": 0,
  "text": "..."
}
```

`UpdateImageFragmentRequest` inherits the same null-free base request:

- positive `imageId` replacement serializes the same base fields plus `imageId:<positive id>`;
- explicit Image clear serializes the same base fields plus `imageId:null`, which continues through the responder's existing null-preserving `ImageFragmentMessageHandler`;
- ordinary text/date/sequence edits omit `imageId`, preserving the current Image reference.

This also prevents positive Image replacement from accidentally carrying the unrelated `marqueeId:null` value into the normal MQTT-RPC dispatcher.

## Regression coverage

Client tests now assert that:

- ordinary IMAGE update requests omit both `marqueeId` and `imageId`;
- positive Image replacement omits `marqueeId` and includes only positive `imageId`;
- Image clear omits `marqueeId` while preserving explicit `imageId:null`;
- IMAGE transcription/date update tests and mixed reorder tests assert the same null-free ordinary wire contract.

The source-generation environment does not contain the Diaries client's `node_modules`, so the full Karma suite must be rerun on the development workstation. Local source validation performed here parsed all changed TypeScript files successfully and executable serialization checks produced the expected three wire shapes.

## Step 13 status

Step 13 remains open. Resume Phase A from the same baseline after applying this correction and rerun the ordinary IMAGE transcription edit. It must now save successfully with the gate disabled before date/reorder and 403-gate checks continue.
