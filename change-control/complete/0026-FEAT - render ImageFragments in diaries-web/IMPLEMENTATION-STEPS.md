# 0026 — Render ImageFragments in diaries-web: implementation steps

Prepared 2026-09-28 from the current workspace and the completed 0025 contract.

This plan records execution only where explicitly linked to evidence. Preserve the feature identifier and record each implementation step under `evidence/Step N/`. Do not mark a step complete solely because its source changes compile.

## Execution status — 2026-10-01

- **Step 1 complete:** [frozen web baseline and evidence](evidence/Step%201/README.md). Parent/web/responder identities and 267 source hashes recorded; 50 web tests passed, including both Docker-backed integration tests, with zero skips; build passed; synthetic MARQUEE screenshots and browser/HTTP deep-link checks captured. Application source remains unchanged.
- **Step 2 complete:** [Image reader contract and degraded states](evidence/Step%202/README.md), with the shared [contract](IMAGE-READER-CONTRACT.md), machine-readable cases and executable contract tests.
- **Step 3 complete:** [canonical Image model, decoding and events](evidence/Step%203/README.md). Recorded focused tests and full web tests/build passed; that full suite contained 94 tests with zero failures, errors or skips, including both Docker-backed integration tests. All 13 recorded source hashes matched at Step-3 close-out, before Step-4 changes.
- **Step 4 complete locally:** [reader subscriptions and minimum broker permissions](evidence/Step%204/README.md). Five canonical subscriptions and minimum Image read permission verified with the actual `diaries-web` identity and committed ACL. Full web tests/build: 107 passed, zero failures/errors/skips; all three Compose configs passed. Explicit SUBACK failure remains unready; Mosquitto's silent read filtering requires a separate deployed-delivery check, documented in the evidence.
- **Step 5 complete locally:** [immutable Image projection storage](evidence/Step%205/README.md). Image upsert/update/tombstone lifecycle, immutable snapshot lookup/count APIs, reconnect isolation and status count are implemented and verified. After the test-only generic-inference correction, the focused projection/contract/HTTP run passed, the MQTT/Testcontainers integration run passed, and the full `:diaries-web:test :diaries-web:build` completed successfully on the normal Windows Java 25/Docker development machine.
- **Step 6 complete locally:** [mixed Fragment resolution and diagnostics](evidence/Step%206/README.md). Mixed MARQUEE/IMAGE/unknown resolution, degraded media states, shared Image references, relationship repair and type-specific diagnostics are implemented. The focused projection/contract/MQTT suite passed and the full `:diaries-web:test :diaries-web:build` completed successfully on the normal Windows Java 25/Docker development machine.
- **Step 7 complete locally:** [runtime Files configuration and safe catalogue URLs](evidence/Step%207/README.md). Backward-compatible `content.filesPath`, safe browser-visible responder-base validation, exactly-once catalogue path encoding, Page URL regression protection and legacy Files-route compatibility are implemented and verified. The focused configuration/rendering/HTTP suite passed and the full `:diaries-web:test :diaries-web:build` gate completed successfully on the normal Windows Java 25/Docker development machine.
- **Step 8 complete locally:** [typed HTTP media view models](evidence/Step%208/README.md). Month-reader and source-page HTTP models now share the same typed-media resolution, distinguish Page scan fields from catalogue Image fields, expose stable degraded-media states, preserve type-safe `hasMarquee`, and retain existing redirects/HEAD/ownership behaviour. The focused HTTP/config/rendering suite passed and the full `:diaries-web:test :diaries-web:build` gate completed successfully on the normal Windows Java 25/Docker development machine.
- **Step 9 complete locally:** [accessible mixed-media rendering](evidence/Step%209/README.md). Both reader templates render catalogue Images only for available media, use escaped catalogue alt/caption metadata, keep stable degraded-state text separate from alt text, preserve Page context, and use responsive intrinsic dimensions plus a no-JavaScript direct-image link. The focused rendering/safety suite passed and the full `:diaries-web:test :diaries-web:build` gate completed successfully on the normal Windows Java 25/Docker development machine.
- **Step 10 complete locally:** [type-aware selection, history and media errors](evidence/Step%2010/README.md). IMAGE selection clears stale MARQUEE geometry and disables only region-specific controls; MARQUEE selection restores the region controls; month-reader and source-page Back/Forward restore typed selection; catalogue byte/decode failure is exposed as browser-only `FILE_LOAD_FAILED` while the broken `<img>` is hidden and retained media state remains unchanged. Focused tests and the full web test/build gate passed on the normal Windows Java 25/Docker development machine, and the core synthetic-browser completion criteria were demonstrated.
- **Steps 11–12 complete locally:** focused security/projection/HTTP tests, real broker/ACL/reconnect and 5,376-topic retained replay verified; see [Step 11](evidence/Step%2011/README.md) and [Step 12](evidence/Step%2012/README.md).
- **Step 13 complete locally:** the owned development fixture ran successfully on 2026-09-30 with real responder, MQTT, web, desktop/mobile browsers, protected Image deletion and restart/replay; see [verified run](evidence/Step%2013/verified-run-20260930-192857/summary.json).
- **Step 14 complete:** the [full regression and artifact verification](evidence/Step%2014/README.md) passed against the exact release candidate on 2026-10-01.
- **Step 15 complete in production:** the [production deployment evidence](evidence/Step%2015/README.md) records the exact image tags/IDs, explicit `content.filesPath=files`, disabled responder authoring gate, read-only Image ACL, healthy services and successful Pluto reader/File-route smoke checks.
- **Step 16 complete:** [final close-out and handoff](evidence/Step%2016/README.md) records the acceptance mapping, final reader policies, release identities and 0027/0028 rollout boundaries; 0026 is moved to `change-control/complete`.

