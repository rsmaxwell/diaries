# 0026 Step 7 — Add runtime Files configuration and safe catalogue URLs

**Complete locally — 2026-09-29.** Runtime Files routing and catalogue URL safety have been verified on the normal Windows Java 25/Docker development machine. The focused configuration/rendering/HTTP suite passed, followed by a successful full `:diaries-web:test :diaries-web:build` run.

## Implemented behaviour

- `content.filesPath` is a runtime setting with documented/default value `files`.
- `ConfigLoader` supplies that default when older JSON omits the property while retaining strict unknown-property handling.
- `ContentConfig` validates and normalises nested Files routes. Leading/trailing separators are normalised; empty/dot/dot-dot segments, backslashes, URI-like colon syntax, query/fragment markers, control characters and non-NFC route text are rejected.
- `content.publicResponderBaseUrl` is validated as either an HTTP(S) browser-visible URL without userinfo/query/fragment/ambiguous encoded separators, or a same-origin rooted path such as `/diaries-responder`.
- `ImageUrlBuilder.catalogueImageUrl(relativePath)` validates canonical Image paths and percent-encodes each literal segment exactly once while preserving real `/` separators.
- Literal spaces, `+`, `%`, `#`, `?`, quotes and Unicode are encoded. Persisted percent-like strings are not decoded first, so stored percent text cannot silently become path structure.
- Page image URL construction remains unchanged.
- Legacy importer `images/<filename>` handling remains separate and now uses configured `filesPath`; with the default `files`, previous `/files/{diary}/images` output remains unchanged.
- CSP behaviour remains origin-scoped. No arbitrary origin, inline-script or unsafe-scheme broadening was introduced.

## Deployment/routing guardrail

The routing review in `routing-review.md` covers development infrastructure, local-docker-build, local-published-smoke, shared production and standalone production.

Production Ansible currently generates a strict JSON file without `filesPath`. That remains valid with this Step-7 binary because the loader defaults the missing setting to `files`. Do not add the new property to an older deployed `diaries-web` binary that does not understand it. The coordinated production template update remains later release work.

## Validation performed

The authoritative user console output is preserved verbatim in `test-results.txt` and was captured after the Step 7 implementation package was applied.

Focused Step 7 verification:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*ConfigLoaderTest" `
  --tests "*RenderingSafetyTest" `
  --tests "*WebServerTest" `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 6s**, 7 actionable tasks, all executed.

Full web regression/build gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 49s**, 15 actionable tasks, all executed.

The compiler emitted deprecated-API notes for `ConfigLoader.java` and `ProjectionServiceTest.java`; neither is a test/build failure. The supplied Gradle console does not print an aggregate JUnit test count, so this record does not infer one.

## Completion decision

Step 7 is complete locally because:

- the Files route is runtime-configured with backward-compatible defaulting;
- browser-visible responder bases and Files-route syntax are constrained to the supported safe forms;
- catalogue Image URLs derive only from validated runtime routing plus validated `Image.relativePath`;
- literal path segments are encoded exactly once, including traversal-shaped percent text;
- Page URLs and default legacy `/files` URLs retain their previous output;
- the focused configuration/rendering/HTTP verification passes;
- the complete `diaries-web` test/build gate passes after the final Step 7 source.

## Step boundary

Step 7 deliberately does **not** attach catalogue URLs to HTTP view models, render IMAGE media in templates, change selection JavaScript, publish/deploy a production image, edit production Ansible configuration, or enable ImageFragment authoring.

**Next:** Step 8 — Extend HTTP view models for typed media.
