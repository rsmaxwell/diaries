# 0026 Step 8 — Extend HTTP view models for typed media

**Complete locally — 2026-09-29.** The Step 8 source has been verified on the normal Windows Java 25/Docker development machine. The focused HTTP/config/rendering suite passed, followed by a successful full `:diaries-web:test :diaries-web:build` run.

## Implemented behaviour

- `WebServer` builds one shared typed-media fragment view and uses it for both month-reader and source-page responses.
- Every fragment view carries `fragmentType`, `mediaState`, type-safe `hasMarquee`, optional `mediaUrl`, `mediaAltText`, `mediaCaption`, `mediaWidth`, `mediaHeight`, and `mediaUnavailableText`.
- Legacy/null type is exposed to the HTTP layer as effective `MARQUEE`; known IMAGE is `IMAGE`; an unknown explicit type preserves its raw retained string (for example `AUDIO`) while remaining `UNSUPPORTED_TYPE`.
- IMAGE always exposes `hasMarquee=false`, even if inconsistent retained data links a Marquee to that Fragment.
- `AVAILABLE` IMAGE media derives its browser URL only through the Step 7 `ImageUrlBuilder.catalogueImageUrl(relativePath)` path. No database, filesystem or per-image HTTP lookup is added.
- `NO_SELECTION` supplies `No image selected`; `MISSING_METADATA` and `INVALID_METADATA` supply `Image unavailable`; unknown explicit type supplies `Unsupported fragment type`.
- Catalogue URL/dimensions use `mediaUrl` / `mediaWidth` / `mediaHeight`. Page scan URL/dimensions remain distinct as `pageImageUrl` / `pageWidth` / `pageHeight` in the month model. The existing month template's `imageUrl` field remains as a compatibility alias until Step 9 changes the template.
- The source-page top-level Page model likewise carries explicit `pageImageUrl` while retaining its existing `imageUrl` alias.
- Fragment HTML still uses the existing sanitizer and legacy image resolver. Catalogue URL/caption/alt values remain ordinary model strings; they are not inserted into the raw Fragment-HTML slot. Step 9 will render those values with Pebble's normal escaping.
- Existing Page ownership, chronology, month/day/fragment redirects, deep links, GET/HEAD handling, errors, readiness and ETag behaviour are unchanged by Step 8.

## Controlled fixture and focused coverage

`TestData.readyMixedMediaProjection()` supplies a Page-owned mixed fixture containing:

- two IMAGE Fragments sharing one valid catalogue Image;
- one IMAGE referencing missing metadata;
- one unknown explicit `AUDIO` Fragment;
- one IMAGE with no `imageId`;
- one IMAGE whose referenced Image metadata is marked invalid for the current projection generation;
- a deliberately invalid Marquee link to an IMAGE Fragment, proving `hasMarquee=false` at the HTTP view boundary.

`WebServerTest` verifies the shared typed-media view fields and checks month/source HTTP responses, Fragment redirect and HEAD behaviour. The Step-8 templates deliberately do not render catalogue media yet; that is Step 9.

## Validation performed

The authoritative user console output is preserved verbatim in `test-results.txt` and was captured after the Step 8 implementation package was applied.

Focused Step 8 verification:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*WebServerTest" `
  --tests "*RenderingSafetyTest" `
  --tests "*ConfigLoaderTest" `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 12s**, 7 actionable tasks, all executed.

Full web regression/build gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 50s**, 15 actionable tasks, all executed.

The compiler emitted deprecated-API notes for `ConfigLoader.java` and `ProjectionServiceTest.java`; neither is a test/build failure. The supplied Gradle console does not print an aggregate JUnit test count, so this record does not infer one.

`static-verification.txt` records the assistant-side source review performed before the normal development-machine run. Its earlier Gradle limitation is superseded by the successful user verification above.

## Completion decision

Step 8 is complete locally because:

- both reader surfaces receive one consistent typed-media HTTP view model;
- Fragment type, media state, type-safe Marquee selection, catalogue URL, alt/caption/dimensions and stable degraded-state text are supplied without extra database/filesystem/per-image lookups;
- Page scan and catalogue Image URL/dimension fields remain explicitly distinct;
- shared Images, missing/invalid metadata, no-selection IMAGE, unknown explicit type and invalid IMAGE→Marquee data are covered by the controlled fixture;
- existing redirects, HEAD handling, ownership and sanitized Fragment HTML behaviour remain covered;
- the focused HTTP/config/rendering verification passes;
- the complete `diaries-web` test/build gate passes after the final Step 8 source.

## Step boundary

Step 8 deliberately does **not** render the new catalogue-media fields in Pebble templates, alter CSS, change fragment-selection JavaScript, perform file-load error handling, deploy a production image, or enable ImageFragment authoring. Those are later 0026 steps.

**Next:** Step 9 — Render accessible media in month and source-page views.
