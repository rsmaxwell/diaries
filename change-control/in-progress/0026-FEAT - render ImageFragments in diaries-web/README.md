# 0026-FEAT - Render ImageFragments in diaries-web

## Type

Feature

## Status

In progress — Steps 1–12 complete locally; Step 13 verification tooling is implemented and awaiting its controlled workstation run; Steps 14–16 pending.

## Priority

High

## Opened

2026-09-08

## Summary

Teach `diaries-web` to consume retained Image entities and render IMAGE fragments alongside MARQUEE fragments in date/sequence order. This reader capability must be deployed and verified before `diaries-client` enables IMAGE authoring.

## Preconditions

- 0022 has added Fragment Page ownership and type.
- 0023 has made the web projection use `Fragment.pageId` rather than Marquee for chronology.
- 0024 has introduced retained Image entities and protected catalogued files.
- 0025 has introduced `Fragment.imageId` and IMAGE persistence/RPC semantics.

The production database need not contain an authored IMAGE Fragment yet. Tests and a controlled fixture provide the first IMAGE data.

## Expected Behaviour

For MARQUEE:

```text
LHS: source Page image with selected marquee
RHS: fragment text
```

For IMAGE:

```text
LHS: Page context without a marquee
RHS: fragment text plus referenced Image
```

An IMAGE fragment with null/missing Image state remains in chronology and displays a stable unavailable-media state. It is never discarded merely because its Image metadata or file is unavailable.

## MQTT and Model Changes

Add `IMAGE` to the retained entity model:

```text
EntityType.IMAGE("images")
ImageItem
Image retained decoder
mutable projection image map
image tombstone handling
```

Validate required identity/version/path metadata without constructing an absolute deployment URL. Unknown additive fields remain tolerated.

## Projection Rules

Generalize `ResolvedFragment` to contain:

```text
fragment
page
diary
optional marquee
optional image
```

Resolution rules are:

```text
MARQUEE -> page required; imageId must be null; matching Marquee optional for degraded rendering
IMAGE   -> page required; no matching Marquee; referenced Image optional for degraded rendering
```

Invalid type-specific relationships produce diagnostics rather than silently changing type. Every valid Page-owned Fragment remains in day/month indexes.

Diagnostics must distinguish at least:

```text
fragmentsWithoutPage
fragmentsWithUnknownType
marqueeFragmentsWithoutMarquee
marqueeFragmentsWithImage
imageFragmentsWithMarquee
imageFragmentsWithoutImage
imagesReferencedButMissing
```

## Rendering and Accessibility

- derive the Image URL from runtime Files configuration plus normalized `relativePath`;
- never trust a persisted absolute URL;
- render `altText` as the image `alt` value;
- render caption separately when present;
- constrain responsive dimensions without distorting aspect ratio;
- give unavailable media a textual explanation;
- keep fragment HTML sanitization unchanged except for changes explicitly required by the legacy migration in 0028;
- ensure keyboard selection and focus updates work when no marquee exists.

## Selection Behaviour

Selecting a MARQUEE fragment continues to select its overlay. Selecting an IMAGE fragment must:

- clear any previously selected marquee overlay;
- leave other marquees unhighlighted;
- update fragment text and Image presentation;
- update URL/deep-link state consistently;
- avoid errors when `imageId`, retained metadata or the file is missing.

## Detailed Implementation Steps

See [IMPLEMENTATION-STEPS.md](IMPLEMENTATION-STEPS.md) for the ordered implementation plan, current-source baseline, validation requirements, deployment sequence and close-out criteria.

- [x] Step 1 — freeze the web baseline and establish evidence ([record](evidence/Step%201/README.md), 2026-09-28). All 50 existing web tests passed, including both Docker-backed integration tests; build passed and synthetic MARQUEE browser behavior was recorded, including the existing source-page selection/history limitation. No application source or production state changed.

