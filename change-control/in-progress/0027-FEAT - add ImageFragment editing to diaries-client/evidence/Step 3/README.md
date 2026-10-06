# Step 3 evidence — first-class client Image model and retained lookup

## Scope

Step 3 introduces the client-side retained Image foundation required by later 0027 authoring steps. It deliberately does **not** add ImageFragment creation/edit controls or change the responder.

Implemented production changes:

- `diaries-client/src/app/model/image.ts`
  - adds metadata-only `CatalogueImage` matching responder `ImagePublishDTO`;
- `diaries-client/src/app/model/model-context.ts`
  - adds `getLiveImage$(id)` on `diaries/images/<id>`;
  - adds share-replayed `selectedImage$`;
  - returns `null` immediately for unresolved/new references and on retained tombstones;
  - avoids re-subscribing when an ordinary Fragment update keeps the same `imageId`;
- `diaries-client/src/app/utilities/catalogue-image-url.ts`
  - centralises HTTP/static-file URL construction from runtime responder base URL, configured Files root and `Image.relativePath`.

Focused regression coverage:

- retained Image resolution for selected IMAGE Fragment;
- already-retained/replayed Image metadata;
- same-topic Image metadata updates;
- MARQUEE and unattached IMAGE null state;
- tombstone -> null transition;
- imageId switch -> immediate null while unresolved -> new Image;
- static URL construction and segment encoding;
- rejection of malformed/non-canonical relative path forms at the presentation helper boundary.

## Contract notes

The retained Image model is metadata only:

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

There is no Image byte/blob/base64 field and no persisted absolute URL. Bytes continue to use the responder/static Files HTTP path.

Legacy/null Fragment `type` is still MARQUEE by the existing rolling-migration rule. `selectedImage$` therefore resolves only explicit `type: 'IMAGE'` Fragments.

## Validation limitation

The complete Angular suite cannot be bootstrapped in this implementation sandbox because the source bundle does not contain `node_modules`. `npm test` therefore has no local `ng`, while `npm ci --offline` fails because `zone.js@0.15.1` is not present in the npm cache. The exact commands/output are retained in `angular-test-attempt.txt`.

The dependency-free Step 3 model/URL helper compile with TypeScript 5.8.3, the URL helper behavior smoke passes, and all changed TypeScript files pass TypeScript syntax transpilation. See `validation.txt`.
