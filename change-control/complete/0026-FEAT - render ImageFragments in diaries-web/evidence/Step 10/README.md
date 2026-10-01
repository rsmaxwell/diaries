# 0026 Step 10 — Make selection, history and media errors type-aware

**Complete locally — 2026-09-29.** The Step 10 source has been verified on the normal Windows Java 25/Docker development machine and the core synthetic-browser completion criteria have been demonstrated in both month-reader and source-page views.

## Implemented behaviour

- Month-reader selection consumes `fragmentType` as well as `hasMarquee`. A valid IMAGE selection is not described as a broken source region.
- MARQUEE → IMAGE on the same Page clears the selected SVG rectangle/mask state, removes the selected Marquee presentation, disables **Fit selection** and **Use highlight style**, and resets stale fit-to-selection state. Page-level **−**, **+** and **Fit page** controls intentionally remain available because they operate on the source Page rather than a Marquee.
- IMAGE → MARQUEE restores the selected region and the Marquee-specific controls.
- Source-page selectors work for Page-owned MARQUEE and IMAGE Fragments. Selection updates the URL hash/history and Back/Forward restores the appropriate Fragment state.
- Catalogue Image byte/decode failure remains distinct from retained Image metadata. Browser `error` exposes an ephemeral `FILE_LOAD_FAILED` state, hides the broken `<img>`, leaves the direct-image link/caption available, and does not rewrite `src` or mutate the server-rendered canonical media state.
- Source-scan load/error state remains independent from catalogue-media load/error state.
- No browser MQTT/RPC/live-update subsystem is introduced.

## Automated verification

The authoritative user console output is preserved verbatim in `test-results.txt`.

Focused Step 10 verification:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*WebServerTest" `
  --tests "*RenderingSafetyTest" `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 11s**, 7 actionable tasks, all executed.

Full web regression/build gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 50s**, 15 actionable tasks, all executed.

The compiler emitted deprecated-API notes for `ConfigLoader.java` and `ProjectionServiceTest.java`; neither is a test/build failure. The supplied Gradle console does not print an aggregate JUnit test count, so this evidence does not infer one.

## Interactive browser verification

The detailed observed results are recorded in `browser-verification-results.md`; representative screenshots are under `screenshots/`.

Verified on the synthetic site:

- Month-reader MARQUEE → IMAGE removes the Marquee and disables the two region-specific controls while retaining Page-level zoom/Fit-page controls.
- IMAGE → MARQUEE restores the Marquee and the region-specific controls.
- Month-reader browser Back/Forward restores the correct typed selection.
- The failed synthetic catalogue request reports `FILE_LOAD_FAILED`; the image element reports `hidden == true`; the visible status text is `The image file could not be loaded.`
- Source-page IMAGE and MARQUEE selection both work; the Marquee is shown/hidden appropriately; source-page browser Back/Forward restores the correct selection.

The synthetic content host intentionally does not provide the Page/catalogue bytes. These are fixture failures used to verify the browser failure path, not production/NAS failures.

The focused manual run demonstrates the Step 10 completion condition. The broader keyboard/focus/late-event browser matrix remains part of Step 11's dedicated focused coverage rather than being silently claimed here.

## Completion decision

Step 10 is complete locally because:

- selecting IMAGE does not leave a previous Marquee highlighted;
- returning to MARQUEE restores region selection correctly;
- Page controls remain usable when IMAGE has no Marquee;
- month-reader and source-page history restore typed Fragment selection correctly;
- media-byte failure produces the required browser-only `FILE_LOAD_FAILED` state without corrupting retained/projected media state;
- the focused test gate passes;
- the complete `diaries-web` test/build gate passes after the final Step 10 source.

## Step boundary

Step 10 does **not** claim production deployment/readiness, full browser automation, broker/replay end-to-end coverage, cross-component development verification, or ImageFragment authoring enablement. Those remain later 0026 steps.

**Next:** Step 11 — Add focused projection, rendering and security coverage.
