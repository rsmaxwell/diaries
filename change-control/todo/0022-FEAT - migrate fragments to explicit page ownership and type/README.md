# 0022-FEAT - Migrate fragments to explicit page ownership and type

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-07

## Summary

Introduce the additive foundation of the new fragment model by making `Fragment` explicitly own its `Page` and by adding an explicit fragment `type`.

Backfill `Fragment.pageId` from the current Marquee relationship wherever that relationship is unambiguous. Do **not** blindly classify every existing Fragment as `MARQUEE`: some existing Fragments already contain supplementary images embedded in their fragment HTML/text and are therefore candidates for later migration to first-class `IMAGE` fragments.

This feature must therefore do two things:

1. establish explicit Page ownership and fragment typing infrastructure without breaking existing applications; and
2. inventory and report legacy image-bearing Fragments so that their final conversion can be performed deliberately after the reusable `Image` catalogue exists.

Preserve existing Marquee persistence, `Marquee.page_id`, embedded fragment HTML/text and existing MQTT fields during this feature so old clients and `diaries-web` remain compatible.

## Background

Today `Fragment` has no direct Page relationship. `Marquee` owns both `page_id` and unique `fragment_id`, and responder code commonly reaches a Page by walking through a Marquee:

```text
Fragment <- Marquee -> Page
```

This prevents a Fragment without a Marquee from being a first-class child of a Page, which in turn prevents the proposed `IMAGE` Fragment model from working cleanly.

The target ownership model is:

```text
Fragment -> Page
```

with an explicit Fragment type:

```text
Fragment.type = MARQUEE | IMAGE
```

Most existing Fragments are normal transcription Fragments associated with a Marquee and are natural `MARQUEE` candidates. However, the existing database also contains legacy image-style Fragments whose fragment text/HTML contains embedded image elements such as:

```html
<img src="/files/.../image.jpg" alt="...">
```

These rows are structurally still existing `Fragment + Marquee` records, but semantically some may represent the precursor of the new `IMAGE` Fragment concept.

Therefore the migration must distinguish between:

```text
A. ordinary legacy fragments
   Fragment + Marquee
   text contains no supplementary image reference
   => safe candidate for type=MARQUEE

B. legacy image-bearing fragments
   Fragment + Marquee
   text contains one or more embedded image references
   => requires explicit migration review

C. fragments without a usable Marquee/Page relationship
   => requires explicit investigation
```

Detection of embedded `<img>` elements is a **candidate detector only**. It must not automatically convert a Fragment to `IMAGE`, because an ordinary transcription Fragment may legitimately contain an inline illustration and still need to remain a `MARQUEE` Fragment.

This feature does not create the reusable `Image` catalogue and does not convert existing image-bearing Fragments into `IMAGE` Fragments. That work belongs in a later feature once `Image` entities exist.

## Goals

After this feature:

- `Fragment` has an authoritative `page`/`pageId` relationship;
- `Fragment` has an explicit `type` capable of representing at least `MARQUEE` and `IMAGE`;
- every legacy Fragment whose Page can be unambiguously inferred is backfilled with the correct `pageId`;
- clearly ordinary legacy transcription Fragments are classified as `MARQUEE`;
- legacy Fragments containing embedded image references are explicitly identified and reported for later migration review rather than silently treated as ordinary `MARQUEE` data;
- orphan/inconsistent Fragments are explicitly reported rather than guessed;
- responder retained Fragment payloads add `pageId` and `type` where a type has been assigned;
- existing `marqueeId` publication and `Marquee.page_id` remain temporarily for compatibility;
- existing `diaries-client` and `diaries-web` versions continue to function;
- no existing text/HTML, date, sequence, Marquee geometry or identity is lost.

## Non-goals

This feature does **not**:

- create the `Image` entity/table;
- create an Image catalogue;
- create `Fragment.imageId`;
- convert legacy embedded image HTML into `Image` entities;
- remove embedded `<img>` markup from Fragment text;
- remove `Marquee.page_id`;
- remove `marqueeId` from MQTT payloads;
- add ImageFragment creation/editing UI;
- change `diaries-web` rendering of legacy image-bearing Fragment HTML.