## Objective and boundaries

Make the read-only web reader consume canonical retained Image metadata and render IMAGE and MARQUEE Fragments in the same chronology. An IMAGE Fragment retains its Page context on the left and displays its sanitized text and referenced Image on the right. Missing Image selection, metadata or bytes must not remove a valid Page-owned Fragment from navigation.

The responder remains authoritative. This feature introduces no database migration, Image mutation RPC, file upload/delete UI, filesystem mutation, or client authoring flow. Images are reusable catalogue entries; their paths and bytes must not be copied into Fragment records.

0025 completion establishes a tested responder capability, not proof that its binary, migration, broker changes or authoring gate have been deployed to production. Verify actual deployment state when reaching the release steps. Keep production `imageFragmentWritesEnabled` disabled throughout 0026. Reader readiness is a prerequisite for the separately controlled 0027/0028 rollout, not permission to enable it here.

## Source baseline before implementation

This table preserves the pre-change baseline captured in Step 1; subsequent completed work is recorded above and in the step evidence. Paths below are relative to the top-level `diaries` repository.

| Area | Current behavior | Required extension |
| --- | --- | --- |
| `diaries-web/model/FragmentItem` and `FragmentType` under `src/main/java/com/rsmaxwell/diaries/web` | Already accept nullable `imageId` and explicit IMAGE; absent/null type falls back to MARQUEE | Preserve this contract; distinguish unknown types from legacy null |
| `mqtt/EntityType`, `TopicParser`, `RetainedMessageDecoder` | Four canonical entity families; no Image decoder | Add canonical `images/+`, Image metadata and tombstones |
| `projection/MutableProjectionState`, `ProjectionEvent`, `ProjectionSnapshot` | No Image map; IMAGE rows already enter Page-owned chronology but increment `unsupportedImageFragments` | Resolve optional Images without losing chronology |
| `projection/ResolvedFragment` | Fragment, optional Marquee, Page, Diary | Add optional Image and explicit media resolution state where needed |
| `http/WebServer`, month/source-page templates | Render sanitized text and Page/Marquee view data | Add typed catalogue-media presentation to both reader surfaces |
| `rendering/ImageUrlBuilder` | Builds Page URLs; legacy embedded-image base hard-codes `/files/` | Add configured catalogue Files URL construction without reinterpreting legacy HTML |
| `config/AppConfig.ContentConfig` | Internal/public responder bases and `diariesPath`; no Files path | Add an explicit, backward-compatible Files path |
| `static/js/diaries.js` | Some no-Marquee behavior exists; missing region wording and image events assume transcription selection | Make IMAGE selection intentional and separate source-image/media failure state |
| `diaries-web/AGENTS.md` and broker ACL | Reader restricted to four canonical families | Document/permit read-only canonical Images as explicitly authorized by 0026 |

Use active source, not historical source copies in completed change-control packages. Avoid broad rewrites of the projection, reader or synchronization code.

## Working contracts

### Retained data and ownership

Consume these five families, substituting the configured topic prefix:

```text
diaries/diaries/+
diaries/pages/+
diaries/fragments/+
diaries/marquees/+
diaries/images/+
```

Do not subscribe to date aliases, RPC topics, people/roles, `diaries-sync/#`, or all of `diaries/#`. A zero-byte retained publication removes the corresponding projected entity; it is not JSON `null`.

Image metadata follows `diaries-responder/.../dto/ImagePublishDTO.java`:

```text
id, version, relativePath, mimeType, originalFilename,
width, height, checksum, caption, altText
```

The browser URL is derived from trusted runtime configuration plus `relativePath`. Neither absolute URLs nor image bytes belong in the retained Image contract. Caption and alt text are plain text; Fragment text continues through the existing HTML sanitizer.

### Resolution policy

