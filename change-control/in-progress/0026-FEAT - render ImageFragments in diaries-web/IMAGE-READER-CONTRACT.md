# 0026 Image reader contract and degraded states

Status: Step 2 contract, 2026-09-28

This note is the authoritative reader-side contract for 0026. It defines the data accepted by the read-only `diaries-web` projection and the degraded states that later decoder, projection and rendering steps must preserve. It does **not** add Image decoding, subscriptions, projection storage or rendering; those begin in Step 3 and later steps.

## 1. Scope and authority

The responder remains authoritative for persisted Image metadata. The reader consumes retained metadata only; it does not infer database state from files, construct chronology from Images, mutate files, or require a deployment URL in retained data.

Canonical Image retained topics use the configured topic prefix:

```text
<prefix>/images/<id>
```

A normal publication contains metadata only. A zero-byte retained publication is a tombstone. JSON `null`, `{}`, malformed JSON, or a structurally invalid Image payload is **not** a tombstone.

Image metadata fields are exactly the additive retained contract published by `ImagePublishDTO`:

```text
id
version
relativePath
mimeType
originalFilename
width
height
checksum
caption
altText
```

Unknown additive JSON properties are ignored. The reader must not invent a second retained schema, persist a browser URL, or require a Files/public responder URL in the retained payload.

## 2. Authoritative Image validation

The reader must accept/reject Image metadata consistently with the responder's `Image` / `ImagePublishDTO` boundary contract.

| Field | Reader contract |
| --- | --- |
| `id` | Required positive integer for a retained Image publication. The numeric topic ID must equal payload `id`. |
| `version` | Required integer, `>= 0`. |
| `relativePath` | Required non-blank canonical NFC relative path. `/` separates segments. No backslash, colon, ISO control character, leading/trailing slash, empty segment, `.` segment or `..` segment. |
| `mimeType` | Required; one of `image/jpeg`, `image/png`, `image/gif`, `image/webp`. |
| `originalFilename` | Required non-blank filename only. No `/`, `\\`, `:`, or ISO control character. |
| `width` | Required positive integer. |
| `height` | Required positive integer. |
| `checksum` | Required exactly 64 lowercase hexadecimal characters (`[0-9a-f]{64}`). |
| `caption` | Plain text. Current responder publications always make it non-null and commonly use `""`. Reader compatibility also treats an **absent** property as `""`. An explicit JSON `null` is invalid metadata. Do not trim or interpret it as HTML. |
| `altText` | Plain text. Current responder publications always make it non-null and commonly use `""`. Reader compatibility also treats an **absent** property as `""`. An explicit JSON `null` is invalid metadata. Do not derive replacement text from the filename. |

`relativePath` validation is syntax-only at decode time. It does not prove that bytes exist or can be loaded by a browser.

## 3. Fragment Image-reference semantics

`Fragment.imageId` is a nullable reference. The JSON property being absent and the property being explicitly `null` are equivalent reader states.

| Fragment state | Meaning |
| --- | --- |
| `IMAGE`, positive `imageId` | A catalogue Image is selected. Resolve that ID if valid metadata is present. |
| `IMAGE`, absent `imageId` | No Image selected. Preserve the Fragment in chronology and render the stable no-selection degraded state. |
| `IMAGE`, `imageId:null` | Same as absent `imageId`. |
| `MARQUEE` / legacy null type, absent or null `imageId` | Normal Marquee/legacy state; no catalogue Image relationship. |
| `MARQUEE` with positive `imageId` | Invalid cross-type relationship. Preserve otherwise valid Page-owned chronology, diagnose it, ignore the Image for rendering, and do not change type. |
| Any present `imageId <= 0` | Structurally invalid Fragment payload; reject and count it. |

Do not infer an Image from Fragment text, filenames, legacy HTML, neighbouring Fragments, or Marquee relationships.

## 4. Fragment type contract

The existing rolling-migration compatibility rule remains:

```text
absent type or explicit JSON null type -> legacy MARQUEE semantics
```

This is different from an unknown explicit type.

For 0026 the internal model must preserve four distinguishable cases:

| Input | Internal semantic kind | Raw diagnostic value |
| --- | --- | --- |
| property absent | `LEGACY_MARQUEE` compatibility state | null |
| JSON `null` | `LEGACY_MARQUEE` compatibility state | null |
| `"MARQUEE"` | `MARQUEE` | null |
| `"IMAGE"` | `IMAGE` | null |
| any other non-null string, e.g. `"VIDEO"` | `UNKNOWN` | exact supplied string |

The implementation may represent this minimally as an `UNKNOWN` sentinel plus a raw-type diagnostic field, or an equivalent value object. It must **not** map an unknown explicit value to null or MARQUEE. An otherwise valid Page-owned unknown-type Fragment remains in chronology and renders Page/text context without inferred Image or Marquee media.

A non-string/non-null type token is malformed input, not an unknown future enum value; reject and count it.

## 5. Media-resolution states

Later projection/rendering work must preserve these distinct states. The names below are the contract names; implementation classes may use equivalent names if the mapping remains one-to-one.