Those changes are deliberately deferred so that this migration remains additive and reversible.

## Expected Behaviour

### Ordinary legacy Fragment

Given an existing Fragment whose Marquee points to Page 85 and whose text contains no legacy supplementary image reference:

```text
Fragment id=84
Marquee.fragment_id=84
Marquee.page_id=85
```

this feature produces:

```text
Fragment id=84
page_id=85
type=MARQUEE
```

while leaving the Marquee and Fragment text unchanged.

### Legacy image-bearing Fragment

Given an existing Fragment whose Marquee points to Page 85 and whose text contains embedded image markup:

```html
<img src="/files/.../whitley-park.jpg" alt="Whitley Park">
```

this feature must:

- backfill `Fragment.page_id` from the existing Marquee;
- preserve the original Fragment text/HTML unchanged;
- preserve the existing Marquee unchanged;
- identify the Fragment in a migration report as a legacy image-bearing candidate;
- avoid automatically reinterpreting it as a first-class `IMAGE` Fragment in this feature.

Its final type handling must be deliberate. The recommended approach for this feature is to leave such rows temporarily unclassified (`type IS NULL`) until the later image migration decides whether each candidate becomes:

```text
MARQUEE
```

or:

```text
IMAGE + imageId -> Image
```

`type` remains nullable during this compatibility feature. 0028 supplies the reviewed classification input and 0029 applies the final non-null constraint.

### Fragment without inferable Page

If a Fragment has no Marquee, multiple inconsistent Marquee relationships, an invalid `Marquee.page_id`, or any other condition that prevents an unambiguous Page assignment, the migration must report it and must not guess a Page.

## Data Classification Rules

The migration preflight should classify every existing Fragment into one of the following categories.

### `ORDINARY_MARQUEE_CANDIDATE`

Criteria:

- exactly one usable Marquee relationship exists;
- the Marquee resolves to a valid Page;
- Fragment text contains no detected embedded image reference requiring review.

Action:

```text
fragment.page_id = marquee.page_id
fragment.type = MARQUEE
```

### `LEGACY_IMAGE_CANDIDATE`

Criteria:

- exactly one usable Marquee relationship exists;
- the Marquee resolves to a valid Page;
- Fragment text contains one or more embedded image references, for example an `<img>` element or another known legacy image form.

Action:

```text
fragment.page_id = marquee.page_id
fragment.type = NULL   (preferred during this feature)
```

and include the row in the migration inventory with enough information to review it later.

Detection must be conservative and report-oriented. It must not assume that every `<img>` means the Fragment should ultimately become `IMAGE`.

### `ORPHAN_OR_INCONSISTENT`

Examples:

- no Marquee exists;
- more than one Marquee exists for the same Fragment despite the intended uniqueness;
- `Marquee.page_id` is null;
- referenced Page does not exist;
- conflicting relationships make Page ownership ambiguous.

Action:

- report the row;
- do not assign a guessed Page;
- do not force a type;
- require explicit operator resolution before later constraints are tightened.

## Migration Inventory

The preflight must produce a reviewable inventory containing at least:

```text
fragment_id
page_id inferred from marquee
marquee_id
existing date fields
sequence
classification
embedded image count
embedded image src values where detectable
short text/HTML preview
reason for classification
```

The inventory should be written in a format that is easy to review and preserve with the change record, for example CSV plus SQL output.

The migration should also report summary counts:

```text
total fragments
ordinary marquee candidates
legacy image candidates
orphans/inconsistent rows
fragments with more than one detected image
unique embedded image paths
```

These counts become part of the migration evidence and must be checked again after backfill.

## Database Changes

Add initially nullable columns:

```text
fragment.page_id
fragment.type
```

Recommended SQL staging:

```text
sql/001-preflight.sql
sql/002-additive-schema.sql
sql/003-classify-and-inventory.sql
sql/004-backfill-page.sql
sql/005-backfill-safe-types.sql
sql/006-postflight.sql
sql/007-constrain-safe-columns.sql
```

### `001-preflight.sql`

Must report:

