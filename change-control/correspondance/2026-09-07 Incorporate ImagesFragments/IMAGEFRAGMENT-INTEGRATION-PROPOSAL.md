# Diaries ImageFragment Integration Proposal

## Purpose

This document proposes a staged implementation of first-class `ImageFragment` support across the Diaries system. It is based on the agreed conceptual model and on a review of the current Diaries source bundle dated 2026-09-07.

The objective is to let an uploaded image participate in the diary chronology as a normal fragment without introducing a second attachment sequence. Existing fragments remain marquee-based and are migrated into the same typed fragment model.

The proposal covers:

- PostgreSQL/JPA data-model evolution;
- migration of all existing fragment/page/marquee data;
- reusable uploaded `Image` entities;
- responder RPC and retained MQTT contracts;
- `diaries-client` editing and image selection;
- `diaries-web` chronological rendering;
- image lifecycle, validation, deletion and reconciliation;
- staged compatibility and rollback;
- final removal of redundant legacy relationships.

## Architectural Principles

The existing Diaries principles remain unchanged:

```text
RPC requests express intent.
Retained MQTT topics publish reality.
The database is the durable source of truth.
```

ImageFragments add one further principle:

```text
A Fragment represents one ordered occurrence in the diary chronology.
An Image represents a reusable uploaded asset.
```

There is still only one ordering mechanism: `Fragment.sequence`.

## Agreed Target Model

```text
Diaries
  diaries              list/relationship of Diary IDs

Diary
  id
  name                 String
  pages                derived/list relationship

Page
  id
  diaryId
  name                 String
  sequence             Decimal
  extension
  fragments            derived/list relationship

Fragment
  id
  pageId
  type                 MARQUEE | IMAGE
  year
  month
  day
  text
  sequence             Decimal
  lock
  imageId              optional

Marquee
  id
  fragmentId           unique
  x
  y
  width
  height

Image
  id
  relativePath         String
  mimeType
  originalFilename     String
  width
  height
  checksum
  caption
  altText
```

Relationships:

```text
Fragment 1 ---- 0..1 Marquee

A Fragment references zero or one Image.
An Image may be referenced by zero or more Fragments.
```

Conceptual names used by the UI/design:

```text
MarqueeFragment = Fragment(type=MARQUEE) with its optional Marquee
ImageFragment   = Fragment(type=IMAGE) with its optional reference to an Image
```

The `Diary.pages` and `Page.fragments` collections are conceptual relationships; they do not require persisted arrays of IDs.

## Current Source Baseline and Important Constraints

The current source is close enough to evolve without replacing the architecture, but several assumptions are currently marquee-centric.

### Responder

