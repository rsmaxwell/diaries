# 0026 Step 3 — canonical Image model, decoding and events

**Complete — 2026-09-28.** The subsequent Windows verification recorded in [test-output.txt](test-output.txt) passed both the focused tests and the full web suite/build. The full suite ran **94 tests with zero failures, errors or skips**, including both Docker-backed MQTT integration tests. All 13 entries in [source-sha256.csv](source-sha256.csv) matched the working tree at Step-3 close-out; see [source-verification.json](source-verification.json). Later steps intentionally change some of these files; this inventory preserves the Step-3 state.

## Scope implemented

This source set implements **Step 3 — Add canonical Image model, decoding and events** against the completed Step-2 Image reader contract.

Implemented changes:

- add immutable `ImageItem` metadata matching the responder `Image` / `ImagePublishDTO` retained contract;
- validate positive Image identity/dimensions, non-negative version, canonical NFC relative paths, supported MIME types, filename-only `originalFilename`, lowercase SHA-256 checksum, and non-null caption/alt text;
- preserve the Step-2 compatibility rule that absent caption/altText decode as `""`, while explicit JSON `null` is rejected;
- add `EntityType.IMAGE("images")` and canonical Image topic parsing/filter generation;
- decode retained Image upserts and zero-byte Image tombstones, including topic/payload ID equality and unknown additive fields;
- add `ProjectionEvent.UpsertImage`;
- add `FragmentType.UNKNOWN` plus exact `FragmentItem.rawType` preservation for future explicit string types;
- keep absent/null Fragment type as legacy MARQUEE semantics and reject non-string/non-null type tokens;
- preserve otherwise valid Page-owned UNKNOWN fragments in existing chronology;
- extend retained-contract/model tests for valid/invalid Image metadata, hostile paths, malformed JSON, tombstones, future fields, unknown Fragment types, and optional text behavior.

## Deliberate step boundaries

Step 3 does **not** activate the live `images/+` MQTT subscription. `TopicParser.canonicalFilter(EntityType.IMAGE)` is available and Image topics are parseable/decodable, but `canonicalFilters()` remains the four currently authorized reader subscriptions until Step 4 adds the Image ACL and subscription together.

Step 3 also does **not** add Image projection storage. `MutableProjectionState` has exhaustive compile-time handling for `UpsertImage` and IMAGE tombstones but intentionally leaves them as no-ops. Step 5 owns the mutable Image map, immutable snapshot lifecycle, and tombstone application.

No Files URL, HTTP rendering, browser behavior, database migration, responder mutation, or Image authoring behavior is introduced here.

## Verification completed on the Windows Java 25 development environment

The recorded focused verification ran from the top-level `diaries` directory:

```powershell
.\gradlew.bat :diaries-web:test `
    --tests "com.rsmaxwell.diaries.web.model.ImageItemTest" `
    --tests "com.rsmaxwell.diaries.web.mqtt.RetainedContractTest" `
    --tests "com.rsmaxwell.diaries.web.mqtt.ImageReaderContractDefinitionTest" `
    --tests "com.rsmaxwell.diaries.web.projection.ProjectionServiceTest" `
    --rerun-tasks `
    --console=plain
```

The ordinary web suite/build also completed successfully:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
    --rerun-tasks `
    --console=plain
```

The existing [test-output.txt](test-output.txt) records successful focused runs (7 seconds) and full test/build runs (22 seconds). The latest full-run XML reports, generated on 2026-09-28 at 14:56 local time, are preserved under [test-reports/](test-reports/); [test-summary.csv](test-summary.csv) records the counts below. These reports were copied from the existing successful run during documentation close-out; tests were not rerun for this documentation-only correction.

| Suite | Tests | Failures / errors / skips |
| --- | ---: | --- |
| ConfigLoaderTest | 2 | 0 / 0 / 0 |
| WebServerTest | 6 | 0 / 0 / 0 |
| ImageItemTest | 3 | 0 / 0 / 0 |
| PageItemTest | 12 | 0 / 0 / 0 |
| RectangleItemTest | 2 | 0 / 0 / 0 |
| ImageReaderContractDefinitionTest | 3 | 0 / 0 / 0 |
| MqttProjectionIntegrationTest | 2 | 0 / 0 / 0 |
| RetainedContractTest | 48 | 0 / 0 / 0 |
| ProjectionServiceTest | 12 | 0 / 0 / 0 |
| RenderingSafetyTest | 4 | 0 / 0 / 0 |
| **Total** | **94** | **0 / 0 / 0** |

The existing ConfigLoader deprecated-API compiler note did not fail verification. This closes Step 3 only: Image subscriptions/ACLs, storage, rendering and production verification remain later steps.

## Historical packaging-environment limitation

The changed production Java sources were syntax-compiled with Java 21 using minimal Jackson API stubs; this verifies Java syntax/exhaustive switches but is **not** a substitute for the real Java 25 Gradle tests above.

The packaging environment could not run the Gradle wrapper because its Gradle 9.6.1 distribution was not cached and outbound access to `services.gradle.org` was unavailable. That packaging attempt did not establish a Gradle pass; the later successful Windows runs above resolve this verification gap. The limitation is retained as historical context, not a pending completion requirement.