- total Fragment count;
- Fragment/Marquee/Page join integrity;
- Fragments without Marquees;
- duplicate Marquee-per-Fragment anomalies;
- invalid/null Page references;
- candidate embedded images in Fragment text;
- counts for every migration category.

### `002-additive-schema.sql`

Add nullable columns and foreign key infrastructure without making the migration irreversible:

```text
fragment.page_id
fragment.type
```

Add the Page foreign key in a way appropriate to PostgreSQL/JPA migration practice.

Do not make `page_id` or `type` `NOT NULL` in 0022. Final constraints belong to 0029 after the reviewed 0028 conversion and after rollback no longer depends on an old responder which does not populate these columns.

### `003-classify-and-inventory.sql`

Create/report the migration classification described above.

The classification logic must be transparent and reviewable. If pattern matching is used to find `<img>` elements, document the exact expression and its limitations.

### `004-backfill-page.sql`

For every Fragment with one valid legacy Marquee/Page relationship:

```text
fragment.page_id = marquee.page_id
```

This applies to both ordinary Marquee candidates and legacy image candidates.

### `005-backfill-safe-types.sql`

Set:

```text
type = MARQUEE
```

only for rows classified as safe ordinary Marquee candidates.

Do not automatically set legacy image candidates to `MARQUEE` merely because they currently have a Marquee.

### `006-postflight.sql`

Verify:

- Fragment row count unchanged;
- IDs unchanged;
- dates unchanged;
- sequence unchanged;
- text/HTML unchanged;
- locks unchanged;
- Marquee IDs and geometry unchanged;
- every backfilled `page_id` matches the legacy `marquee.page_id` used as its source;
- safe ordinary candidates have `type=MARQUEE`;
- legacy image candidates remain present and identifiable;
- no previously detected orphan/inconsistency silently disappeared.

### `007-constrain-safe-columns.sql`

Apply only constraints that are safe at this stage.

It is acceptable for `fragment.type` to remain nullable temporarily if unresolved legacy image candidates still need later classification.

Do not make `fragment.page_id` or `fragment.type` `NOT NULL` in this feature. An older responder does not populate either column, so early constraints would make the documented application rollback unsafe and could reject writes during a mixed-version deployment. Constraint enforcement belongs to 0029 after every candidate has been resolved and rollback no longer depends on the old responder.

## Diaries Responder Changes

Update the relevant responder model, DTO and replay code, including the current equivalents of:

```text
model/Fragment.java
dto/FragmentDBDTO.java
dto/FragmentPublishDTO.java
utilities/DiaryContext.java
repositories and repository implementations as necessary
```

### Fragment type

Introduce:

```java
public enum FragmentType {
    MARQUEE,
    IMAGE
}
```

Even though this feature creates no new first-class IMAGE rows, the enum establishes the target contract.

`Fragment.type` must tolerate the temporary migration state if legacy image candidates remain unclassified. Do not fabricate `MARQUEE` merely to avoid nullable handling.

### Explicit Page ownership

Make `Fragment` own a `Page` relationship corresponding to `fragment.page_id`.

During this compatibility feature, retain `Marquee.page` / `marquee.page_id` unchanged.

For newly-created normal fragments, both relationships must agree:

```text
Fragment.page = requested Page
Marquee.page  = requested Page
```

The Fragment Page becomes the target authoritative relationship; the Marquee Page remains temporarily for compatibility until a later feature removes the legacy coupling.

### Existing AddFragment behaviour

The existing `AddFragment` operation continues to create the current Marquee-based Fragment and must explicitly set:

```text
fragment.page = requested Page
fragment.type = MARQUEE
```

before persisting the Fragment and Marquee in the existing transaction.

No ImageFragment creation is introduced here.

### Database replay / DiaryContext

Refactor database replay so Fragment publication is based on Fragment rows and their explicit Page relationship rather than assuming that every publishable Fragment can be discovered only by Page -> Marquee traversal.

However, this feature must remain compatible with temporarily unclassified legacy image candidates.

For those rows, choose one explicit compatibility behaviour and document it. The safest approach is:

