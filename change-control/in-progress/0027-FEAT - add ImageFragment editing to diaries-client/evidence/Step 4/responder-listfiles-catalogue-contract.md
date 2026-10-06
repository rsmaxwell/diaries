# Step 4 responder `listFiles` catalogue enrichment

During Step 4 implementation the current source bundle exposed a contract mismatch:

- `uploadFile` already returned `imageId` plus nested `ImagePublishDTO` metadata;
- the client compatibility fixtures anticipated the same additive fields on `listFiles` entries;
- the production `ListFiles` handler still emitted only filesystem metadata.

Step 4 closes that mismatch additively. For each listed regular image file the responder resolves its canonical Files-relative path against the Image repository. If an Image row exists, the returned `ImageItem` includes:

```text
imageId
image
```

Directories and uncatalogued files keep those fields null/omitted because `ImageItem` uses NON_NULL JSON inclusion. The existing name/url/size/mtime/dateTaken/dir fields are unchanged.

This lets the client select by persisted Image ID rather than guessing identity from a filename or URL.
