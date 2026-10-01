# 0026 Step 6 — Resolve mixed Fragment types and add diagnostics

**Complete locally — 2026-09-29.** Mixed Fragment resolution and relationship diagnostics have been verified on the normal Windows Java 25/Docker development machine. The focused Step 6 projection/contract/MQTT suite passed, followed by a successful full `:diaries-web:test :diaries-web:build` run.

## Implemented behaviour

Step 6 generalises `ResolvedFragment` to carry optional Marquee and Image media plus the reader-contract media state:

- `NOT_APPLICABLE`
- `NO_SELECTION`
- `AVAILABLE`
- `MISSING_METADATA`
- `INVALID_METADATA`
- `UNSUPPORTED_TYPE`

Fragment chronology and ownership remain exclusively `Fragment.pageId -> Page.diaryId`. Images and Marquees never establish ownership or chronology.

Resolution follows the 0026 policy:

- MARQUEE and legacy-null types retain Marquee behaviour and never resolve catalogue Images.
- MARQUEE with `imageId` remains MARQUEE and is diagnosed by `marqueeFragmentsWithImage`.
- IMAGE with a valid referenced Image resolves the shared `ImageItem` and never exposes a selected Marquee.
- IMAGE without `imageId` resolves as `NO_SELECTION`.
- IMAGE whose referenced Image is absent resolves as `MISSING_METADATA`.
- IMAGE whose current-generation retained Image payload was rejected resolves as `INVALID_METADATA` when no valid Image is active.
- A malformed live replacement does not displace an already-valid Image, so resolution remains `AVAILABLE` while invalid-message diagnostics increase.
- Unknown explicit Fragment types remain valid Page-owned chronology rows with `UNSUPPORTED_TYPE`; they are never coerced to MARQUEE or IMAGE.

The projection records the Step 6 diagnostics while preserving the existing Page/Marquee counters:

- `fragmentsWithoutPage`
- `fragmentsWithUnknownType`
- `marqueeFragmentsWithImage`
- `imageFragmentsWithMarquee`
- `imageFragmentsWithoutImage`
- `imagesReferencedButMissing`
- `imagesReferencedButInvalid`

`unsupportedImageFragments` remains present for compatibility but is deliberately zero because IMAGE is now a supported projection type. Actual retained Marquee links to IMAGE are detected independently of the compatibility `Fragment.marqueeId`, and stale/missing compatibility pointers remain diagnosed separately.

Two or more IMAGE Fragments may reference the same catalogue Image. Image update/tombstone events rebuild all affected media resolutions while preserving the Page-owned Fragment rows and their chronology.

## Validation performed

The authoritative user console output is preserved verbatim in `test-results.txt`. It was captured after the Step 6 implementation package was applied.

Focused Step 6 verification:

```powershell
.\gradlew.bat :diaries-web:test `
  --tests "*ProjectionServiceTest" `
  --tests "*ImageReaderContractDefinitionTest" `
  --tests "*MqttProjectionIntegrationTest" `
  --tests "*MqttReaderAclIntegrationTest" `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 46s**, 7 actionable tasks, all executed.

Full web regression/build gate:

```powershell
.\gradlew.bat :diaries-web:test :diaries-web:build `
  --rerun-tasks --console=plain
```

Result: **BUILD SUCCESSFUL in 49s**, 15 actionable tasks, all executed.

The compiler emitted deprecated-API notes for the pre-existing `ConfigLoader.java` usage and for Step 6 test compatibility access in `ProjectionServiceTest`; neither is a test/build failure. The supplied Gradle console does not print an aggregate JUnit test count, so this record does not infer one.

## Completion decision

Step 6 is complete locally because:

- valid Page-owned IMAGE rows remain in chronology regardless of selection/media availability;
- MARQUEE, IMAGE, legacy-null and unknown explicit Fragment types are resolved without silent type coercion;
- degraded media states distinguish no selection, missing metadata, rejected current-generation metadata and unsupported types;
- cross-type Marquee/Image inconsistencies are diagnosed without changing ownership;
- shared Images, metadata updates, tombstones and later relationship repair preserve Fragment rows and ordering;
- the focused projection/contract/MQTT verification passes with Docker-backed integration tests;
- the complete `diaries-web` test/build gate passes after the final Step 6 source.

## Step boundary

Step 6 deliberately does **not** build browser-visible catalogue URLs, extend HTTP view models, render IMAGE media in templates, or change selection JavaScript. Those are Steps 7–10. No production deployment or ImageFragment authoring is enabled by this completion.

**Next:** Step 7 — Add runtime Files configuration and safe catalogue URLs.