- continue publishing their existing payload and embedded text exactly as before;
- include `pageId`;
- omit `type` or publish an explicit temporary compatibility value only if the MQTT DTO contract supports that safely;
- do not invent `IMAGE` until the later migration has created an `Image` entity and `imageId`.

The detailed implementation must choose a representation that preserves existing client/web behaviour during the staged rollout.

## MQTT Contract

Do not remove or rename existing topics.

Extend retained Fragment payloads additively with explicit Page ownership and type information where available.

Target shape for a migrated ordinary Fragment:

```json
{
  "id": 84,
  "pageId": 85,
  "type": "MARQUEE",
  "year": 1828,
  "month": 3,
  "day": 20,
  "sequence": 2,
  "text": "...",
  "marqueeId": 123
}
```

Legacy image candidates must continue to retain their current fragment text/HTML. This feature must not rewrite those payloads into first-class ImageFragments.

If `type` remains temporarily nullable for such candidates, MQTT serialization and both consumers must handle that migration state safely until the later conversion feature completes.

Date-index topics must preserve their existing behaviour and ordering.

## Diaries Client / Diaries Web

No new ImageFragment UI or rendering behaviour is required in this feature.

Existing versions must continue to render all legacy fragments exactly as before, including fragments whose text contains embedded `<img>` markup.

Additive JSON properties must not break existing clients.

If this feature introduces nullable/absent `type` for legacy image candidates, the currently deployed client and web applications must continue treating those rows using legacy behaviour until later features migrate them.

## Detailed Implementation Steps

- [ ] Back up a representative production-like database and restore it into a disposable migration-test environment.
- [ ] Record baseline Fragment, Marquee and Page row counts.
- [ ] Write preflight SQL for Fragment/Marquee/Page integrity anomalies.
- [ ] Add conservative detection of legacy embedded image references in Fragment text/HTML.
- [ ] Produce a migration inventory separating ordinary Marquee candidates, legacy image candidates and orphan/inconsistent rows.
- [ ] Review the inventory manually before modifying production data.
- [ ] Add `FragmentType` with at least `MARQUEE` and `IMAGE`.
- [ ] Add nullable `fragment.page_id` and `fragment.type` mappings.
- [ ] Write explicit SQL migration rather than depending on schema auto-generation.
- [ ] Backfill `fragment.page_id` from the exact current `marquee.page_id` wherever the relationship is unambiguous.
- [ ] Set `type=MARQUEE` only for safe ordinary legacy candidates.
- [ ] Leave legacy image candidates explicitly identifiable for later migration; do not silently classify them as ordinary Marquee fragments.
- [ ] Resolve or report fragments without an inferable Page; never guess.
- [ ] Add postflight row-count, data-preservation and join-integrity queries.
- [ ] Update `FragmentDBDTO` and entity inflate/save paths.
- [ ] Update `AddFragment` to persist Page + `MARQUEE` type on newly-created normal fragments.
- [ ] Add `pageId` and `type` support to `FragmentPublishDTO` without removing `marqueeId`.
- [ ] Refactor database replay so Fragment publication no longer depends exclusively on Marquee traversal.
- [ ] Preserve legacy embedded image HTML/text unchanged.
- [ ] Extend retained-state contract tests for ordinary typed Fragments and migration-state legacy image candidates.
- [ ] Add migration integration test or scripted verification against a legacy-schema fixture that includes at least one embedded-image Fragment.
- [ ] Confirm existing `diaries-client` and `diaries-web` builds still render the migrated database correctly.
- [ ] Preserve the migration inventory with the change-control record as a required input to 0028.

## Acceptance Criteria

### Data preservation

- [ ] Existing Fragment IDs are unchanged.
- [ ] Existing Fragment date fields are unchanged.
- [ ] Existing Fragment sequences are unchanged.
- [ ] Existing Fragment text/HTML is byte-for-byte or semantically unchanged according to the chosen DB migration method.
- [ ] Existing Fragment locks are unchanged.
- [ ] Existing Marquee IDs are unchanged.
- [ ] Existing Marquee geometry is unchanged.
- [ ] Existing `Marquee.page_id` values are unchanged.

### Explicit Page ownership