Current files reviewed include:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Marquee.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Page.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentDBDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/MarqueePublishDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UploadFile.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java
```

Important current behaviour:

1. `Fragment` does not own a `Page` relationship.
2. `Marquee` owns both `page_id` and unique `fragment_id`.
3. `AddFragment` creates and persists a Fragment and Marquee together.
4. `FragmentPublishDTO` contains `marqueeId`, but no `pageId`, `type` or `imageId`.
5. `DiaryContext.loadFromDatabase()` primarily discovers fragments by iterating Diary -> Page -> Marquee -> Fragment, then separately publishes fragments without marquees.
6. `UploadFile` already safely uploads JPEG, PNG, GIF and WebP content (plus `application/octet-stream`), performs size/checksum/path validation, and returns file URL/path information. It does not create persistent media metadata.
7. JPA classes are registered programmatically in `GetEntityManager`; a new `Image` entity must be registered there.

### Diaries Client

Current files reviewed include:

```text
diaries-client/src/app/model/fragment.ts
diaries-client/src/app/model/model-context.ts
diaries-client/src/app/fragment/**
diaries-client/src/app/files-list-dialog/**
diaries-client/src/app/mqtt/rpc.service.ts
```

Important current behaviour:

1. the TypeScript `Fragment` model contains `marqueeId` but not `pageId`, `type` or `imageId`;
2. `AddFragmentRequest` contains marquee geometry, so “add fragment” means “add marquee fragment” today;
3. the client already derives the selected marquee from the current page's marquees and fragment ID;
4. the files dialog can select an uploaded file and already has useful image browsing infrastructure;
5. current page navigation is appropriate for ImageFragments because editing is page-oriented rather than date-oriented.

### Diaries Web

Current files reviewed include:

```text
diaries-web/src/main/java/com/rsmaxwell/diaries/web/model/FragmentItem.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/model/MarqueeItem.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/mqtt/EntityType.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/mqtt/TopicParser.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/projection/ProjectionSnapshot.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/projection/ResolvedFragment.java
diaries-web/src/main/java/com/rsmaxwell/diaries/web/http/WebServer.java
```

The critical current assumption is in `ProjectionSnapshot`: a fragment with no `marqueeId`, a missing marquee, or inconsistent Fragment/Marquee linkage is not resolved into the reader chronology. Page and Diary are discovered through the Marquee. ImageFragments therefore require `Fragment.pageId` to become authoritative in the projection.

## Target Retained MQTT Model

Canonical retained entity topics should become:

```text
diaries/diaries/{diaryId}
diaries/pages/{pageId}
diaries/fragments/{fragmentId}
diaries/marquees/{marqueeId}
diaries/images/{imageId}
```

The existing date indexes remain useful:

```text
diaries/dates/{year}/{month}/{day}/{fragmentId}
```

The proposed fragment payload is additive during migration:

```json
{
  "id": 123,
  "version": 7,
  "pageId": 45,
  "type": "MARQUEE",
  "year": 1829,
  "month": 6,
  "day": 26,
  "sequence": 3.0000,
  "text": "...",
  "imageId": null,
  "marqueeId": 456,
  "lock": null
}
```

During the compatibility stages, `marqueeId` remains present so the old client/web contract is not broken immediately. The final model does not require it because Marquee has `fragmentId`.

An image payload should contain metadata only, not file bytes:

```json
{
  "id": 73,
  "version": 1,
  "relativePath": "images/portrait.jpg",
  "mimeType": "image/jpeg",
  "originalFilename": "portrait.jpg",
  "width": 1200,
  "height": 800,
  "checksum": "...",
  "caption": "",
  "altText": ""
}
```

The image URL is derived at the consumer from configuration:

```text
${base}/${filesRoot}/${image.relativePath}
```

The database and MQTT payload must not persist a deployment-specific absolute URL.

## RPC Direction

Do not overload the existing marquee-specific `AddFragment` request with a large set of conditional fields. Keep it as the marquee-fragment operation for compatibility, and add a clearly validated ImageFragment operation.

Recommended intent operations:

```text
AddFragment          existing MARQUEE semantics, enhanced internally
AddImageFragment     new IMAGE semantics
UpdateFragment       common date/text/sequence; validates type-specific imageId changes
SetFragmentImage     optional dedicated operation if clearer than extending UpdateFragment
```

`AddImageFragment` should accept:

```text
pageId
year
month
day
sequence
text
imageId              optional while editing if the UI creates before selection
```

All existing fragment locking and sequence-normalisation rules must apply equally to both types.

## Database Migration Strategy

Migration must be explicit, inspectable and reversible. Do not rely on Hibernate silently inventing the production migration.

### Phase A: additive schema

Add to `fragment`:

```text
page_id        BIGINT NULL initially
type           fragment type / varchar NULL initially
image_id       BIGINT NULL (once Image exists)
```

Add the `image` table when its feature is introduced.

Do not initially remove `marquee.page_id`.

### Phase B: backfill existing fragments

Every existing fragment reachable from a marquee can have Page ownership backfilled unambiguously. Rows without embedded-image migration questions are existing MarqueeFragments:

```sql
UPDATE fragment f
SET page_id = m.page_id
FROM marquee m
WHERE m.fragment_id = f.id;
```

Set `type='MARQUEE'` only for safe ordinary candidates. Rows containing legacy embedded images remain temporarily unclassified until 0028 records and applies a reviewed disposition; `<img>` detection alone does not determine semantic type.

The actual migration script must first check for invalid legacy data:

- a fragment referenced by more than one marquee (should be prevented by current uniqueness);
- a marquee with a missing page;
- a marquee with a missing fragment;
- a fragment with no marquee and therefore no inferable page;
- conflicting page relationships if unexpected legacy rows exist.

Fragments without a marquee cannot have `pageId` inferred from the current schema. The migration must list those IDs and stop before imposing `NOT NULL`, unless an explicit page assignment has been supplied. It must never guess a page.

### Phase C: validate and constrain

Final validation and non-null constraints are deferred to 0029. This preserves rollback compatibility while old responders that do not populate the additive columns could still be used. After orphan remediation and the 0028 reviewed conversion:

```text
fragment.page_id -> page.id foreign key
fragment.type     NOT NULL
```

When `Image` is introduced:

```text
fragment.image_id -> image.id foreign key, nullable
```

Application validation enforces:

```text
type=MARQUEE => image_id is null
type=IMAGE   => no Marquee row for fragment
```

A database CHECK may additionally enforce `MARQUEE => image_id IS NULL`, but the reverse cannot fully assert a Marquee row without a trigger. Prefer service-layer transaction validation plus integration tests unless there is a strong reason for triggers.

### Phase D: final normalisation

Only in 0029, after all deployed consumers use `Fragment.pageId` and the 0028 migration has reconciled its inventory:

- migrate responder code so Marquee page is derived from `marquee.fragment.page`;
- remove `marquee.page_id` from the database;
- stop requiring `marqueeId` in the canonical Fragment payload/client model;
- keep any compatibility field/topic only if operationally needed and explicitly documented.

## Existing Uploaded File Migration

The existing filesystem may already contain uploaded images that are not represented in PostgreSQL. The Image catalogue feature therefore needs an idempotent reconciliation/import utility.

For every supported image file below the configured Files root:

1. derive a normalized path relative to the Files root;
2. detect/validate MIME type from file content where practicable rather than trusting the extension alone;
3. read image dimensions;
4. compute SHA-256;
5. create an `Image` row if no image already has the same normalized `relativePath`;
6. retain original filename from the basename when no better historical value exists;
7. leave caption/alt text empty unless existing metadata supports them;
8. publish the resulting Image entity to retained MQTT state.

The utility must support dry-run mode and produce counts for created, existing, unsupported, unreadable and conflicting files.

Do not create ImageFragments while importing existing uploaded image files. Uploading/cataloguing an Image and placing it in the diary chronology are separate operations.

## Image Lifecycle Rules

Recommended rules:

- an Image can exist with zero referring fragments;
- an ImageFragment references at most one Image;
- the same Image may be referenced by multiple ImageFragments;
- deleting an ImageFragment never deletes the Image file/entity;
- deleting an Image that is still referenced must be rejected with a conflict response;
- deleting an unreferenced Image should remove the database entity and retained topic, then delete the underlying file in a controlled operation;
- if filesystem deletion fails, the operation must not silently leave retained/database state claiming success;
- overwrite of a file that already backs an Image must either be prohibited or treated as an explicit Image replacement/update operation with refreshed checksum/dimensions/version. Silent byte replacement would make metadata stale.

These protections begin when the Image catalogue is introduced, not in the final cleanup feature. As soon as a file has an Image row, the generic `DeleteFile` operation must refuse to delete it and the normal upload path must refuse to silently replace it. Before ImageFragments can reference Images, the responder must also provide reference-aware Image deletion.

## Client Behaviour

### MarqueeFragment

```text
LHS: diary Page image + editable selected marquee
RHS: editable fragment date and text
```

### ImageFragment

```text
LHS: diary Page image, no marquee
RHS: editable fragment date and text
     selected uploaded Image
     select/change Image control
```

The same fragment lock governs all fragment-level editing. Marquee editing controls must be disabled/hidden for `type=IMAGE`.

The new Image selection UI should choose Image entities by ID, not store a raw file URL in the Fragment. The existing file browser can be adapted or reused visually, but selection must return an `imageId` and Image metadata.

## Diaries Web Behaviour

Fragments remain sorted by date and `sequence`, independent of type.

For a selected MarqueeFragment:

```text
LHS: Page image with selected marquee
RHS: fragment text
```

For a selected ImageFragment:

```text
LHS: Page image without marquee
RHS: fragment text plus referenced Image
```

If an IMAGE fragment temporarily has no Image or references missing retained Image state, the reader should remain stable and show a clear unavailable-media placeholder/diagnostic rather than dropping the fragment from the chronology.

## Compatibility and Deployment Order

The implementation is intentionally staged:

```text
0022 responder/database adds pageId + type while preserving legacy fields
  -> old clients still work

0023 client + diaries-web consume pageId + type, still MARQUEE-only behaviour
  -> all consumers no longer depend on Marquee to discover Page

0024 add reusable persistent Image catalogue and migrate existing uploaded files
  -> no ImageFragments yet

0025 add responder ImageFragment persistence/RPC/retained contract and referenced-Image deletion protection
  -> backend supports IMAGE fragments

0026 add diaries-web ImageFragment projection/rendering
  -> IMAGE fragments are readable before production authoring is enabled

0027 add diaries-client ImageFragment creation/edit/selection
  -> ImageFragments can now be authored safely

0028 consume the reviewed legacy embedded-image inventory
  -> approved legacy rows are converted or split deliberately

0029 complete lifecycle hardening and remove redundant legacy relationships/contract assumptions
  -> target model complete
```

Where deployment could expose a new payload before a consumer understands it, the consumer must ignore unknown additive fields/types safely. The change records call this out explicitly.

The production order is stricter: the 0026-capable web reader must be deployed before the 0027 client enables IMAGE creation. Backend support from 0025 may be deployed earlier, but no production IMAGE rows should be created until the reader can render them.

## Legacy Embedded-Image Migration

The inventory produced by 0022 is an input to a dedicated migration feature, not merely historical documentation. After the Image catalogue, responder, reader and editor understand first-class Images, 0028 performs a reviewed conversion.

Every candidate receives an explicit disposition in a preserved migration manifest:

```text
CONVERT_TO_IMAGE
    Preserve the existing Fragment id, Page, date and sequence; attach the
    matched Image; remove its Marquee; and replace only the approved legacy
    <img> markup.

SPLIT_MARQUEE_AND_IMAGE
    Preserve the existing Fragment as MARQUEE, remove only the reviewed image
    markup, and create one adjacent IMAGE Fragment for each approved image.

KEEP_LEGACY
    Preserve the row and markup unchanged as a documented compatibility
    exception. This blocks claiming that all embedded media is normalized.

DEFER
    Make no change because the source is missing, external, ambiguous or still
    requires a decision.
```

The converter must never infer a disposition solely from the presence of an `<img>` element. Multiple embedded images cannot be placed on one IMAGE Fragment: an approved split creates one IMAGE Fragment per Image, reusing the same catalogued Image entity wherever appropriate.

## Testing Strategy

### Responder

Add/extend:

- JPA/repository tests for Page/Fragment/Image relationships;
- SQL migration verification against a copy of real data;
- retained DTO contract tests for pageId/type/imageId and Image topics;
- AddImageFragment validation tests;
- locking tests across both fragment types;
- sequence normalisation tests containing mixed MARQUEE/IMAGE fragments;
- image import/reconciliation tests;
- referenced-image deletion conflict tests;
- transaction tests ensuring DB and retained state are consistent.

### Diaries Client

Add/extend:

- model parsing for additive fragment fields and Image retained entities;
- current-page fragment navigation independent of Marquee presence;
- create ImageFragment workflow;
- image chooser selection/reselection;
- type-specific toolbar/control states;
- ImageFragment locking/date/text updates;
- mixed sequence reorder tests;
- missing-image state.

### Diaries Web

Add/extend:

- topic parser/decoder for `images`;
- projection tests for MARQUEE and IMAGE fragments;
- fragment-without-marquee must resolve when type=IMAGE and pageId is valid;
- missing image diagnostics/placeholders;
- mixed chronological ordering;
- rendering tests for Image URL/caption/alt text;
- retained replay/tombstone tests including Image entities.

### End-to-End

A final smoke dataset should contain at least:

```text
Page A
  seq 1 MARQUEE
  seq 2 IMAGE referencing Image X
  seq 3 MARQUEE
  seq 4 IMAGE referencing Image X again

Page B
  seq 1 IMAGE referencing Image Y
```

Verify editing, locking, date navigation, reorder/normalisation, restart/replay, file serving and web rendering.

## Backup, Rollback and Migration Evidence

Before applying any production schema/data migration:

1. stop writers or otherwise guarantee a consistent migration window;
2. take a PostgreSQL binary backup and preferably a readable SQL backup;
3. record row counts for diary/page/fragment/marquee/image;
4. run preflight SQL and archive the result;
5. apply migration;
6. run post-migration integrity queries;
7. restart responder and compare databaseMap/topicTreeMap/replay diagnostics;
8. smoke-test the client and web app;
9. only then remove legacy columns in 0029.

Rollback for additive stages is primarily application rollback plus database restore if schema/data changes must be undone. The final destructive 0029 migration requires its own fresh backup and cannot rely on simply rolling back container images.

## Proposed Change-Control Features

| ID | Feature | Purpose |
|---|---|---|
| 0022 | Migrate fragments to explicit page ownership and type | Add `Fragment.pageId`/`type`, backfill unambiguous ownership and safe types, inventory exceptions, publish additive contract |
| 0023 | Make consumers use typed fragment page ownership | Update client and web projections to stop depending on Marquee for Page resolution |
| 0024 | Introduce reusable persistent Image catalogue | Add Image entity/topics, reconcile existing files and protect catalogued paths from generic deletion/overwrite |
| 0025 | Add responder ImageFragment persistence and RPC | Add `imageId`, AddImageFragment, validation, locking, mixed sequencing and reference-aware deletion |
| 0026 | Render ImageFragments in diaries-web | Consume Image topics and render IMAGE fragments before authoring is enabled |
| 0027 | Add ImageFragment editing to diaries-client | New button, image selection, type-specific editor rendering and controls |
| 0028 | Migrate reviewed legacy embedded-image fragments | Consume the 0022 inventory and deliberately convert, split, preserve or defer every candidate |
| 0029 | Complete Image lifecycle and remove legacy fragment/marquee coupling | Reconciliation/replacement hardening, cleanup, drop redundant `marquee.page_id`, retire legacy assumptions |

Each feature is supplied as a separate change-control `README.md` under `change-control/todo` in this package.

## Definition of Done for the Whole Proposal

The proposal is complete when:

- every existing historical fragment has a valid `pageId` and a reviewed final type or explicitly documented compatibility disposition;
- no existing diary chronology or marquee geometry has changed during migration;
- uploaded images are durable reusable Image entities with retained MQTT representation;
- a user can create/edit/reorder an ImageFragment in diaries-client using the same fragment locking/date/text rules;
- the same Image may be reused by multiple ImageFragments;
- diaries-web renders mixed MarqueeFragments and ImageFragments in date/sequence order;
- missing or incomplete media cannot make the reader projection discard otherwise valid fragments;
- database and retained MQTT state converge correctly after restart/replay;
- image deletion cannot break existing ImageFragments silently;
- every legacy embedded-image candidate inventoried by 0022 has a recorded 0028 disposition and every approved conversion reconciles;
- `Fragment.pageId` is authoritative and redundant persistent `Marquee.pageId` has been removed;
- tests and smoke validation cover both fragment types across database, MQTT, client, web and static file serving.