| Fragment state | Chronology / Page context | Media / overlay behavior |
| --- | --- | --- |
| MARQUEE or legacy null type, valid Page/Diary | Preserve existing chronology | Existing matching Marquee behavior; no catalogue Image |
| MARQUEE with non-null `imageId` | Keep valid Page-owned row; diagnose invalid relationship | Ignore Image for rendering; do not convert type |
| IMAGE with a resolvable `imageId` | Keep row and authoritative Page | Referenced catalogue Image; never a selected Marquee |
| IMAGE with no `imageId` | Keep row and Page | Textual “No image selected” state |
| IMAGE referencing missing/malformed Image metadata | Keep row and Page | Textual “Image unavailable” state |
| IMAGE with an attached or conflicting Marquee pointer | Keep row and Page; diagnose both actual links and pointer anomalies | Ignore Marquee for IMAGE rendering |
| IMAGE whose file fails to load | Keep row, text and navigation | Browser media-load fallback; no change to projection ownership |
| Unknown explicit Fragment type with otherwise valid identity/Page/date | Preserve an unsupported-type row and diagnose it | Text/Page context only; no inferred Image or Marquee |
| Missing Page ownership, missing Page, or missing Diary | Preserve raw entity for later resolution and diagnostics | Follow existing unresolved-owner behavior; do not guess ownership from Image/Marquee |

Do not confuse an unknown explicit type with absent/null legacy type. Do not guess an Image from filename, HTML, neighbouring fragments or Marquee associations.

---

## Step 1 — Freeze the web baseline and establish evidence

**Completed 2026-09-28:** see [Step 1 evidence](evidence/Step%201/README.md), including reproducible commands, deployment limitations and fixture cleanup.

1. Read this feature, completed 0023/0025 evidence, and repository/web guardrails. Record the current execution mode.
2. Record main/web/responder Git HEADs, dirty status and source hashes. Preserve existing uncommitted work.
3. Inspect current deployed reader/responder tags and embedded metadata read-only if available; distinguish verified deployment information from historical evidence.
4. Run the existing web suite/build using the parent wrapper. Record actual test counts and any Docker-gated skips; do not assume the previous 50-test total remains current.
5. Capture representative MARQUEE month/source-page screenshots, deep-link behavior and runtime configuration shape, with credentials redacted.
6. Define an isolated fixture namespace/broker, temporary image directory and cleanup ownership. No production/NAS test mutations.

**Evidence:** baseline identities, SHA inventory, commands/logs, screenshots and fixture plan.

**Complete when:** the pre-change reader behavior is reproducible and the implementation can be attributed to a known working tree.

## Step 2 — Define the Image reader contract and degraded states

**Completed 2026-09-28:** see [Step 2 evidence](evidence/Step%202/README.md) and the [Image reader contract](IMAGE-READER-CONTRACT.md). Its three contract tests also passed in the Step-3 full-suite run.

1. Add a feature contract note or test fixtures documenting the Image fields above, nullable Fragment reference semantics, tombstones, topic/payload ID equality and unknown additive fields.
2. Match authoritative `Image`/`ImagePublishDTO` validation: positive identity/dimensions, non-negative version, required valid path/MIME/checksum metadata. Do not invent a new retained schema or require a deployment URL.
3. Specify handling of absent/blank optional caption/alt text without breaking the responder's current empty-string values. Do not treat caption as HTML.
4. Decide the internal distinction between no selection, missing metadata, invalid metadata/path and unsupported type. File-load failure is a browser presentation state, not proof that the database Image is absent.
5. Define unknown-type handling explicitly: represent an unknown non-null type with a distinct sentinel/raw diagnostic value, never coerce it to null/MARQUEE. Preserve otherwise valid Page-owned chronology. Truly invalid identity/date payloads remain rejected and counted.
6. Define malformed replacement behavior using existing decoder semantics: retain the last valid entity until a valid update/tombstone, count the rejected update, and document that policy.

**Evidence:** contract examples and table-driven test cases, including explicit null versus absent `imageId`.

**Complete when:** the decoder, projection and rendering steps share one unambiguous contract.

## Step 3 — Add canonical Image model, decoding and events

**Completed 2026-09-28:** see [Step 3 evidence](evidence/Step%203/README.md), including successful focused/full Gradle output, the 94-test summary, preserved XML reports and source-hash verification. Live subscriptions and Image storage remain deliberately deferred to Steps 4 and 5.

**Files:** new `model/ImageItem.java`; `mqtt/EntityType.java`, `TopicParser.java`, `RetainedMessageDecoder.java`; `projection/ProjectionEvent.java`; relevant Fragment model/type handling.

1. Add immutable Image metadata and validation; reuse existing validation helpers where appropriate.
2. Add `EntityType.IMAGE("images")`, canonical parsing/filter generation and `UpsertImage`.
3. Decode metadata with the existing unknown-additive-field tolerance and topic/payload ID checks.
4. Add Image tombstone decoding, update exhaustive switches and implement the unknown Fragment type policy from Step 2.
5. Extend `RetainedContractTest`, fixtures and model tests. Cover incorrect types, missing/invalid required fields, hostile paths, empty caption/alt, future fields, zero-byte tombstones and invalid JSON.
6. Keep ordinary MARQUEE payloads with omitted/null `imageId` working exactly as before.

**Complete when:** the five canonical families and both known Fragment types have tested decoding contracts; malformed input cannot terminate the MQTT projection thread.

## Step 4 — Extend reader subscriptions and minimum broker permissions

