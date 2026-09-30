# 0026 Step 9 — Render accessible media in month and source-page views

**Complete locally — 2026-09-29.** The Step 9 source has been verified on the normal Windows Java 25/Docker development machine. The focused rendering/safety suite passed, followed by a successful full `:diaries-web:test :diaries-web:build` run.

## Implemented behaviour

- `month-reader.peb` keeps the original Page scan on the left and renders IMAGE Fragment text plus its catalogue Image on the right.
- `source-page.peb` keeps the source Page/Marquee view and renders the same typed catalogue media beneath each Fragment's text.
- Both templates render an `<img>` only when `mediaUrl` is present. `NO_SELECTION`, `MISSING_METADATA`, `INVALID_METADATA` and `UNSUPPORTED_TYPE` therefore never produce an empty or `null` `src`; their stable `mediaUnavailableText` is rendered separately instead.
- Catalogue `altText` is written to the normal Pebble-escaped `alt` attribute. Empty catalogue alt text remains `alt=""`; no filename-derived description is invented.
- Caption is rendered separately in an optional `<figcaption>` and remains normal escaped Pebble data rather than raw Fragment HTML.
- Image metadata `width` and `height` attributes provide intrinsic aspect-ratio/layout information. CSS uses `max-width: 100%` and `height: auto`, so wide/tall content scales responsively without cropping or distortion while small images are not deliberately stretched.
- Every available catalogue Image also has a normal `Open image directly` link. This remains usable without JavaScript and remains visible if the browser cannot render the image bytes. Browser-enhanced `FILE_LOAD_FAILED` handling remains Step 10.
- The templates consume the explicit Step-8 `pageImageUrl` field for Page scans rather than the temporary `imageUrl` compatibility alias.
- Month-reader selector wording is type-safe: a Fragment without a Marquee promises only to show its original source Page, not a nonexistent transcription region.
- Catalogue media has no generated HTML `id`, so two Fragments may reuse the same Image URL without duplicate DOM IDs.
- Existing MARQUEE overlay/source-page markup and navigation are otherwise unchanged.

## Controlled fixture and focused coverage

The mixed-media fixture covers:

- an Image with documented empty alt text and empty caption;
- a tall Image (400×1600) with long HTML-like caption text that must remain escaped;
- a wide Image (2400×300);
- a small Image (64×48);
- an IMAGE Fragment with empty transcription text;
- two Fragments reusing one shared Image;
- missing, invalid, no-selection and unknown-type degraded states.

`WebServerTest` verifies both month and source-page HTML for escaped alt/caption values, empty alt, intrinsic dimensions, responsive CSS, reused Image rendering, one media container per Fragment, no empty/null media `src`, degraded-state text, and the type-safe non-Marquee selection wording. `RenderingSafetyTest` remains in the focused gate so the existing sanitization/escaping boundary is exercised alongside the new template rendering.

## Validation performed

The authoritative user console output is preserved verbatim in `test-results.txt` and was captured after the Step 9 implementation package was applied.

Focused Step 9 verification:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*WebServerTest" `
  --tests "*RenderingSafetyTest" `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 6s**, 7 actionable tasks, all executed.

Full web regression/build gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 49s**, 15 actionable tasks, all executed.

The compiler emitted deprecated-API notes for `ConfigLoader.java` and `ProjectionServiceTest.java`; neither is a test/build failure. The supplied Gradle console does not print an aggregate JUnit test count, so this evidence does not infer one.

`static-verification.txt` records the assistant-side source review performed before the normal development-machine run. Its earlier Gradle limitation is superseded by the successful user verification above.

## Completion decision

Step 9 is complete locally because:

- both reader surfaces render typed catalogue Image media only when a safe `mediaUrl` is available;
- alt/caption metadata is rendered through normal escaping, including explicit empty alt text;
- degraded media states cannot create empty/null image requests;
- Page scan media and catalogue Image media remain distinct;
- intrinsic dimensions and responsive CSS cover tall, wide and small Images without deliberate distortion;
- reused Images render for each referring Fragment without duplicate generated media IDs;
- a normal direct-image link provides server-rendered/no-JavaScript fallback;
- the focused rendering/safety verification passes;
- the complete `diaries-web` test/build gate passes after the final Step 9 source.

## Step boundary

Step 9 deliberately does **not** add browser-side catalogue Image load-error state, alter selection/history media behaviour, add production configuration, publish/deploy a `diaries-web` image, or enable ImageFragment authoring. Those remain later 0026 steps.

**Next:** Step 10 — Make selection, history and media errors type-aware.
