# Step 6 client update contract

The client now exposes two intentionally different update paths to the same responder `updateFragment` function.

| User intent | Client API | Wire `imageId` | Meaning |
| --- | --- | --- | --- |
| edit text/date/sequence or reorder | `updateFragment$(fragment)` | omitted | preserve current Image reference |
| attach/replace Image | `updateImageFragment$(imageFragment, positiveId)` | positive integer | set/replace Image reference |
| clear Image | `updateImageFragment$(imageFragment, null)` | explicit `null` | clear Image reference |

`UpdateFragmentRequest` deliberately contains no `imageId` property. `UpdateImageFragmentRequest` is separate, accepts only an IMAGE Fragment with `marqueeId: null`, and rejects zero, negative or fractional IDs. Both request types omit `pageId` and `type`; those identity fields remain responder-authoritative and immutable after creation.

The explicit mutation method still sends RPC function `updateFragment`; no responder protocol function has been invented.