**Completed locally 2026-09-28:** see [Step 4 evidence](evidence/Step%204/README.md). Real-broker tests prove allowed Image replay and blocked reads/writes; a separate MQTT-5 peer proves explicit rejected SUBACK handling. The shared client-ID RPC reply pattern required a web-user deny. The supplied production-role ACL matches the five web read grants but needs that deny; a checked handoff patch is included. Actual production deployment/reload and delivery verification remain release work. A successful SUBACK alone cannot detect Mosquitto file-ACL silent filtering.

**Files:** `MqttProjectionClient.java`, topic-filter tests; `config/mosquitto/aclfile.txt`, its README; web test broker ACL; `diaries-web/AGENTS.md` canonical-family wording.

1. Subscribe to `images/+` alongside existing canonical filters, using the established QoS/session policy. Review SUBACK and failed-subscription handling so denied Image access is not mistaken for complete readiness.
2. Add read permission for `diaries-web` on canonical `diaries/images/+` only. Keep its credentials external.
3. Prove the reader still cannot publish, call RPC, read date aliases/people/roles or use responder synchronization barriers.
4. Update the web guardrail's four-family wording to include canonical Image metadata; retain all read-only restrictions. This narrow extension is authorized by 0026 itself.
5. Compare the shared ACL mounted by all local modes, test ACL fixtures and the production Ansible-managed equivalent. Document any external repository work; modify it only if included and writable.
6. Use authenticated broker integration tests for both allowed Image replay and denied operations. Broad `allow_anonymous` fixtures alone do not prove ACL correctness.

**Complete when:** the new subscription works with the actual reader identity and no extra write privilege.

## Step 5 — Store Images in immutable projection snapshots

**Complete locally 2026-09-29:** see [Step 5 evidence](evidence/Step%205/README.md). After correcting the test-only Java generic-inference issue in `ProjectionServiceTest`, the focused projection/contract/HTTP tests, MQTT/Testcontainers integration tests, and full `:diaries-web:test :diaries-web:build` all passed on the normal Windows Java 25/Docker development machine.

**Files:** `MutableProjectionState.java`, `ProjectionSnapshot.java`, `ProjectionService.java`, `ProjectionStatus.java` and related status/health serialization.

1. Add the mutable Image map, upsert change detection and Image tombstone handling.
2. Copy Images into immutable snapshots and expose bounded lookup/count APIs needed by resolution and diagnostics.
3. Include Images in the existing reconnect lifecycle: empty staging state, retained replay, atomic ready swap. Never carry an old Image map into a fresh generation.
4. Preserve existing readiness/replay timeout semantics; count rejected payloads and subscription failures without silently presenting an incomplete new generation as ready.
5. Test duplicate delivery, changed metadata/version, Image-before-Fragment, Fragment-before-Image, tombstone-before-reference cleanup, reconnect without an old Image and immutable snapshot isolation.
6. Follow the projection's existing event/version policy; do not add an unrelated global stale-version algorithm during this change.

**Complete when:** Image metadata has the same lifecycle guarantees as the existing canonical entity maps.

## Step 6 — Resolve mixed Fragment types and add diagnostics

**Complete locally 2026-09-29:** see [Step 6 evidence](evidence/Step%206/README.md). Mixed MARQUEE/IMAGE/unknown resolution, degraded media states, per-generation invalid Image metadata tracking, shared Image references, relationship repair and type-specific diagnostics are implemented and verified. The focused Step 6 projection/contract/MQTT run and the full `:diaries-web:test :diaries-web:build` both passed on the normal Windows Java 25/Docker development machine.

**Files:** `ResolvedFragment.java`, `ProjectionSnapshot.java`, `RelationshipDiagnostics.java`, `ProjectionServiceTest.java`.

1. Extend `ResolvedFragment` with an optional Image and enough state to render degraded media deterministically.
2. Resolve Page and Diary exclusively through `Fragment.pageId` and `Page.diaryId`. Preserve current date/sequence/ID tie-break ordering and source-page ordering.
3. Apply the resolution policy table. Count actual Marquee links to IMAGE independently of `marqueeId`, including pointer-only inconsistencies.
4. Replace the blanket unsupported-IMAGE counter with meaningful counts. Preserve or deliberately deprecate existing status fields used by diagnostics consumers.
5. Distinguish at least: no Page ID, missing Page, Page without Diary, unknown type, MARQUEE without Marquee, MARQUEE with Image, IMAGE with Marquee, IMAGE without selection, and referenced Image metadata missing. Document names and avoid accidental double counting within each category.
6. Ensure two Fragments can resolve the same Image without duplicating it or deriving chronology from it. Image updates/tombstones affect media resolution for every reference while preserving all corresponding Fragment rows.
7. Add a full relationship matrix, mixed-day/month ordering tests and relationship repair after later retained messages.

**Complete when:** missing media and invalid type-specific links never remove otherwise valid Page-owned chronology or silently change Fragment type.

## Step 7 — Add runtime Files configuration and safe catalogue URLs

