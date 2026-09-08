# 0025-FEAT - Add responder ImageFragment persistence and RPC

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-07

## Summary

Extend the responder so a Fragment can reference a reusable Image and can be created/updated as `type=IMAGE`. Add explicit ImageFragment RPC intent while applying existing locking, sequence normalisation, persistence and retained-publication rules to both fragment types.

## Background

By this point:

- Fragment owns Page and type;
- consumers understand typed Page ownership;
- reusable Image entities exist and are retained.

The responder can now introduce the missing relationship:

```text
Fragment.image_id -> Image.id (nullable)
```

without embedding file paths/URLs in Fragment.

## Expected Behaviour

- `AddFragment` continues creating MARQUEE fragments for compatibility;
- new `AddImageFragment` creates an IMAGE fragment for a Page;
- an ImageFragment references zero or one existing Image while editing;
- a MARQUEE fragment cannot reference an Image;
- an IMAGE fragment cannot have a Marquee;
- date/text/sequence/lock semantics are common to both types;
- mixed MARQUEE/IMAGE sequence normalisation works correctly;
- fragment retained payload includes `imageId`;
- an Image referenced by any Fragment cannot be deleted;
- Image deletion cannot be bypassed through generic file operations.

## Scope

### Database / JPA

Add nullable `fragment.image_id` foreign key to `image(id)` and JPA relationship (`ManyToOne` is appropriate because many Fragments may reference one Image).

Do not put `fragmentId` on Image.

### RPC

Add `AddImageFragment` handler with fields:

```text
pageId
year
month
day
sequence
text
imageId optional
```

Validate:

- Page exists;
- requested Image exists if provided;
- type is fixed by the operation and cannot be supplied inconsistently;
- authorization is EDITOR or stronger;
- sequence/date/text validation matches existing Fragment rules.

Consider a dedicated `SetFragmentImage` RPC if extending `UpdateFragment` would make validation opaque. If `UpdateFragment` gains `imageId`, it must reject `imageId` for MARQUEE fragments and must not permit arbitrary type mutation unless a separately designed conversion workflow exists. This proposal does not require converting an existing fragment between types.

### Persistence Transaction

Create ImageFragment without Marquee. Do not reuse `DiaryContext.save(fragment, marquee)` unchanged; introduce focused save methods or a service that supports both valid aggregate shapes without nullable assumptions scattered through handlers.

### Retained MQTT

Fragment payload now includes:

```text
pageId
type
imageId
```

During compatibility, `marqueeId` may remain. For an IMAGE fragment it is null.

### Locking and Sequence Utilities

Audit:

```text
FragmentLocking
UpdateFragment
DeleteFragment
FragmentSequenceNormaliser
NormaliseFragments
```

Any utility that inflates/publishes `FragmentAndMarquee` must be generalized so IMAGE fragments do not require a Marquee. Prefer a `ResolvedFragmentState`/service abstraction over proliferating null Marquee parameters.

Deleting an ImageFragment removes only the Fragment. It must not delete the referenced Image.

### Reference-aware Image deletion

Implement `DeleteImage(imageId)` before enabling any operation that creates an Image reference:

- lock or otherwise serialize the Image row and reference check in the database transaction;
- return conflict when any Fragment references the Image;
- for an unreferenced Image, coordinate filesystem removal, database removal and retained tombstone so partial failure is reported and recoverable;
- never report success while the database/topic tree claims deletion but the implementation has silently lost track of a failed filesystem operation;
- retain the 0024 guards so `DeleteFile` cannot bypass this operation.

Because PostgreSQL and the filesystem cannot participate in one atomic transaction, document the chosen failure protocol. A staged deletion state or recoverable operation journal is preferred to irreversible file deletion before the database transaction is known to be durable.

## Detailed Implementation Steps

- [ ] Add explicit migration SQL for nullable `fragment.image_id` FK.
- [ ] Extend Fragment entity/DB DTO/publish DTO with image relationship/ID.
- [ ] Add repository/inflation support for referenced Image.
- [ ] Introduce a fragment aggregate/service that can represent MARQUEE and IMAGE shapes safely.
- [ ] Implement `AddImageFragment` RPC and register it with responder request handling.
- [ ] Decide and implement `SetFragmentImage` versus type-aware UpdateFragment.
- [ ] Ensure UpdateFragment preserves immutable type/page relationship unless separately intended.
- [ ] Generalize delete/lock/unlock publication to avoid assuming a Marquee exists.
- [ ] Generalize sequence normalisation for mixed types.
- [ ] Add retained contract tests for IMAGE payloads.
- [ ] Add integration tests for two ImageFragments referencing the same Image.
- [ ] Add tests proving deletion of one ImageFragment leaves Image and other reference intact.
- [ ] Add tests proving MARQUEE cannot carry imageId and IMAGE cannot acquire a Marquee through responder operations.
- [ ] Add an indexed repository query for Fragment references to an Image.
- [ ] Implement reference-aware `DeleteImage` with a documented partial-failure protocol.
- [ ] Test the race between attaching an Image and attempting to delete it.
- [ ] Test retained tombstone and filesystem failure recovery.

## Acceptance Criteria

- [ ] Responder can create an IMAGE fragment with and without initial image selection.
- [ ] Existing AddFragment MARQUEE workflow remains compatible.
- [ ] Image reuse across multiple fragments works.
- [ ] Locks operate identically at Fragment level for both types.
- [ ] Mixed-type sequence normalisation preserves correct order.
- [ ] Retained DB replay recreates IMAGE fragments correctly.
- [ ] Deleting ImageFragment does not delete Image.
- [ ] Invalid cross-type relationships are rejected.
- [ ] A referenced Image cannot be deleted.
- [ ] An unreferenced Image can be deleted without leaving an untracked partial-success state.
- [ ] Generic `DeleteFile` cannot bypass Image reference integrity.

## Dependencies

Requires 0022 and 0024. 0023 must be deployed before IMAGE creation is enabled. The 0026-capable diaries-web reader must be deployed before the 0027 client enables production authoring.

## Deployment and Rollback

Backend capability may be deployed before any UI creates IMAGE fragments. Do not create production IMAGE fragments until 0026 has been deployed and verified. If administrative RPC access could create them earlier, gate the handler with deployment configuration or operational access control.
