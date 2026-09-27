# 0025-FEAT - Implementation Steps

## Objective

Extend `diaries-responder` so `Fragment` can persist and publish an optional reference to a reusable catalogued `Image`, and so the responder can create and edit `IMAGE` fragments without requiring a `Marquee`.

The implementation must preserve the existing MARQUEE workflow, locking rules, sequence ordering, retained MQTT behaviour and 0024/0030 Image lifecycle protections.

This feature is responder-side capability only. It must **not** enable production ImageFragment authoring by itself. `0026-FEAT` must be deployed and verified before `0027-FEAT` exposes ImageFragment authoring in the Angular client.

The steps below are based on the current source bundle dated 2026-09-27. In that baseline:

- 0022 has already added `Fragment.page_id` and `Fragment.type`;
- 0023 consumers understand typed Page ownership;
- 0024 has added the persistent reusable `Image` catalogue and retained `diaries/images/{id}` topics;
- 0030 has already implemented recoverable `DeleteImage` and the generic `DeleteFile` catalogue guard;
- `Fragment` does not yet contain `image_id`;
- `FragmentPublishDTO` does not yet publish `imageId`;
- `AddFragment` still creates MARQUEE fragments and a Marquee together;
- `UpdateFragment`, locking and sequence-normalisation code can tolerate a missing Marquee in some paths, but the helper naming and persistence API still assume the historical Fragment/Marquee pairing;
- the existing `DeleteImage` path does **not** yet reject an Image referenced by a Fragment.

## Design decisions for this implementation

### 1. Fragment owns the Image reference

Add:

```text
fragment.image_id -> image.id
```

The relationship is nullable and many-to-one:

```text
many Fragments -> one reusable Image
```

Do not add `fragmentId` or a fragment collection to the persisted `Image` model.

### 2. Valid aggregate shapes

The responder must enforce these shapes:

```text
MARQUEE Fragment
    pageId required for normal post-0022 data
    imageId = null
    Marquee = zero or one during the compatibility window

IMAGE Fragment
    pageId required
    imageId = zero or one
    Marquee = none
```

The temporary ability for an IMAGE fragment to have `imageId = null` is deliberate. It supports creation/editing and degraded rendering without inventing file paths or placeholder Image records.

### 3. Keep `AddFragment` backward compatible

`addFragment` remains the MARQUEE creation RPC and keeps its current request shape.

Add a separate:

```text
addImageFragment
```

RPC for IMAGE creation.

### 4. Extend `UpdateFragment`; do not add `SetFragmentImage`

Use the existing fragment lock/version transaction for Image selection changes. Extend `updateFragment` with optional `imageId` semantics instead of introducing a second write RPC.

For an existing IMAGE fragment:

```text
imageId key absent   -> preserve current Image reference
imageId: null        -> clear the Image reference
imageId: <positive>  -> replace with that existing Image
```

For a MARQUEE fragment:

```text
non-null imageId -> reject
```

`type` and `pageId` remain immutable through ordinary `updateFragment` calls. This feature does not provide MARQUEE <-> IMAGE conversion.

This choice keeps date, text, sequence and Image-selection changes in one optimistic-versioned edit operation and avoids awkward multi-RPC lock ownership.

### 5. Generalise Fragment state instead of spreading nullable Marquee assumptions

Replace the narrowly named `FragmentAndMarquee` helper with a type-aware state/aggregate helper such as:

```text
ResolvedFragmentState
```

It should contain the Fragment and its optional Marquee. The Image relationship is held by `Fragment` itself.

The helper/service boundary should make it explicit that a Fragment is the authoritative object and a Marquee is type-specific associated state rather than an object every Fragment must possess.

### 6. Extend the existing 0030 Image deletion path

Do not create a second Image-deletion implementation.

Enhance the existing:

```text
DeleteImage
ImageCatalogueService
ImageRepository / FragmentRepository
```

path so a referenced Image produces a controlled conflict before any physical-file staging occurs.

The database foreign key remains the final integrity barrier. The responder must also perform an explicit reference check so the RPC produces a stable `409 Conflict` rather than exposing an internal constraint failure.

### 7. No legacy embedded-image migration in 0025

0025 introduces capability only. It does not convert the reviewed legacy HTML/image candidates. That data conversion remains 0028.

---

## Step 1 — Freeze and record the pre-0025 responder baseline

Before changing the schema or Fragment contract, capture the behaviours which must remain compatible.

### Baseline behaviours to preserve

Verify and record that:

- `addFragment` creates a `MARQUEE` Fragment and a Marquee;
- `updateFragment` updates date/text/sequence while preserving `pageId` and `type`;
- fragment locking/unlocking publishes the Fragment correctly;
- sequence normalisation orders all Fragment rows by date/sequence/id and does not depend on Marquee geometry;
- `DeleteFragment` removes a Fragment and its optional Marquee;
- startup/database replay publishes Fragments independently of whether a Marquee exists;
- `DeleteFile` rejects catalogue-owned Image paths;
- current `DeleteImage` succeeds for an unreferenced Image and performs the recoverable 0030 file/database/MQTT lifecycle.