| Contract state | Meaning | Projection/reader behavior |
| --- | --- | --- |
| `NOT_APPLICABLE` | MARQUEE/legacy Fragment or unsupported type has no catalogue media to resolve | No catalogue `<img>` is constructed. |
| `NO_SELECTION` | Known IMAGE Fragment has absent/null `imageId` | Keep chronology/Page/text. Display “No image selected”. |
| `AVAILABLE` | Positive `imageId` resolves to valid retained Image metadata and a safe URL can be constructed | Render catalogue media; file bytes may still fail later. |
| `MISSING_METADATA` | Positive `imageId` has no valid Image entity and no rejected current Image payload is known for that ID | Keep chronology/Page/text. Display “Image unavailable”. |
| `INVALID_METADATA` | The reader has seen/rejected Image metadata for the referenced ID in the current projection generation, including invalid path metadata | Keep chronology/Page/text. Display “Image unavailable”; retain rejection diagnostics. |
| `UNSUPPORTED_TYPE` | Fragment carries an unknown explicit non-null type | Keep otherwise valid Page-owned chronology/Page/text; no inferred Image or Marquee. |

A browser file-load failure is deliberately **not** an Image-metadata state. After `AVAILABLE` metadata has produced a valid URL, HTTP 404, network error, unsupported/corrupt bytes, or image decode failure becomes the ephemeral browser presentation state `FILE_LOAD_FAILED`. It must not be interpreted as proof that the database Image is absent, and it must not remove or tombstone projection metadata.

## 6. Tombstones and topic identity

- A **zero-byte retained payload** on a canonical entity topic is a tombstone.
- Tombstone identity comes from the canonical topic; no JSON body is required.
- JSON `null` is malformed replacement data, not a tombstone.
- For non-empty Image payloads, topic ID and payload `id` must be identical.
- A mismatch rejects the update and increments invalid-message diagnostics; it must not delete or replace a previously valid entity.
- Unknown additive fields do not invalidate an otherwise valid payload.

## 7. Malformed replacement policy

The existing decoder/client boundary is preserved: decoding/validation happens before `ProjectionService.accept(...)`. If decoding fails, `MqttProjectionClient` records an invalid message and does not emit a projection event.

Therefore, for the active ready generation:

1. a valid entity remains the active value when a malformed replacement for the same topic is received;
2. the rejected update increments the invalid-message count;
3. only a subsequent valid upsert replaces it;
4. only a valid zero-byte tombstone removes it.

Reconnect/replay has one important lifecycle qualification: replay uses a fresh staging map. A malformed retained payload cannot reconstruct an entity that is no longer validly replayed. The previous ready generation may remain visible while replay is in progress, but the new staging generation must not copy an old Image merely to conceal malformed retained state. This is the existing atomic-replay rule, not an exception to malformed-live-update handling.

## 8. Caption and alt-text semantics

`caption` and `altText` are metadata text, never HTML.

- Preserve a present string exactly, including the empty string and whitespace-only content.
- Treat an absent property as `""` for reader compatibility.
- Reject explicit JSON `null` because it violates the current responder publication contract.
- Escape both normally at HTML-rendering boundaries.
- `altText` supplies the `<img alt>` value. Empty alt text stays empty; do not synthesize it from `caption`, `originalFilename`, Fragment text, or path.
- Caption is rendered separately when the later rendering step decides it is present; it is never passed through the Fragment HTML sanitizer as trusted HTML.

## 9. Contract examples

### Valid Image metadata

```json
{
  "id": 60,
  "version": 3,
  "relativePath": "1829/06/img2893-detail.jpg",
  "mimeType": "image/jpeg",
  "originalFilename": "img2893-detail.jpg",
  "width": 1600,
  "height": 900,
  "checksum": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "caption": "Detail from the source page",
  "altText": ""
}
```

Unknown additive fields may appear and are ignored.

### IMAGE Fragment with explicit null selection

```json
{
  "id": 50,
  "version": 0,
  "year": 1829,
  "month": 6,
  "day": 26,
  "sequence": 2,
  "text": "<p>Map detail</p>",
  "pageId": 22,
  "type": "IMAGE",
  "imageId": null,
  "marqueeId": null
}
```

Omitting `imageId` has exactly the same no-selection meaning.

### Unknown explicit Fragment type

```json
{
  "id": 51,
  "version": 0,
  "year": 1829,
  "month": 6,
  "day": 26,
  "sequence": 3,
  "text": "<p>Future typed content</p>",
  "pageId": 22,
  "type": "VIDEO"
}
```

This must later resolve as an unsupported-type Page-owned row with raw diagnostic type `VIDEO`; it must not become MARQUEE.

## 10. Step boundaries

Step 2 deliberately does not:

- add `ImageItem` or Image retained decoding;
- add `EntityType.IMAGE` or `images/+` subscriptions;
- add an Image projection map;
- alter broker ACLs;
- build Files URLs;
- render catalogue `<img>` elements;
- change production authoring or `imageFragmentWritesEnabled`.

Those remain the responsibility of Steps 3 onward. The machine-readable matrix in `diaries-web/src/test/resources/fixtures/image-reader-contract-cases.json` is intended to be reused as those steps become executable.
