# Step 5 client `addImageFragment` RPC contract

## Request model

`AddImageFragmentRequest` is intentionally separate from `AddFragmentRequest`.

Allowed request fields:

- `pageId`
- `year`
- `month`
- `day`
- `sequence`
- `text`
- optional `imageId`

The client request type has no Fragment `id`, `type` or `marqueeId`; those identity fields remain responder-authoritative.

### `imageId` creation semantics

- positive integer supplied: serialize `imageId` with that value;
- explicit `null`: serialize `imageId: null`;
- omitted/`undefined`: omit the `imageId` property from JSON entirely.

The production Step 2 UX will normally select a catalogued Image before creation, but the client transport keeps the full responder contract available.

## RPC wrapper

`RpcService.addImageFragment$()` sends:

```json
{
  "function": "addImageFragment",
  "args": {
    "pageId": 12,
    "year": 1830,
    "month": 2,
    "day": 3,
    "sequence": 4.5,
    "text": "Image fragment",
    "imageId": 101
  }
}
```

The method uses the existing `authorisedRpcRequest()` path, including the existing access-token refresh/retry behaviour and `RpcError` status propagation.

## Reply type

A successful reply is deserialized as `ImageFragment`, a narrowed `Fragment` type requiring:

- `type: 'IMAGE'`
- `marqueeId: null`

The remaining committed Fragment fields, including the responder-assigned `id`, `version`, `pageId` and `imageId`, are returned unchanged.

## Compatibility

The existing MARQUEE `addFragment$()` method and its wire request are not changed by Step 5. A focused regression test retains its existing request shape.