### Tests/evidence to retain

At minimum run the existing focused tests covering:

```text
FragmentRepositoryImplTest
FragmentSequenceNormaliserTest
DiaryContextTest
RetainedStateDtoContractTest
DeleteImageTest
ImageCatalogueDeletionTest
ImageDeletionConcurrencyTest
```

and a responder build.

### Result

The later implementation must be demonstrably additive:

```text
existing MARQUEE behaviour before 0025
    ==
existing MARQUEE behaviour after 0025
```

Do not start production ImageFragment creation if the baseline is already failing.

---

Step 1 completed on 2026-09-27. Frozen clean responder commit and source hashes, recorded source/test behaviour matrix, and ran all seven required suites plus generic DeleteFile guard coverage: 47 passed, zero failures/errors/skips; responder build passed. See [Step 1 baseline](evidence/Step%201/README.md). No schema or application behaviour changed. Handler source inspection is distinguished from executable coverage in the evidence.

## Step 2 — Add the database schema for `fragment.image_id`

Create a dedicated migration under the 0025 change-control directory, following the explicit migration style already used by 0022 and 0024.

Suggested files:

```text
change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/
  migration/
    001-preflight.sql
    002-add-fragment-image-reference.sql
    003-postflight.sql
    README.md
    tests/
      constraints.sql
```

If the existing migration tooling warrants it, also provide the same sort of PowerShell runner used by the 0024 migration.

### 2.1 Preflight

The preflight should prove that the expected prerequisite schema exists:

- `public.fragment` exists;
- `public.fragment.page_id` exists;
- `public.fragment.type` exists;
- `public.image` exists;
- `fragment_type_check` accepts `MARQUEE` and `IMAGE`;
- current Fragment/Image rows are internally consistent enough to add the FK;
- an existing `fragment.image_id`, if present because of a partial/repeated migration attempt, has the expected type and constraints.

Capture row counts and integrity values needed to prove that the migration is additive and does not modify chronology data.

### 2.2 Add the nullable column

Add:

```sql
ALTER TABLE public.fragment
    ADD COLUMN IF NOT EXISTS image_id BIGINT;
```

No existing row is backfilled in 0025.

### 2.3 Add the foreign key

Add a named FK such as:

```text
fragment_image_fk
```

from:

```text
fragment(image_id)
```

to:

```text
image(id)
```

Use normal PostgreSQL restrictive/no-action deletion semantics. Do **not** use `ON DELETE CASCADE`; deleting a Fragment must not delete its Image, and deleting an Image must fail while it is referenced.

Use the same safe staged pattern as earlier migrations where practical:

```text
ADD CONSTRAINT ... NOT VALID
VALIDATE CONSTRAINT ...
```

### 2.4 Add the reference index

Add:

```text
fragment_image_id_idx
```

on `fragment(image_id)`.

The index is required both for normal reference lookup and for efficient Image deletion protection.

### 2.5 Add a same-row type/reference check

Add a check constraint which prevents a non-null Image reference on a non-IMAGE Fragment, for example the logical rule:

```text
image_id is null
OR
(type is not null AND type = 'IMAGE')
```

This provides a database backstop for:

```text
MARQUEE -> no Image
```

The inverse rule:

```text
IMAGE -> no Marquee
```

crosses tables and should remain responder/service enforced in 0025. Final destructive integrity tightening belongs to 0029.

### 2.6 Postflight

Verify:

- the column exists and is `BIGINT`/nullable;
- the FK exists and is validated;
- the index exists;
- the type/reference check exists and is validated;
- no current Fragment has a non-null `image_id` at migration time unless it was explicitly expected by a repeat/recovery run;
- Fragment count and existing chronology values are unchanged;
- Image count is unchanged.

### Completion criterion

The migrated database accepts both:

```text
MARQUEE + image_id null
IMAGE   + image_id null/non-null existing Image
```

and rejects an invalid/missing Image id or a MARQUEE row carrying `image_id`.

---

Step 2 completed on 2026-09-27. Added explicit preflight/apply/postflight SQL, compatible-repeat/partial-recovery checks, restrictive FK/index/type-reference check, data-preservation snapshots and migration/test runners. Thirteen scenario groups passed against disposable PostgreSQL restored from the frozen backup; all original data digests unchanged. See [Step 2 evidence](evidence/Step%202/README.md). No live migration or JPA/RPC change performed.

## Step 3 — Extend the Fragment persistence model and repository contract

Update the responder model/DTO/repository layer before exposing any new RPC.