- [ ] Every Fragment with one valid legacy Marquee/Page relationship has the same Page copied to `Fragment.page_id`.
- [ ] No Fragment is silently assigned to a Page that cannot be inferred unambiguously.
- [ ] Any unresolved orphan/inconsistent row appears in the migration report.

### Type migration

- [ ] Clearly ordinary legacy transcription/Marquee Fragments are assigned `type=MARQUEE`.
- [ ] Existing image-bearing Fragments are inventoried separately and are not blindly converted to `MARQUEE` merely because they currently have a Marquee.
- [ ] No existing Fragment is automatically converted to first-class `IMAGE` in this feature.
- [ ] The inventory records enough information to support a later deliberate conversion of legacy image candidates.

### New data

- [ ] Newly-created normal Fragments have explicit `pageId` and `type=MARQUEE`.
- [ ] Newly-created Fragment and Marquee Page relationships agree.

### MQTT / compatibility

- [ ] Ordinary migrated retained Fragment JSON includes `pageId`, `type=MARQUEE` and the legacy `marqueeId`.
- [ ] Legacy image-bearing Fragment text/HTML continues to be published unchanged.
- [ ] Existing retained topic names are unchanged.
- [ ] Existing `diaries-client` and `diaries-web` builds continue to function against the updated responder.
- [ ] Existing image-bearing legacy Fragments continue to render as they did before this migration.

### Testing

- [ ] Migration tests include an ordinary Marquee Fragment.
- [ ] Migration tests include a Fragment containing embedded `<img>` markup.
- [ ] Migration tests include an orphan/no-Marquee case.
- [ ] Responder unit/integration tests pass.
- [ ] Preflight and postflight counts reconcile.

## Dependencies

None. This remains the foundation for the later ImageFragment work.

0024 uses this feature's embedded-image paths while reconciling the Image catalogue. 0028 must consume the complete reviewed candidate inventory and record a disposition for every candidate. 0029 must not impose final constraints while any candidate or Page-ownership anomaly remains unresolved.

## Deployment Sequence

1. Take a verified database backup.
2. Run `001-preflight.sql` and preserve its output.
3. Generate and review the legacy image candidate inventory.
4. Resolve any Page ownership anomalies that can be safely resolved before migration.
5. Apply additive schema changes.
6. Backfill explicit Page ownership.
7. Backfill only safe `MARQUEE` classifications.
8. Run postflight verification and compare counts with preflight.
9. Deploy the responder compatibility build.
10. Republish/replay retained state as required by the normal Diaries deployment process.
11. Verify the current `diaries-client` and `diaries-web` against representative ordinary and legacy image-bearing Fragments.
12. Preserve the reviewed migration inventory as a required input to 0028.

## Rollback

This feature is intentionally additive.

Before migration, take a database backup. If application rollback is required, old binaries should be able to ignore the newly-added columns because legacy `Marquee.page_id`, Fragment text/HTML and existing MQTT fields remain intact.

If the data migration itself is suspect, restoring the pre-migration database backup is the safest rollback.

Do not drop `marquee.page_id` in this feature.
Do not remove `marqueeId` from retained Fragment payloads in this feature.
Do not rewrite or remove legacy embedded image HTML in this feature.

## Follow-on Work

0028 must consume the legacy image candidate inventory and, after the reusable `Image` catalogue and both applications support IMAGE Fragments, deliberately decide which candidates are converted, split, preserved as legacy compatibility cases, or deferred.

For a confirmed legacy image candidate, that later work may perform a transformation conceptually like:

```text
Before
------
Fragment
  pageId = 85
  type = temporary/unclassified
  text = '<img src="/files/.../whitley-park.jpg" ...>'

Marquee
  fragmentId = Fragment.id
  pageId = 85

After
-----
Image
  relativePath = '.../whitley-park.jpg'
  ...metadata...

Fragment
  same id
  same pageId
  type = IMAGE
  same date
  same sequence
  imageId = Image.id
  text = retained meaningful non-image text/caption as deliberately defined

Marquee
  removed from this Fragment if the approved target model requires IMAGE fragments to have no Marquee
```

That transformation is explicitly outside 0022.