**Completed 2026-09-29:** see [Step 7 evidence](evidence/Step%207/README.md). The focused configuration/rendering/HTTP verification and full web test/build gate both passed on the normal Windows Java 25/Docker development machine.

**Files:** `AppConfig.java`, `ConfigLoader.java`, `ImageUrlBuilder.java`, web example/Docker JSON, `ConfigLoaderTest.java`, `RenderingSafetyTest.java`; deployment config documentation.

1. Add `content.filesPath` as the configured responder Files route, with documented backward-compatible default `files` when absent. Update Java constructor call sites and test fixtures.
2. Keep `publicResponderBaseUrl` as the browser-visible origin/base path; do not substitute internal Docker DNS or an internal responder URL.
3. Add one catalogue Image URL method to `ImageUrlBuilder`. Join the configured base/Files route and each normalized relative-path segment, preserving nested diary/subfolder paths.
4. Reject absolute paths, drive/UNC paths, URI schemes, backslash ambiguity, dot/dot-dot segments, control characters and unsafe empty segments. Validate path syntax before encoding. Do not decode stored percent sequences and then treat them as path structure.
5. Encode literal path segments exactly once: spaces as `%20`, plus as `%2B`, percent as `%25`, Unicode as UTF-8 escapes; preserve real `/` separators. Cover `#`, `?`, quotes, percent-like traversal strings and leading/trailing separator cases.
6. Validate configured browser bases as supported HTTP(S) or same-origin rooted paths, excluding protocol-relative/userinfo/unsafe schemes. Keep resulting image requests within the configured content route.
7. Review CSP generation for the configured origin; do not broaden it to arbitrary origins, inline scripts or unsafe URL schemes.
8. Preserve Page URL behavior and the legacy embedded-image resolver. Any use of the new Files setting by legacy URLs must preserve default output and get regression tests; no legacy conversion is included.
9. Compare development-infrastructure, local-docker-build, local-published-smoke, and shared/standalone frontend routing. New JSON properties must not be sent to an older strict config decoder before its compatible binary is installed.

**Complete when:** catalogue URLs depend only on validated runtime routing and Image.relativePath, with tested compatibility and escaping.

## Step 8 — Extend HTTP view models for typed media

**Complete locally 2026-09-29:** one shared typed-media view now feeds both month-reader and source-page models. It carries effective/raw Fragment type, type-safe `hasMarquee`, media state, catalogue URL, alt/caption/dimensions and stable unavailable text while keeping Page scan URL/dimensions distinct. Focused HTTP/model tests cover shared Images, missing/invalid metadata, no-selection IMAGE, unknown explicit type, invalid IMAGE→Marquee retained data, redirects and HEAD. The focused HTTP/config/rendering suite and full `:diaries-web:test :diaries-web:build` gate both passed on the normal Windows Java 25/Docker development machine. See [Step 8 evidence](evidence/Step%208/README.md).

**Files:** `WebServer.java`, `SiteUrls.java` only if necessary, HTTP tests and fixture builders.

1. Centralize the catalogue-media view model so month-reader and source-page responses use the same resolution policy and URL builder.
2. Supply explicit Fragment type, `hasMarquee`, optional media URL, alt text, caption, dimensions and unavailable-state text. Keep Page scan URL/dimensions distinct from catalogue Image URL/dimensions.
3. IMAGE always has `hasMarquee=false` for selection even when retained data contains an invalid Marquee link.
4. Continue sanitizing Fragment HTML with the existing sanitizer and legacy resolver. Escape caption/alt/path-derived strings normally; never mark them `raw`.
5. Preserve month/day/fragment redirects, deep-link IDs, ownership checks, GET/HEAD behavior, errors and HTTP readiness responses.
6. Test full-page and fragment-selected responses with shared Images, missing media, unknown type, malformed metadata and no-Marquee IMAGE rows.

**Complete when:** HTTP rendering supplies enough safe data for both templates without requiring database, filesystem or per-image HTTP lookups on the web server.

## Step 9 — Render accessible media in month and source-page views

**Files:** `month-reader.peb`, `source-page.peb`, optional shared media partial, `static/css/diaries.css`.

1. Retain the left-hand Page context; display IMAGE text plus a responsive `<figure>`/`<img>` and optional `<figcaption>` on the right.
2. Use Image.altText as the escaped `alt` attribute, including the documented empty value. Do not invent descriptions from filenames. Keep unavailable-state explanation separate from alternative text.
3. Constrain width and preserve aspect ratio (`height:auto` or equivalent). Use metadata dimensions for layout stability without stretching or cropping the content.
4. Give no-selection, missing metadata and unsupported type stable textual states. Avoid rendering an invalid/empty media `src` that would request the page itself.
5. Provide no-JavaScript content and clear link/alt fallback when media cannot load. Add browser-enhanced file-load failure handling in Step 10; server-rendered metadata alone cannot prove that bytes exist.
6. Preserve MARQUEE text/overlay markup and source-page navigation. Update selection wording that promises a transcription region when IMAGE has none.
7. Test escaped malicious caption/alt values, long captions, empty text, tall/wide/small images, mobile layout and reused Images. Do not create duplicate HTML IDs for reused media.