### Files expected to change

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentDBDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java
```

### 3.1 `Fragment`

Add an optional JPA relationship:

```java
@ManyToOne(optional = true)
@JoinColumn(name = "image_id")
private Image image;
```

Follow the existing `page`/`persistedPageId` pattern so repository-oriented DTOs can carry an Image id without requiring every repository operation to inflate the Image object.

Add the equivalent of:

```text
persistedImageId
getImageId()
setImage(Image image)
```

Ensure both `FragmentDBDTO` and `FragmentPublishDTO` constructors preserve `imageId` when reconstructing a Fragment.

### 3.2 `FragmentDBDTO`

Add:

```text
Long imageId
```

This is the persistence representation of the nullable FK.

### 3.3 `FragmentRepositoryImpl`

Add `image_id` to:

- `getFields()`;
- `getValues()`;
- `newDTO()` positional mapping;
- every hand-written Fragment projection in the class.

Pay special attention to the positional shift of all lock columns after inserting `image_id`. The current tests specifically protect this positional mapping and must be extended.

Update projections used by:

```text
findAllWithoutMarquee
findAllFragmentsWithMarqueesonDate
findStaleLocks
```

and any later-added query which delegates to `newDTO()`.

### 3.4 Add reference lookup

Add a bound repository method such as:

```java
boolean existsByImageId(Long imageId);
```

Optionally also add:

```java
long countByImageId(Long imageId);
```

if useful for diagnostics/tests.

Do not implement the reference check by assembling raw untrusted SQL in the RPC handler.

### 3.5 Repository/model tests

Extend `FragmentRepositoryImplTest` to prove:

- `imageId` is read from the correct projection position;
- lock columns still map correctly;
- null migration values remain null;
- `getFields().size() == getValues(fragment).size()`;
- a Fragment DTO round-trip preserves Page/type/Image identity.

Add a database-backed repository test for `existsByImageId` against:

- no references;
- one reference;
- two references to the same Image;
- reference deletion.

### Completion criterion

All repository operations can round-trip a Fragment with or without `image_id` without changing any existing Page/type/lock values.

---

## Step 4 — Generalise Fragment aggregate resolution and persistence

Remove the remaining persistence assumption that every newly created Fragment has a Marquee.

### Files expected to change/add

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentAndMarquee.java
```

Prefer replacing `FragmentAndMarquee.java` with a more accurate abstraction such as:

```text
ResolvedFragmentState.java
```

and update callers accordingly.

### 4.1 Focused create methods

Replace the generic historical method:

```java
save(Fragment fragment, Marquee marquee)
```

with explicit operations, for example:

```text
saveMarqueeFragment(fragment, marquee)
saveImageFragment(fragment)
```

Both operations own one database transaction.

`saveMarqueeFragment` must require:

```text
fragment.type == MARQUEE
fragment.imageId == null
marquee != null
marquee.fragment == fragment
marquee.page == fragment.page
```

`saveImageFragment` must require:

```text
fragment.type == IMAGE
marquee does not exist
image reference is null or an existing Image
```

Do not silently coerce an invalid type to make the operation succeed.

### 4.2 Image inflation/reference helper

Extend `DiaryContext.inflateFragment(...)` so a non-null `imageId` is resolved to the corresponding `Image` relationship.

For Fragment writes which attach/change an Image, use a transaction-scoped Image lookup/lock rather than trusting a detached id. The intended concurrency rule is:

```text
attach Image reference and DeleteImage
    must serialize through the database
```

A JPA `PESSIMISTIC_READ`/key-share-style lookup of the Image row inside the Fragment write transaction is appropriate, provided it is verified against PostgreSQL behaviour in the integration test.

### 4.3 General state resolution

Provide one helper which resolves:

```text
Fragment
optional Marquee
Fragment.image / imageId
```

and validates the type-specific shape before publication where appropriate.

Do not make the reader/replay path discard a Fragment merely because an optional associated object is absent. Invalid relationships should be explicit failures/diagnostics in writer paths, while retained replay must remain capable of exposing recoverable database state.

### Completion criterion

The responder has a clean creation/persistence path for both Fragment types without passing `null` into an API that conceptually requires a Marquee.

---

## Step 5 — Extend the retained Fragment contract with `imageId`

Update:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java
```

Add:

```text
Long imageId
```

### Required payload shape

A MARQUEE Fragment should publish, for example:

```json
{
  "id": 33,
  "pageId": 22,
  "type": "MARQUEE",
  "imageId": null,
  "marqueeId": 44
}
```

An IMAGE Fragment should publish, for example:

```json
{
  "id": 34,
  "pageId": 22,
  "type": "IMAGE",
  "imageId": 91,
  "marqueeId": null
}
```

Retain `marqueeId` for compatibility in 0025. Its eventual retention/removal is a 0029 contract decision.

### Replay

Update `DiaryContext.loadFromDatabase()` so database replay reconstructs `imageId` correctly for every Fragment.

The Fragment remains published to both existing topics:

```text
diaries/fragments/{id}
diaries/dates/{year}/{month}/{day}/{id}
```

No new Fragment topic hierarchy is needed.

### Contract tests

Extend `RetainedStateDtoContractTest` to prove:

- `imageId` is always present in the JSON shape, including explicit `null`;
- MARQUEE payloads keep `imageId = null`;
- IMAGE payloads carry the referenced Image id;
- IMAGE payloads use `marqueeId = null`;
- canonical and date aliases contain identical payloads;
- tombstone behaviour on both Fragment topics is unchanged.

Extend `DiaryContextTest` to replay an IMAGE Fragment with:

- a valid Image reference;
- a null Image reference;
- no Marquee.

### Completion criterion

A responder restart/database replay can recreate the exact retained representation required by 0026 without requiring any client authoring code.

---

## Step 6 — Implement and register `addImageFragment`

Create:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragment.java
```