- [x] Step 2 — define the Image reader contract and degraded states ([record](evidence/Step%202/README.md), [contract](IMAGE-READER-CONTRACT.md)).
- [x] Step 3 — add canonical Image model, decoding and events ([record](evidence/Step%203/README.md), 2026-09-28). The recorded full web run passed all 94 tests with zero failures, errors or skips; the build passed and all 13 source hashes matched at Step-3 close-out.
- [x] Step 4 — extend reader subscriptions and minimum broker permissions ([record](evidence/Step%204/README.md), 2026-09-28). Actual `diaries-web` identity and committed ACL verified; all 107 web tests passed without skips, full build and all three Compose configs passed. Production ACL reload/delivery verification remains release work.
- [x] Step 5 — store Images in immutable projection snapshots ([record](evidence/Step%205/README.md), 2026-09-29). Image lifecycle/replay/tombstone storage and immutable snapshot access verified; focused projection/contract/HTTP tests passed, MQTT/Testcontainers integration tests passed, and the full web test/build completed successfully.
- [x] Step 6 — resolve mixed Fragment types and add diagnostics ([record](evidence/Step%206/README.md), 2026-09-29). Mixed MARQUEE/IMAGE/unknown resolution, degraded media states, shared Image references, relationship repair and type-specific diagnostics verified; focused projection/contract/MQTT tests and the full web test/build passed.
- [x] Step 7 — add runtime Files configuration and safe catalogue URLs ([record](evidence/Step%207/README.md), 2026-09-29). Backward-compatible `filesPath`, safe public-base validation, exactly-once catalogue path encoding, Page URL regression protection and legacy Files-route compatibility were verified; the focused configuration/rendering/HTTP tests and full web test/build passed.
- [x] Step 8 — extend HTTP view models for typed media ([record](evidence/Step%208/README.md), 2026-09-29). Shared month/source typed-media fields, type-safe Marquee handling, catalogue-media state, controlled mixed-media fixtures and HTTP regressions were verified; the focused HTTP/config/rendering tests and full web test/build passed.
- [x] Step 9 — render accessible media in month and source-page views ([record](evidence/Step%209/README.md), 2026-09-29). Both reader surfaces render available catalogue Images with escaped alt/caption metadata, intrinsic responsive dimensions, stable degraded-state text and a direct-image fallback link; focused rendering/safety verification and the full web test/build gate passed.
- [x] Step 10 — make selection, history and media errors type-aware ([record](evidence/Step%2010/README.md), 2026-09-29). Type-aware month/source selection, URL history and browser-only `FILE_LOAD_FAILED` handling were verified; IMAGE selection clears stale MARQUEE state while Page zoom controls remain available, MARQUEE selection restores region controls, and Back/Forward restores the correct selection.
- [x] Step 11 — add focused projection, rendering and security coverage ([record](evidence/Step%2011/README.md), 2026-09-29). Focused retained-contract/projection/config/rendering/HTTP security coverage passed, the full web test/build gate passed, and browser verification confirmed the successful catalogue-media path, keyboard/focus behavior and the existing browser-only file-failure path. No production runtime source changed.
- [x] Step 12 — verify real MQTT replay, permissions and HTTP projection ([record](evidence/Step%2012/README.md), 2026-09-29). Fresh-broker/Testcontainers coverage verified late retained replay, live Image lifecycle, reversed arrival, reconnect staging, ACL degradation/no-write/no-RPC behavior, HTTP projection and a production-sized 5,376-topic replay; the focused Java 25/Docker run and full web test/build gate both completed successfully under PowerShell 7.6.6.
- [ ] Step 13 — run controlled cross-component development verification ([implementation/evidence plan](evidence/Step%2013/README.md), 2026-09-29). The disposable restored-database/Mosquitto/responder/web/browser runner is implemented, including strict distinct-Page/date shared-Image coverage and cache-independent missing-file verification. Step 13 remains open until the runner passes on the Docker-enabled development workstation and its evidence is reviewed.

- [x] Add Image model and retained decoder tests.
- [x] Add IMAGE entity storage, replay and tombstone handling.
- [x] Generalize `ResolvedFragment` and type-aware diagnostics.
- [x] Prove all valid IMAGE fragments enter date/month indexes.
- [x] Extend the web view model with Fragment type and optional Image.
- [x] Add a single configured Image URL builder with path-normalization tests.
- [x] Update templates and CSS for Image preview, caption, alt text and missing state.
- [x] Make fragment-selection JavaScript tolerate fragments with no marquee.
- [x] Add tests for reused Images and mixed MARQUEE/IMAGE chronology.
- [x] Add tests for invalid cross-type retained data.
- [x] Test retained replay and Image tombstones.
- [ ] Run final diaries-web tests and build after the remaining implementation (Steps 4 and 5 tests/build already passed).
- [ ] Deploy and smoke-test this reader before enabling 0027 authoring.

## Acceptance Criteria

- [ ] IMAGE fragments appear in the correct date/sequence order.
- [ ] Selecting IMAGE displays its referenced Image and no selected marquee.
- [ ] MARQUEE behaviour remains unchanged.
- [ ] Missing Image metadata/file cannot remove a Fragment from chronology.
- [ ] Reused Images render for every referring Fragment without catalogue duplication.
- [x] Runtime configuration determines URLs.
- [ ] Caption, alt text, focus and keyboard behaviour are accessible.
- [x] Projection diagnostics identify invalid cross-type relationships.
- [ ] Tests/build pass and a controlled mixed-type fixture is demonstrated.

## Dependencies

Requires 0022–0025. This feature is a deployment prerequisite for enabling 0027 authoring and for executing the 0028 legacy conversion.

## Deployment and Rollback

Deploying reader support is additive and may occur while production contains only MARQUEE fragments. Rollback is safe only while no production IMAGE fragments exist. Once 0027 or 0028 creates IMAGE rows, rolling back to a reader that omits them is not an acceptable application state.