**Complete when:** both reader surfaces render readable, accessible mixed content, including degraded states.

## Step 10 — Make selection, history and media errors type-aware

**File:** `static/js/diaries.js`, with focused browser tests.

1. On MARQUEE → IMAGE selection, clear selected rectangle, mask/dimming, selected overlay classes and stale fit-to-selection state; retain Page context and unhighlighted other Marquees.
2. Disable or appropriately handle region-only controls. Use intentional IMAGE wording rather than reporting every valid IMAGE as a broken source region.
3. On IMAGE → MARQUEE, restore the selected region and normal zoom/focus behavior. Test same-Page and cross-Page transitions.
4. Preserve previous/next selection, keyboard Enter/Space, focus visibility, `aria-current`/`aria-pressed`, URL history, back/forward and direct deep-link selection for all Fragment types.
5. Keep catalogue media error/load state separate from source-scan error/load state. A source image `load` event must not clear an unrelated unavailable-media notice.
6. Handle 404, network error, invalid image bytes and late events after selection changes. Prevent fallback loops, stale updates and duplicate event handlers. Register handlers in the existing external JS, compatible with CSP.
7. Avoid nested interactive controls inside an existing role=button selector; any original-image link must remain independently keyboard accessible.
8. Preserve the read-only server-rendered model: MQTT updates become visible through a new HTTP snapshot/request; no browser MQTT/RPC or live-update subsystem is added here.

**Complete when:** selecting IMAGE never leaves a previous Marquee highlighted, and navigation remains usable when metadata or bytes are unavailable.

## Step 11 — Add focused projection, rendering and security coverage

**Implementation status (2026-09-29): complete locally.** The Step 11 patch is test/harness/evidence only; no production runtime source changes were required. The focused Java 25 suite and full `diaries-web` test/build gate passed, and browser verification confirmed both successful catalogue-media loading and the browser-only media-error branch used by the deterministic failure fixtures.

Extend existing suites rather than replacing their MARQUEE cases:

| Test area | Required cases |
| --- | --- |
| `RetainedContractTest` | Image metadata/tombstones/ID mismatch; additive fields; legacy null versus unknown explicit type |
| `ProjectionServiceTest` | Image map lifecycle; atomic reconnect swap; both message arrival orders; shared references; every resolution/diagnostic row above |
| `ConfigLoaderTest` / URL tests | Missing filesPath default; custom nested routes; public/internal base separation; percent/Unicode/hostile paths |
| `RenderingSafetyTest` | Sanitizer unchanged; caption/alt escaped; no persisted absolute URL; no untrusted `raw` media metadata |
| `WebServerTest` | Mixed chronology, redirects/deep links, both templates, GET/HEAD-only, unknown/missing media and CSP |
| Browser tests | Overlay clearing/restoration; history/focus/keyboard; responsive layout; media load errors and late events |

Use deterministic fixtures. Avoid arbitrary long sleeps; await observable projection generation, readiness, DOM or network conditions with bounded deadlines. A missing external prerequisite must be reported as skipped/blocked, never as a pass.

**Completion result (2026-09-29): complete locally.** Tests distinguish reference absence, missing metadata, rejected metadata, bad/missing bytes, invalid cross-type links and missing Page ownership. Browser evidence confirms the normal IMAGE path, keyboard/focus behavior, type-aware selection/history and the browser-only `FILE_LOAD_FAILED` presentation. Step 12 remains responsible for the real broker → decoder → projection → HTTP path.

## Step 12 — Verify real MQTT replay, permissions and HTTP projection

**Completion result (2026-09-29): complete locally.** A dedicated `Step12MqttHttpIntegrationTest` uses fresh owned Mosquitto containers, the committed `diaries-web` ACL, authenticated publisher/reader identities, the real `MqttProjectionClient`, `ProjectionService` and `WebServer`, plus a production-sized 5,376-topic retained tree. No production runtime source changed. The focused Java 25/Docker integration command was rerun under PowerShell 7.6.6 and completed successfully in 1m 16s with 7 actionable tasks executed; the complete `:diaries-web:test :diaries-web:build` gate completed successfully in 1m 35s with 15 actionable tasks executed. Exact PowerShell 7.6.6 console output is preserved under `evidence/Step 12/test-results.txt`. Step 13 is next.

**Files:** extend `MqttProjectionIntegrationTest.java`, test broker config/ACL and fixtures; add focused cases if the existing class becomes unwieldy.

1. Use a fresh owned broker, authenticated fixture publisher and read-only web identity. Publish known canonical Diary/Page/Fragment/Marquee/Image state.
2. Start the actual web projection/HTTP server and verify readiness plus mixed rendered output after retained replay, including late subscriber startup.
3. Exercise Image metadata update and tombstone, restoration, reversed arrival order and two Fragment references. Query HTTP again to verify the new immutable snapshot.
4. Disconnect/reconnect or restart web with changed retained state; verify no stale Image survives the fresh staging generation. Replay must complete before the new content generation is exposed.
5. Cover denied `images/+` subscription and forbidden writes/RPC with meaningful expected failure/readiness behavior; positive rendering tests alone do not verify ACLs.
6. Use a realistically sized retained tree including Images to catch replay queue/timeout problems. Follow actual broker settings and record counts/limits; do not simply hide a timeout by increasing sleeps or copying responder synchronization logic into web.
7. Capture RPC-free subscriber behavior, retained fixture payloads, projection counts/diagnostics, HTTP output, failures and cleanup.