Register it in:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java
```

as:

```text
addImageFragment
```

### Request contract

Accept:

```text
pageId
year
month
day
sequence
text
imageId optional
```

Do not accept caller-controlled Fragment `type`; the operation itself fixes:

```text
type = IMAGE
```

### Validation

The handler must:

1. authenticate the access token;
2. require an active user;
3. require `EDITOR` or stronger;
4. validate `pageId` and inflate the Page;
5. validate year/month/day/sequence/text using the same rules and normalisation as `AddFragment`;
6. if `imageId` is supplied and non-null, require a positive id and resolve the existing Image inside the write transaction;
7. reject a missing Image as a controlled not-found/bad-request contract decision rather than an internal error;
8. construct an IMAGE Fragment with no Marquee;
9. save through the focused IMAGE persistence operation;
10. publish the committed `FragmentPublishDTO`;
11. return the created Fragment payload using the same general success convention as `AddFragment`.

### Sequence behaviour

Creation must participate in the same chronology as MARQUEE fragments. If the existing `AddFragment` semantics intentionally allow arbitrary decimal insertion without immediate normalisation, preserve that behaviour here. Do not create a separate IMAGE sequence namespace.

### Tests

Add handler tests covering:

- authorization;
- missing/invalid Page;
- malformed date/sequence/text;
- no `imageId`;
- valid `imageId`;
- missing Image;
- type is always IMAGE regardless of unexpected caller fields;
- no Marquee row is created;
- retained Fragment has `imageId` and `marqueeId = null`.

### Completion criterion

The responder can create an IMAGE Fragment with either zero or one existing Image reference without changing `addFragment` behaviour.

---

## Step 7 — Make `UpdateFragment` type-aware and Image-aware

Update:

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java
```

Do not add arbitrary type conversion.

### 7.1 Preserve authoritative identity

Continue loading the original Fragment from the database and carry forward:

```text
pageId
existing type
```

Reject or ignore-with-explicit-contract any supplied attempt to change `pageId` or `type`. Prefer explicit rejection if those keys are present with a different value so accidental future client drift is visible.

### 7.2 `imageId` semantics

Use `args.containsKey("imageId")` so absence and explicit JSON null are distinguishable.

For `MARQUEE`:

```text
imageId absent/null -> keep null
imageId non-null    -> 400 Bad Request
```

For `IMAGE`:

```text
imageId absent      -> preserve current imageId
imageId null        -> clear reference
imageId positive    -> resolve and attach existing Image
```

A nonexistent referenced Image must not turn into a nullable/missing relationship silently.

### 7.3 Lock/version semantics

Image selection is part of the Fragment edit. It must obey the existing rules:

- Fragment must be locked by the caller;
- the supplied Fragment version must match;
- one successful update increments the version once according to the existing model rules;
- successful edit clears the Fragment lock exactly as existing `UpdateFragment` does;
- failed edit rolls back without publishing a false retained state.

### 7.4 Sequence normalisation

Keep the existing `FragmentSequenceNormaliser.normaliseAffectedDates(...)` call in the same transaction.

Changing only `imageId` must not renumber chronology. Changing date/sequence at the same time must normalise exactly as it does for MARQUEE fragments.

### 7.5 Publication

After commit/reload, publish the final Fragment with:

```text
correct imageId
correct optional marqueeId
lock = null
```

If date keys changed, remove the old date-topic alias before publishing the new one exactly as today.

### Tests

Cover at least:

- MARQUEE update with no `imageId` remains compatible;
- MARQUEE rejects non-null `imageId`;
- IMAGE text-only update preserves `imageId` when the key is absent;
- IMAGE can attach an Image;
- IMAGE can replace an Image;
- IMAGE can clear an Image with explicit null;
- missing Image is rejected;
- stale version is rejected;
- wrong lock owner is rejected;
- date/sequence + Image change commits as one edit;
- retained publication reflects only the committed result.

### Completion criterion

All ordinary Fragment editing fields, including IMAGE selection, participate in one existing lock/version transaction without introducing a second edit protocol.

---

## Step 8 — Generalise lock, unlock, delete and normalisation paths for mixed Fragment types

Audit every path named in the feature README and every caller of the old `FragmentAndMarquee` helper.

