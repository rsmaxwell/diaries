# deleteImage RPC contract — 0030 Step 2

Defined 2026-09-26. The responder implements and registers `deleteImage` as of Step 5 (2026-09-27). Client integration remains subsequent work.

## Request and transport

Publish UTF-8 JSON to the existing `diaries/rpc/request` topic, QoS 0, retain false:

```json
{
  "function": "deleteImage",
  "args": { "subdir": "diary-1830/images", "name": "img2221.jpg" }
}
```

Use the existing MQTT v5 properties: `responseTopic` is the client's reply topic,
`correlationData` identifies this request, and `userProperties.accessToken`
contains the access token. Credentials do not belong in the JSON body.
Replies use the supplied response topic/correlation, QoS 1, retain false, with
the existing JSON-encoded `userProperties.status` object `{code,message}`.
The payload is the response body itself, not a second status envelope.

| Field | Rule |
| --- | --- |
| `function` | Exactly `deleteImage` |
| `args` | Required JSON object |
| `args.name` | Required non-blank string basename; no slash or backslash |
| `args.subdir` | Optional string, default `""` (Files root); explicit null/non-string is invalid |

No Image ID, URL, overwrite flag or recursive-delete flag is accepted as an
alternative identity. Unknown extra fields have no authority and may be ignored
for additive compatibility. The responder resolves the Image row by canonical
path under the existing catalogue lock; client metadata cannot select a different row.

## Authorization and validation

Authenticate before catalogue lookup or filesystem mutation. Require an active
account with `EDITOR` or stronger role through the existing Authorization helpers.
Those helpers currently use **401**, including for inactive accounts and
insufficient/missing/invalid roles; this feature does not introduce a new 403
convention. Missing, invalid or expired credentials must fail closed.

Use `ImagePathPolicy.uploadPath(subdir, name)` and the existing repository's
canonical path identity. Paths are raw relative names, not URL-encoded strings.
Normalize separators to `/` and Unicode to NFC; reject absolute/drive/UNC paths,
URIs, `..`, reserved `.image-staging` segments, non-portable names, symlinks and
reparse-point escapes. Preserve the existing conservative filesystem alias
checks; do not invent a second case-folding or URL-decoding policy. Do not create
directories during deletion. A directory is never a request for recursive deletion.

The success path comes from the stored Image's canonical `relativePath`, not
from echoing an unvalidated request. Errors must not reveal absolute server/NAS
paths, credentials, SQL or stack traces.

## Success

Status property: `{"code":200,"message":"ok"}`. JSON payload:

```json
{ "id": 85, "relativePath": "diary-1830/images/img2221.jpg", "deleted": true }
```

All three fields are required: `id` is the deleted Image's positive numeric ID,
`relativePath` is its canonical path, and `deleted` is the boolean `true`.
Consumers may ignore future additive fields. No absolute file path or deployment
URL is returned. There is no `200` response with `deleted: false`.

Success requires the coordinated file removal/database commit and publication
of a zero-byte **retained** tombstone to `diaries/images/{id}` using the existing
Image publication mechanism. Publish only after durable deletion; JSON `null`,
an empty JSON object and a non-retained message are not tombstones. The client
refreshes the current file list and derives catalogue state from retained MQTT.
Do not assume the reply and retained update arrive in a particular order.

## Errors and partial outcomes

Error status is carried in the same status property; the JSON body is a safe
human-readable string, consistent with existing file RPC errors. Clients branch
on the numeric status, not exact prose. Fixture error messages are illustrative.

| Code / status message | Meaning |
| --- | --- |
| 400 / `bad request` | Malformed args, missing/invalid name, invalid subdir or unsafe path |
| 401 / `unauthorized` | Authentication or active-account/role check failed |
| 404 / `not found` | No catalogue row owns the path, including a repeat request after successful deletion; do not delete an uncatalogued file |
| 409 / `conflict` | Catalogue row exists but bytes are missing or the target is not a regular file; later, a referenced Image also conflicts |
| 500 / `internal error` | Storage/database coordination, compensation, post-commit tombstone publication or required cleanup could not be confirmed |

A failure before mutation leaves state unchanged. A database failure after
staging restores the original file where possible. A restore/commit outcome that
is uncertain must not report success. A post-commit publication/cleanup failure
may mean deletion has already committed: log a recoverable diagnostic and return
500, without pretending that the row/file is intact or automatically resurrecting it.
Later service steps must provide the recovery behaviour; the contract does not
turn filesystem, database and MQTT into one atomic transaction.

Timeout is a client transport outcome with no server status; it does not prove
that deletion failed. Refresh state before retrying. There is no idempotency key
in this version. Repeating a completed deletion returns 404, not success, and
must never fall back to generic `DeleteFile`.

## Compatibility fixtures and Step 2 boundary

Synthetic examples live in
`diaries-client/src/app/testing/delete-image-rpc.fixture.ts`. The existing
`file-rpc-compatibility.spec.ts` harness sends them through the actual shared
client RPC transport with fake broker replies, checking request properties,
success decoding, status/error delivery and correlation-handler cleanup.

These tests do not prove responder authorization/path enforcement or real MQTT
publication. Later handler/service tests must use the same contract. The frozen
0024 captured fixture is unchanged; generic `DeleteFile` continues to reject
catalogued paths as verified by Step 1.

Step 2 adds no service deletion, handler registration, client wrapper or UI.
The future referenced-image fixture reserves 409 for 0025; it adds no ImageFragment
reference lookup or enforcement now.
