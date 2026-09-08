# 0026-FEAT - Render ImageFragments in diaries-web

## Type

Feature

## Status

To do

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

- [ ] Add Image model and retained decoder tests.
- [ ] Add IMAGE entity storage, replay and tombstone handling.
- [ ] Generalize `ResolvedFragment` and type-aware diagnostics.
- [ ] Prove all valid IMAGE fragments enter date/month indexes.
- [ ] Extend the web view model with Fragment type and optional Image.
- [ ] Add a single configured Image URL builder with path-normalization tests.
- [ ] Update templates and CSS for Image preview, caption, alt text and missing state.
- [ ] Make fragment-selection JavaScript tolerate fragments with no marquee.
- [ ] Add tests for reused Images and mixed MARQUEE/IMAGE chronology.
- [ ] Add tests for invalid cross-type retained data.
- [ ] Test retained replay and Image tombstones.
- [ ] Run diaries-web tests and build.
- [ ] Deploy and smoke-test this reader before enabling 0027 authoring.

## Acceptance Criteria

- [ ] IMAGE fragments appear in the correct date/sequence order.
- [ ] Selecting IMAGE displays its referenced Image and no selected marquee.
- [ ] MARQUEE behaviour remains unchanged.
- [ ] Missing Image metadata/file cannot remove a Fragment from chronology.
- [ ] Reused Images render for every referring Fragment without catalogue duplication.
- [ ] Runtime configuration determines URLs.
- [ ] Caption, alt text, focus and keyboard behaviour are accessible.
- [ ] Projection diagnostics identify invalid cross-type relationships.
- [ ] Tests/build pass and a controlled mixed-type fixture is demonstrated.

## Dependencies

Requires 0022–0025. This feature is a deployment prerequisite for enabling 0027 authoring and for executing the 0028 legacy conversion.

## Deployment and Rollback

Deploying reader support is additive and may occur while production contains only MARQUEE fragments. Rollback is safe only while no production IMAGE fragments exist. Once 0027 or 0028 creates IMAGE rows, rolling back to a reader that omits them is not an acceptable application state.