### Files expected to change

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentLocking.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliser.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/LockFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UnlockFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/NormaliseFragments.java
```

Also audit:

```text
AddMarquee
UpdateMarquee
DeleteMarquee
```

for cross-type guards.

### 8.1 Lock/unlock

Locking is owned by the Fragment, not by Marquee or Image.

For both types:

```text
lockFragment   -> updates/publishes Fragment lock
unlockFragment -> clears/publishes Fragment lock
```

Publication must not require a Marquee.

The selected Image itself is **not** locked by Fragment editing. The reusable Image row has its own lifecycle semantics; selecting it only changes the Fragment FK.

### 8.2 DeleteFragment

For MARQUEE:

```text
delete optional Marquee
-> delete Fragment
-> tombstone Marquee if present
-> tombstone Fragment aliases
```

For IMAGE:

```text
delete Fragment only
-> leave referenced Image row/file/topic untouched
-> tombstone Fragment aliases
```

Deleting an ImageFragment must never call `DeleteImage` and must never infer that an otherwise unreferenced Image should also be removed.

### 8.3 Marquee operations

Ensure responder operations cannot create an invalid IMAGE+Marquee relationship.

`AddMarquee` already checks `FragmentType.IMAGE`; keep and strengthen the invariant so it also requires a MARQUEE-compatible Fragment and a null `imageId`.

`UpdateMarquee` must reject an invalid IMAGE Fragment rather than treating it as an ordinary geometry update.

`DeleteMarquee` may remain capable of removing an existing invalid marquee as a repair action if deliberately desired, but it must not mutate the Fragment into IMAGE/MARQUEE implicitly. Document whichever repair behaviour is retained.

### 8.4 Sequence normalisation

`FragmentSequenceNormaliser` must operate solely on Fragment chronology:

```text
year, month, day, sequence, id
```

and never filter by Fragment type.

Its publication helper may resolve an optional Marquee, but absence of a Marquee for IMAGE is normal and must not be an error.

Add a focused mixed-type test such as:

```text
MARQUEE sequence 4
IMAGE   sequence 2
MARQUEE sequence 1
IMAGE   sequence 3
```

and prove normalisation yields one shared ordered sequence `1..4`, with the Image references preserved.

### Completion criterion

All shared Fragment lifecycle operations work identically at the Fragment level for MARQUEE and IMAGE, with only the type-specific associated-object rules differing.

---

## Step 9 — Add reference-aware protection to the existing `DeleteImage`

**Complete - 2026-09-27.** Reference checks run before staging and again under the deletion transaction's Image row lock. Clean reference conflicts restore staged bytes and return 409. Full responder regression/build, both database race orderings, client compatibility tests and production build passed. See [Step 9 evidence](evidence/Step%209/README.md).

This is the critical integration with completed feature 0030.

Do **not** replace the 0030 recoverable file-deletion protocol. Extend it.

### Files expected to change

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueService.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteImage.java
```

### 9.1 Reference check location

The reference decision must occur inside the database-side deletion transaction while the Image row is protected from a concurrent reference/delete race.

The logical operation is:

```text
acquire existing 0030 catalogue/filesystem lock
-> identify Image
-> stage nothing yet if it is already known to be referenced where practical
-> enter DB delete transaction
-> lock Image row for deletion
-> check Fragment reference(s)
-> if referenced: rollback/return conflict
-> otherwise continue existing 0030 deletion protocol
```

The exact location of the physical staging relative to the DB reference check must preserve the proven 0030 recovery guarantees. If staging remains before the database transaction, a reference conflict must restore/clean the staging backup exactly like another clean rollback; it must never leave a harmless conflict looking like an administrator-recovery failure.

A small refinement which checks references before staging is preferable if it can be done without weakening race safety. The authoritative check must still be repeated/held under the deletion transaction/row lock.

### 9.2 Stable conflict exception

Introduce a deliberate service exception such as:

```text
ImageReferencedException
```

and map it in `DeleteImage` to:

```text
409 Conflict
```

Do not depend on parsing PostgreSQL FK exception text in the handler.

### 9.3 Keep the FK as final protection

Even after the explicit query, the `fragment.image_id` FK remains mandatory. A direct database writer or unforeseen race must still be unable to delete a referenced Image.

### 9.4 Attach/delete race

The attach/update transaction and Image deletion transaction must serialize correctly.

Test both orderings:

```text
A: attach starts/commits first
   -> DeleteImage observes reference -> 409

B: DeleteImage locks/deletes first
   -> later attach cannot resolve/reference deleted Image -> controlled failure
```

There must be no ordering in which both operations report success while the resulting Fragment points at a missing Image.

### 9.5 Multiple references

Test:

```text
Fragment A -> Image 91
Fragment B -> Image 91
```

Then:

- `DeleteImage(91)` -> conflict;
- delete Fragment A -> Image remains and deletion still conflicts;
- delete Fragment B -> Image remains;
- `DeleteImage(91)` -> now succeeds through the existing 0030 recoverable lifecycle.

### 9.6 Generic file guard

Re-run the 0030 `DeleteFile` guard tests unchanged.

A caller must never be able to bypass reference integrity by deleting the bytes directly.

### Completion criterion

An Image cannot be deleted by any supported responder operation while one or more Fragments reference it, and the concurrency outcome is deterministic and database-safe.

---

## Step 10 — Add focused unit and contract coverage for cross-type invariants