**Complete when:** the real broker → decoder → immutable projection → HTTP path passes with reader permissions and fresh reconnect state.

## Step 13 — Run controlled cross-component development verification

**Completed locally (2026-09-30):** the controlled run is recorded at `evidence/Step 13/verified-run-20260930-192857/summary.json` with `status=PASSED`, zero cleanup failures and no live database/NAS modification. The disposable runner builds the exact current responder/web JARs, restores a supplied backup into owned PostgreSQL tmpfs, uses owned Mosquitto/responder/web services and a real browser, and records cleanup/evidence. It deliberately remains incomplete until that run succeeds on the Docker-enabled development workstation.

1. Build candidate web and use the tested 0025-capable responder in disposable development services. Apply required schema only to a restored disposable database before starting that responder.
2. Seed a small mixed fixture through supported responder operations: MARQUEE, IMAGE with selection, IMAGE without selection, two Fragments sharing one Image, different dates/Pages and nested file paths.
3. Enable Image authoring only in that isolated fixture. Verify normal MARQUEE behavior with the gate disabled first where practical.
4. Observe metadata via retained topics and bytes via actual configured HTTP routing; include browser-visible production-style path prefixes, not only direct container addresses.
5. Capture desktop/mobile month and source-page views, keyboard selection, deep links and browser-back behavior. Exercise unavailable metadata and a missing-file case using only owned fixture topics/files; never delete real NAS content.
6. Verify reference-aware DeleteImage conflict; remove fixture references, delete the fixture Image through its supported operation and confirm reader fallback/tombstones. Do not bypass the production guard to manufacture a failure in real data.
7. Restart responder/web and verify deterministic replay and chronology. Preserve database and retained fixture IDs/payloads, screenshots and HTTP/network results.
8. Clean up only fixture services/files/rows and record successful cleanup. Keep the live development database unchanged unless a separately authorized, backed-up validation explicitly requires it.

**Complete when:** real browser behavior is demonstrated against authoritative responder metadata and HTTP bytes, beyond unit/template assertions.

## Step 14 — Full regression and artifact verification

**Implementation status (2026-09-30): verification runner and negative controls implemented; final Java 25/Docker workstation run pending.** See [Step 14 verifier/commands](evidence/Step%2014/README.md). No full-suite or published-image acceptance is claimed until fresh machine evidence passes.

