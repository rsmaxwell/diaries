# 0026 Step 11 — Add focused projection, rendering and security coverage

**Complete locally — 2026-09-29.**

Step 11 hardens the test/evidence surface built incrementally during Steps 2–10. It intentionally changes no production runtime code. Existing MARQUEE regression cases remain in place; the Step 11 additions make the IMAGE/degraded/security matrix explicit and deterministic.

## Completion evidence

The focused Java 25 verification completed successfully:

```text
BUILD SUCCESSFUL in 11s
7 actionable tasks: 7 executed
```

The complete `:diaries-web:test :diaries-web:build` gate also completed successfully:

```text
BUILD SUCCESSFUL in 50s
15 actionable tasks: 15 executed
```

The exact console transcript is preserved in `test-results.txt`.

Browser verification against the Step 11 deterministic local content fixture confirmed:

- the source Page image loads successfully on the normal fixture path;
- Fragment 35 remains `data-media-state="AVAILABLE"`;
- its catalogue `<img>` remains visible and uses the expected exactly-once encoded URL;
- alt/caption values remain escaped in browser-visible markup;
- IMAGE selection exposes no selected Marquee and keeps region-only controls disabled;
- keyboard Enter/Space changes Fragment selection and focus remains visible.

The exact browser observations are preserved in `browser-verification-results.txt`. The Step 10 browser evidence is also intentionally reused for the browser-only `FILE_LOAD_FAILED` branch: a failed catalogue media request set `data-media-file-state="FILE_LOAD_FAILED"`, hid the `<img>`, preserved the canonical projection media state, and displayed `The image file could not be loaded.`. Step 11's local content harness supplies deterministic HTTP-404 and HTTP-200-invalid-image endpoints for that same browser `error` path, so no NAS or production file is needed to reproduce it.

## Focused coverage completed

- `RetainedContractTest`: additive Image fields, tombstones, topic/payload ID mismatch, explicit legacy `type:null`, unknown future explicit Fragment type.
- `ProjectionServiceTest`: missing ownership/Page/Diary, MARQUEE/IMAGE cross-type inconsistencies, no selection, missing/rejected Image metadata, unknown explicit type, legacy fallback and chronology preservation.
- `ConfigLoaderTest`: default/nested Files routes, Unicode/percent handling and public/internal responder separation.
- `RenderingSafetyTest`: public-only catalogue URLs, exactly-once path encoding, persisted absolute-URL rejection, escaped media metadata and strict `| raw` boundary.
- `WebServerTest`: mixed chronology, degraded states, source/month views, redirects/deep links, GET/HEAD-only behavior, missing ownership and CSP/internal-address exclusion.
- synthetic browser fixture: valid local image bytes plus deterministic 404 and invalid-image-byte endpoints.

## Step boundary

Step 11 adds coverage and deterministic browser fixtures only. It does not add production runtime behavior, real-broker end-to-end replay verification, cross-component development deployment, production deployment or ImageFragment authoring. Those remain Steps 12–16.

**Next:** Step 12 — Verify real MQTT replay, permissions and HTTP projection.