**Complete - 2026-09-27.** Added the full writer invariant matrix, legacy addFragment contract, and handler-level lifecycle/guard tests. The focused 85-case suite and full responder tests/build passed. See [Step 10 evidence](evidence/Step%2010/README.md).

Before the database-backed end-to-end test, add a concentrated responder test set for the new contract.

Suggested new/extended test classes include:

```text
handlers/AddImageFragmentTest.java
handlers/UpdateFragmentTest.java
repositoryImpl/FragmentRepositoryImplTest.java
dto/RetainedStateDtoContractTest.java
utilities/DiaryContextTest.java
utilities/FragmentSequenceNormaliserTest.java
utilities/ImageCatalogueDeletionTest.java
utilities/ImageDeletionConcurrencyTest.java
```

A dedicated aggregate/invariant test class is appropriate if a new `ResolvedFragmentState` or validation helper is introduced.

### Required invariant matrix

Prove:

| Fragment type | Marquee | imageId | Expected writer result |
| --- | --- | --- | --- |
| MARQUEE | present | null | valid |
| MARQUEE | absent | null | allowed during compatibility/degraded state |
| MARQUEE | present/absent | non-null | reject |
| IMAGE | absent | null | valid/incomplete |
| IMAGE | absent | non-null existing | valid |
| IMAGE | present | any | reject through responder writer operations |
| IMAGE | absent | non-null missing | reject |

### Additional contract tests

Prove that:

- `addFragment` request/reply shape remains compatible;
- `addImageFragment` does not create/publish a Marquee;
- `updateFragment` cannot mutate `type`;
- `updateFragment` cannot mutate authoritative `pageId`;
- `FragmentPublishDTO.imageId` is additive and explicit;
- one Image may be reused by multiple Fragments;
- deleting one referring Fragment never changes the Image;
- locking is identical for both Fragment types.

### Completion criterion

The unit/contract suite can detect every invalid cross-type mutation before integration testing starts.

---

## Step 11 — Add database-backed ImageFragment integration tests

**Complete - 2026-09-27.** Combined PostgreSQL/Mosquitto lifecycle fixture plus both attach/delete race orderings passed (2 tests, no skips), with JPA schema validation and unchanged database row hashes after cleanup. All 12 scenarios are mapped in [Step 11 evidence](evidence/Step%2011/README.md).

Create an integration fixture using disposable PostgreSQL data and, where publication is in scope, disposable Mosquitto retained topics.

Do not use production data or the live NAS for this step.

### Database fixture

Create at least:

```text
one Diary
one Page
at least two catalogued Images
mixed MARQUEE and IMAGE Fragments
one Image reused by two IMAGE Fragments
```

### Scenarios

Verify in real PostgreSQL:

1. `fragment.image_id` FK accepts an existing Image;
2. FK rejects a missing Image;
3. same-row check rejects MARQUEE + `image_id`;
4. `addImageFragment` commits IMAGE + optional Image reference;
5. no Marquee row is created for IMAGE;
6. two IMAGE fragments can reference the same Image;
7. `updateFragment` attach/replace/clear works under lock/version rules;
8. mixed MARQUEE/IMAGE normalisation preserves one chronology;
9. deleting one IMAGE Fragment leaves Image and other reference intact;
10. referenced `DeleteImage` returns conflict and leaves file/row/topic unchanged;
11. after the last reference is removed, the existing 0030 deletion succeeds;
12. attach-vs-delete concurrency cannot produce a dangling reference.

### Schema validation

Run Hibernate/JPA with:

```text
hibernate.hbm2ddl.auto = validate
```

against the migrated fixture so the new `Fragment.image` mapping is proved compatible with the real schema.

### Completion criterion

The core behaviour has been proven against the real PostgreSQL constraint/locking model rather than mocks alone.

---

## Step 12 — Verify retained MQTT replay and live RPC end to end

**Complete - 2026-09-27.** Live MQTT create/lock/edit/normalise/delete and fresh-context startup reconciliation passed. Fixed explicit-null Image RPC decoding discovered on the wire. See [Step 12 evidence](evidence/Step%2012/README.md), whose authoritative run is `final-run`.

Use a disposable development stack with real responder RPC dispatch, PostgreSQL and Mosquitto.

### 12.1 Create a controlled IMAGE Fragment

Through `addImageFragment`, create:

```text
Page P
Image I
IMAGE Fragment F -> I
```

Verify database state:

```text
fragment.id       = F
fragment.page_id  = P
fragment.type     = IMAGE
fragment.image_id = I
no marquee for F
```

Verify retained state:

```text
diaries/fragments/F
diaries/dates/<year>/<month>/<day>/F
```

both contain:

```text
pageId = P
type = IMAGE
imageId = I
marqueeId = null
```

and the Image catalogue topic remains:

```text
diaries/images/I
```

### 12.2 Edit the IMAGE Fragment

Lock F and exercise:

- text change;
- sequence change;
- date change;
- Image replacement;
- Image clearing;
- Image reattachment.