From the top-level `diaries` directory on Windows:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build --rerun-tasks --console=plain
.\gradlew.bat :diaries-web:test --tests "com.rsmaxwell.diaries.web.mqtt.MqttProjectionIntegrationTest" --rerun-tasks --console=plain
```

1. Run the full web suite/build and required real-MQTT cases with Docker available. Copy ordinary-suite reports before selected runs overwrite them. Explicitly report Testcontainers skips.
2. If responder source/contracts changed, rerun its full suite/build and relevant MQTT integrations. If client source changed, run its relevant tests and production build; neither should require a change merely to implement 0026.
3. Render affected Compose configurations and exercise local-docker-build and local-published-smoke as applicable. Confirm actual image IDs, tags, runtime configuration, broker subscriptions and health; avoid assuming local source equals a published image.
4. Check normal MARQUEE regression, missing-media behavior, URL escaping, sanitization, diagnostics, source-page/month navigation and reconnect readiness.
5. Generate fresh source/config SHA inventories, candidate JAR/image identity and exact command/results evidence. Re-run affected validation if production source changes after capture, as required for 0025's synchronization revision.
6. Preserve warnings/failures and their resolutions; no credentials or signed tokens in committed evidence.

**Complete when:** all required tests/builds, browser checks and real-MQTT cases pass against the exact release candidate; skipped work is not silently treated as acceptance.

## Step 15 — Deploy reader support with production authoring disabled

1. Verify actual production reader/responder/broker versions, 0025 schema readiness and `imageFragmentWritesEnabled` state. Confirm no unexpected IMAGE rows exist before relying on an old-reader rollback.
2. Prepare a concrete deployment change: explicit web image/tag, Files route configuration, reader-only Image ACL and compatible broker configuration. Record rollback artifacts/configuration and the deployment order before applying it.
3. Where Ansible lives outside this workspace, provide a reviewed change/handoff unless that repository is explicitly authorized and writable. Do not claim deployment based only on editing local examples or defaults.
4. Build/publish/deploy through the approved workflow when authorized. Keep the production Image authoring gate disabled; this step must not enable 0027 or run 0028 conversion.
5. Apply/reload the narrow broker ACL and deploy compatible reader configuration/binary together. Confirm generated configuration, running image/embedded version, subscription success, projection readiness and both shared/standalone frontend behavior applicable to the target.
6. Smoke-test existing production MARQUEE reads, navigation and HTTP image routes. Demonstrate mixed IMAGE behavior using the identical published artifact in controlled staging. A production IMAGE smoke fixture requires separate explicit authorization and cleanup evidence; it is not required to fabricate production data to prove reader readiness.
7. Record evidence that the published reader is ready for the later rollout, including tested Image route/ACL, artifact identity, controlled mixed fixture and gate state.
8. If IMAGE data already exists, do not roll back to a reader that hides it. Prefer a compatible forward fix or an explicitly planned compatible rollback; disabling authoring alone does not remove existing IMAGE rows.

**Complete when:** the actual production reader artifact and configuration are verified, or the step is explicitly recorded as pending an external deployment. Local build success alone cannot close this step.

## Step 16 — Close out the feature and hand off to 0027/0028

**Status: Complete — 2026-10-01.** Final acceptance, policy documentation, production release identity and 0027/0028 handoff are recorded in `evidence/Step 16/`. The feature directory is moved to `change-control/complete`.

1. Update feature README checklists and this plan with actual completion status, exact changed files, commands/test counts, skipped checks, source/artifact hashes and evidence links.
2. Record final unknown-type/degraded-media policies, Files configuration/defaults, URL validation, caption/alt semantics, diagnostic field compatibility and any deviations.
3. Update web README, configuration examples, architecture documentation where needed, broker ACL documentation and the narrow canonical-topic guardrail change. Correct stale four-family assumptions.
4. Map every acceptance criterion below to tests and observed deployment/browser evidence. Do not close with unverified production reader readiness; clearly separate implementation completion from deployment completion when waiting for an operator.
5. Only mark 0026 Complete and move it to `change-control/complete` when acceptance and deployment prerequisites are evidenced. Preserve failed attempts and baseline records; do not commit/push unless requested.
6. Hand off the verified reader version/configuration and remaining gate/deployment prerequisites to 0027 and 0028. Leave 0029's destructive cleanup and relationship migration separate.

**Complete when:** another implementer/operator can reproduce validation and determine exactly whether production authoring may proceed through its own approved rollout.

---

## Required test and evidence fixture matrix

- Existing MARQUEE with a valid Marquee; legacy null type; MARQUEE missing its Marquee.
- IMAGE with an Image, IMAGE with null/absent reference, referenced Image missing, metadata rejected, file 404 and invalid image bytes.
- Two IMAGE Fragments referring to one Image; metadata update/tombstone changes both presentations without duplicating the catalogue entry.
- MARQUEE carrying imageId; IMAGE carrying a real Marquee link or stale pointer; unknown explicit type.
- Page/Diary ownership missing and then repaired by later retained messages.
- Mixed same-date ordering and sequence ties, date/month boundaries, multiple Pages and deep-linked IMAGE selection.
- Empty/long caption, explicit alt text, blank alt text, hostile HTML-like metadata, empty Fragment text.
- Nested subdirectories, spaces, Unicode, literal plus/percent/hash/question characters; rejected traversal/absolute/URI paths.
- Default/custom Files route, same-origin/subpath/absolute public base, internal host isolation and CSP.
- Same-Page and cross-Page MARQUEE ↔ IMAGE selection, keyboard/focus/history, disabled region controls and late source/media load events.
- Fresh retained replay, disconnect/reconnect, tombstones, restored metadata, malformed updates, denied subscriptions and a large retained tree.

## Final acceptance checklist

- [x] Read-only web consumes all five canonical retained entity families with minimum ACLs.
- [x] Image metadata and tombstones participate in immutable snapshots and atomic reconnect replay.
- [x] Every otherwise valid Page-owned IMAGE remains in date/month/source-page chronology, including missing media.
- [x] Fragment.pageId remains the ownership authority; ordering is unchanged.
- [x] IMAGE shows Page context, text and optional referenced Image, with no selected Marquee.
- [x] MARQUEE rendering and legacy null-type compatibility remain intact.
- [x] Invalid cross-type relationships and unknown explicit types have distinct diagnostics and safe rendering.
- [x] Runtime configuration alone determines Files URLs; paths are validated and encoded safely.
- [x] Caption/alt text are escaped, aspect ratio is preserved, and unavailable media has accessible text.
- [x] Keyboard selection, focus, deep links and browser history work across both types.
- [x] Shared Images, updates, tombstones and late metadata affect every reference without catalogue duplication.
- [x] HTML sanitization, CSP and GET/HEAD-only behavior remain effective.
- [x] Full web tests/build, real MQTT/ACL integration and controlled browser deployment checks pass.
- [x] Exact published reader artifact/configuration is verified before any production authoring enablement.
- [x] Production gate/rollback state and 0027/0028 handoff are recorded; no unrelated legacy conversion or destructive cleanup occurred.
- [x] Change-control evidence contains reproducible commands, source/artifact identities and actual results.
