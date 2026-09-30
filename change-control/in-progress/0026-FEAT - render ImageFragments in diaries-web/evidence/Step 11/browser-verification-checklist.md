# Step 11 browser verification checklist

Start the deterministic synthetic site from the top-level `diaries` directory:

```powershell
.\gradlew.bat :diaries-web:runSyntheticSite
```

The harness starts:

```text
reader site:       http://127.0.0.1:18082
synthetic content: http://127.0.0.1:18083
```

The content server is local test infrastructure. It serves visible valid PNG bytes for normal Page/catalogue requests and two controlled failures. No NAS or production service is used.

## 1. Normal IMAGE and source Page bytes

Open:

```text
http://127.0.0.1:18082/diaries/11/2026/09?fragment=35#fragment-35
```

Verify:

- the source Page image loads without `The source image could not be loaded.`;
- Fragment 35 remains `data-media-state="AVAILABLE"`;
- its catalogue `<img>` is not hidden and no `data-media-file-status` failure is shown;
- IMAGE selection has no selected Marquee and the region-only controls stay disabled;
- keyboard Enter/Space on Fragment selectors changes selection and focus remains visible.

## 2. HTTP 200 but invalid image bytes

Open/select Fragment 45 (`Invalid image bytes`):

```text
http://127.0.0.1:18082/diaries/11/2026/09?fragment=45#fragment-45
```

In DevTools Network, the catalogue request to port `18083` must be HTTP 200. In the console verify:

```javascript
document.querySelector('[data-fragment-media="45"]').dataset.mediaFileState
document.querySelector('[data-fragment-media="45"] img').hidden
document.querySelector('[data-fragment-media="45"] [data-media-file-status]').textContent
document.querySelector('[data-reader-fragment="45"]').dataset.mediaState
```

Expected:

```text
FILE_LOAD_FAILED
true
The image file could not be loaded.
AVAILABLE
```

This is the required distinction between valid retained metadata and invalid physical bytes.

## 3. HTTP 404 physical file

Open/select Fragment 46 (`Missing image file`):

```text
http://127.0.0.1:18082/diaries/11/2026/09?fragment=46#fragment-46
```

Verify the port-18083 request is HTTP 404 and the same browser-only `FILE_LOAD_FAILED`/hidden/status behavior appears while canonical `data-media-state` remains `AVAILABLE`.

## 4. Metadata/reference states do not become file failures

Select:

- Fragment 37: expected canonical `MISSING_METADATA`, text `Image unavailable`, no catalogue `<img>`.
- Fragment 39: expected canonical `NO_SELECTION`, text `No image selected`, no catalogue `<img>`.
- Fragment 40: expected canonical `INVALID_METADATA`, text `Image unavailable`, no catalogue `<img>`.

None should fabricate a URL or report `FILE_LOAD_FAILED`, because the browser never received a valid media URL to load.

## 5. Cross-type / history / responsive regression

- Fragment 35 has deliberately inconsistent retained IMAGE→Marquee test data; selecting it must still show no selected Marquee.
- Move MARQUEE → IMAGE → MARQUEE, then use Back/Forward; overlay and typed selection must restore correctly.
- Repeat IMAGE/MARQUEE selection on `http://127.0.0.1:18082/diaries/11/pages/22`.
- Narrow the viewport below 48rem (or use device emulation): source/month layouts must become one column and catalogue media must remain within its container without horizontal overflow.
- Rapidly move between fragments on different Pages and IMAGE/MARQUEE types; a late prior source-image event must not overwrite the currently selected Page/status. No timed sleep is required—observe the current selection after network activity settles.

Record any unavailable browser prerequisite as **blocked**, not passed.