Verify old date-topic tombstones and new retained aliases exactly match the committed database row.

### 12.3 Mixed chronology

Create MARQUEE and IMAGE neighbours on one date, reorder/normalise them and verify the database and retained date tree have the same order/sequence values.

### 12.4 Delete the IMAGE Fragment

Delete F and verify:

```text
Fragment row absent
Fragment retained topics absent
Image row still present
Image retained topic still present
physical Image file still present
```

### 12.5 Replay after restart

Restart/rebuild retained state from the database and verify remaining IMAGE fragments are recreated with the correct `imageId` and no synthetic Marquee requirement.

### Completion criterion

The real MQTT RPC + PostgreSQL + retained-topic path works through create, lock, update, normalise, delete and restart for mixed Fragment types.

---

## Step 13 — Introduce a safe deployment/authoring gate

**Complete - 2026-09-27.** Added default-disabled `imageFragmentWritesEnabled`, controlled 403 authoring rejection, explicit disposable-fixture enablement, and verified lifecycle/replay preservation over real MQTT/PostgreSQL. See [Step 13 evidence](evidence/Step%2013/README.md).

0025 capability may be deployed before the reader/client features which make production IMAGE content safe to create.

Because the registered MQTT RPC could otherwise be invoked manually by an authorised editor, add an explicit responder configuration gate unless deployment access control already provides an equivalent hard guarantee.

A suitable configuration property is conceptually:

```text
imageFragmentWritesEnabled
```

with a safe default of:

```text
false
```

### Gate scope

When disabled, reject operations which would introduce/change an IMAGE relationship, specifically:

```text
addImageFragment
IMAGE imageId mutation through updateFragment
```

Existing IMAGE rows, once they legitimately exist, must still be:

- replayed;
- readable;
- lockable/unlockable;
- safely deletable if operationally required.

Do not make the read/replay path depend on the write feature flag.

### Environments

Enable the gate in disposable development/integration configuration for 0025 testing.

Keep production disabled until:

1. 0025 responder is deployed and validated;
2. 0026 diaries-web reader support is deployed and verified;
3. 0027 explicitly begins the ImageFragment authoring rollout.

If a configuration flag is added, update responder configuration documentation and deployment templates/examples so an absent property never accidentally means enabled.

### Completion criterion

Deploying 0025 cannot accidentally introduce production IMAGE rows before the reader prerequisite is ready.

---

## Step 14 — Full responder regression and compatibility verification

**Completed 2026-09-27.** Full responder/web tests and builds, client tests/production build, four selected PostgreSQL/MQTT cases and deployed client/web nullable-field parsing checks passed. See [Step 14 evidence](evidence/Step%2014/README.md) for counts, skips, scope and artifacts.

Run the complete responder test suite and build after all 0025 code is assembled.

At minimum verify:

```text
./gradlew :diaries-responder:test
./gradlew :diaries-responder:build
```

or the equivalent Windows Gradle commands used in the project.

Also run the environment-gated PostgreSQL/MQTT integration fixtures required by Steps 11 and 12.

### Regression focus

Review failures specifically for accidental changes to:

- existing MARQUEE creation/editing;
- lock expiry/ownership;
- date alias publication;
- sequence normalisation;
- startup retained replay;
- Image catalogue upload/reconciliation;
- 0030 `DeleteImage` recovery paths;
- generic `DeleteFile` catalogue protection;
- authentication/status mappings.

### Client/web compatibility sanity check

Even though 0025 does not implement client/web UI changes, verify that the currently deployed consumers tolerate the additive `imageId` field on MARQUEE retained Fragment payloads.

No consumer should fail merely because:

```json
"imageId": null
```

is now present.

### Completion criterion

All responder tests/builds pass, database/MQTT integration passes, and existing consumer parsing remains compatible with the additive retained field.

---

## Step 15 — Development deployment, controlled validation and close-out

### 15.1 Apply schema before responder binary

**Completed for development 2026-09-27.** The Step 2 schema was already installed on `diaries-development-db` / `diaries`; fresh preflight/postflight and schema inspection passed. Backup and responder candidate identity are recorded in [15.1 evidence](evidence/Step%2015/15.1/README.md). No reapply or responder start was performed; later Step 15 substeps remain open.

Because the new responder mapping/repository expects `fragment.image_id`, apply and verify the 0025 additive migration before starting the new responder build against that database.

Record:

- database backup/restore point;
- preflight output;
- migration output;
- postflight output;
- responder version/commit;
- schema version/evidence.

### 15.2 Deploy responder with production ImageFragment writes disabled

Deploy the responder capability and verify normal MARQUEE operation first.

Smoke-test:

- sign-in;
- existing day/page reads;
- create/edit/delete MARQUEE in a controlled development environment;
- Image upload/catalogue behaviour;
- unreferenced Image deletion;
- generic `DeleteFile` protection.

### 15.3 Controlled IMAGE validation

In a non-production or explicitly controlled test environment with the write gate enabled, repeat the Step 12 create/edit/delete/replay flow.

Preserve evidence of:

```text
DB Fragment row
DB Image row
absence of Marquee for IMAGE
retained Fragment payload
retained Image payload
reference-aware DeleteImage conflict
successful DeleteImage after final reference removal
```

### 15.4 Update change-control records

Update `README.md` and this document with:

- exact changed files;
- test/build totals;
- migration evidence;
- integration evidence;
- any design deviations;
- exact `updateFragment.imageId` semantics;
- the chosen attach/delete locking protocol;
- the production write-gate state;
- known limitations deferred to 0026/0027/0028/0029.

### 15.5 Close only when acceptance criteria are evidenced

Do not move 0025 to `complete` merely because it compiles.

The feature is complete when the responder capability, persistence integrity, retained contract and Image deletion protection have all been demonstrated.

---

## Expected source-file scope

The exact final list may vary slightly as implementation proceeds, but the current source indicates the following primary scope.

### New responder source

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddImageFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ResolvedFragmentState.java
```

`ResolvedFragmentState.java` replaces `FragmentAndMarquee.java` if the generalisation is implemented by rename/replacement rather than by modifying the existing class.

### Existing responder source likely to change

```text
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/Responder.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/config/Config.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/model/Fragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentDBDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/dto/FragmentPublishDTO.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repository/FragmentRepository.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImpl.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/DiaryContext.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentLocking.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliser.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueService.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/LockFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UnlockFragment.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/NormaliseFragments.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/AddMarquee.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/UpdateMarquee.java
diaries-responder/src/main/java/com/rsmaxwell/diaries/responder/handlers/DeleteImage.java
```

`DeleteMarquee.java` should also be reviewed; it only needs a source change if the chosen invalid-state repair policy requires an explicit type guard.

### Migration/change-control files

```text
change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/migration/...
change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/IMPLEMENTATION-STEPS.md
change-control/in-progress/0025-FEAT - add responder ImageFragment persistence and RPC/README.md
```

### Test scope likely to change/add

```text
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/repositoryImpl/FragmentRepositoryImplTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/dto/RetainedStateDtoContractTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/DiaryContextTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/FragmentSequenceNormaliserTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageCatalogueDeletionTest.java
diaries-responder/src/test/java/com/rsmaxwell/diaries/responder/utilities/ImageDeletionConcurrencyTest.java
```

plus new focused handler/database/MQTT integration tests for `AddImageFragment` and IMAGE-aware `UpdateFragment`.

---

## Final acceptance checklist

0025 can be considered complete when all of the following are evidenced:

- [ ] `fragment.image_id` exists as a nullable indexed FK to `image(id)`.
- [ ] Database constraints prevent a non-null Image reference on a non-IMAGE Fragment.
- [x] `Fragment`, persistence DTO and repository round-trip `imageId` correctly.
- [x] `FragmentPublishDTO` publishes explicit `imageId` on both retained Fragment aliases.
- [ ] `addFragment` remains backward-compatible MARQUEE creation.
- [ ] `addImageFragment` creates IMAGE with no Marquee.
- [ ] IMAGE may have zero or one existing Image reference.
- [ ] One Image may be reused by multiple IMAGE Fragments.
- [ ] Ordinary `updateFragment` cannot change `type` or authoritative Page ownership.
- [ ] IMAGE Image selection/removal obeys the existing Fragment lock/version transaction.
- [ ] MARQUEE cannot acquire an Image through responder operations.
- [ ] IMAGE cannot acquire a Marquee through responder operations.
- [ ] Lock/unlock works for both types without requiring a Marquee.
- [ ] Mixed MARQUEE/IMAGE sequence normalisation produces one correct chronology.
- [ ] Deleting an IMAGE Fragment removes only the Fragment and leaves the Image untouched.
- [ ] A referenced Image cannot be deleted and returns a controlled conflict.
- [ ] Attach-vs-DeleteImage concurrency cannot create a dangling reference.
- [ ] Generic `DeleteFile` still cannot bypass Image catalogue/reference integrity.
- [ ] After the final Fragment reference is removed, existing 0030 `DeleteImage` still completes its recoverable file/database/MQTT lifecycle.
- [ ] Database replay recreates IMAGE retained Fragment state correctly after restart.
- [ ] Existing MARQUEE retained payloads remain compatible apart from the additive `imageId: null` field.
- [ ] Full responder tests/build pass.
- [ ] Real PostgreSQL integration tests pass.
- [ ] Real MQTT retained/RPC development verification passes.
- [ ] Production ImageFragment writes remain disabled until 0026 has been deployed and verified.
- [ ] Change-control evidence records exact files, commands, results and any deviations.

## Explicitly deferred work

The following are **not** part of 0025:

```text
0026 - diaries-web IMAGE rendering
0027 - diaries-client IMAGE creation/editing UI
0028 - reviewed legacy embedded-image data conversion
0029 - final destructive constraints, Marquee page_id removal and retained-contract cleanup
```

0025 should leave each of those later features with a stable responder/database contract rather than attempting to absorb their scope.
