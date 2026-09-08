# 0028-FEAT - Migrate reviewed legacy embedded-image fragments

## Type

Feature

## Status

To do

## Priority

High

## Opened

2026-09-08

## Summary

Consume the legacy embedded-image candidate inventory produced by 0022 and the Image catalogue reconciliation produced by 0024. Provide a dry-run and reviewed-manifest migration which deliberately converts each approved legacy row into the accepted typed Fragment model without guessing intent or losing production content.

## Background

Some existing Fragment text contains one or more `<img>` elements. Those rows still have legacy Fragment/Marquee structure and currently render because the image URL is embedded in HTML. Detection alone cannot determine whether the row is:

- fundamentally an IMAGE Fragment;
- a real MARQUEE Fragment with a supplementary image;
- malformed, missing or external content;
- an intentional compatibility exception.

The accepted target invariant remains:

```text
MARQUEE Fragment -> optional Marquee, no Image
IMAGE Fragment   -> optional Image, no Marquee
Fragment         -> zero or one Image
Image            -> zero or more Fragments
```

Therefore a legacy MARQUEE containing several embedded images cannot become one IMAGE Fragment with several attachments. It must be reviewed and, where approved, split into separate ordered IMAGE Fragments.

## Preconditions

- 0022 inventory is complete and preserved.
- 0024 reconciliation maps supported Files-root images to stable Image IDs.
- 0025 supports IMAGE persistence, locking, publication and safe Image deletion.
- 0026 web rendering is deployed.
- 0027 client editing is deployed or at least available for correcting migrated rows.
- a production database backup and Files-root snapshot have been restored and rehearsed in a disposable environment.

## Inputs and Preserved Evidence

The migration package must use versioned, reviewable inputs:

```text
0022-fragment-candidates.csv
0024-image-reconciliation.csv
0028-dispositions.csv
```

The disposition manifest must contain at least:

```text
fragment_id
expected_fragment_version
page_id
marquee_id
date
sequence
embedded_image_ordinal
original_src
resolved_image_id
disposition
review_note
reviewed_by
reviewed_at
```

Do not accept a manifest when the live row/version, Marquee relationship, embedded source list or resolved Image differs from the reviewed expectations.

## Allowed Dispositions

### `CONVERT_TO_IMAGE`

Use when the existing Fragment is semantically an image occurrence and its Marquee is only a legacy/artificial anchor.

- preserve Fragment ID, Page, date and sequence;
- set `type=IMAGE` and the approved `imageId`;
- remove the Marquee in the same database transaction;
- remove only the reviewed `<img>` markup from Fragment text;
- retain meaningful accompanying text as the IMAGE Fragment text;
- increment/version the Fragment according to the approved migration policy;
- publish the Fragment update and Marquee tombstone after commit.

This disposition is valid only when the candidate resolves to zero or one intended Image. A null Image is permitted only if explicitly reviewed and justified.

### `SPLIT_MARQUEE_AND_IMAGE`

Use when the existing Fragment is a genuine transcription/source fragment but also contains supplementary images.

- preserve the original Fragment ID, Page, Marquee, date and non-image text;
- classify/retain the original as `MARQUEE` with `imageId=null`;
- remove only the approved embedded `<img>` markup;
- create one new `IMAGE` Fragment for each approved image;
- each new Fragment references exactly one Image and has no Marquee;
- place new fragments immediately after the original in embedded-image order;
- normalize all affected sequences deterministically;
- publish every changed/new Fragment after commit.

If useful captions or text are associated with individual images, the reviewed manifest must specify their allocation. The migration must not duplicate the full transcription text onto every generated IMAGE Fragment.

### `KEEP_LEGACY`

Preserve the row, Marquee and HTML unchanged as an explicit compatibility exception. Where the relationship is valid, assign/retain `type=MARQUEE` and `imageId=null`; the embedded HTML is legacy presentation content, not a first-class Image relationship. Record why normalization is inappropriate. A remaining `KEEP_LEGACY` row means the system still intentionally supports legacy inline image markup and final documentation must say so.

### `DEFER`

Make no change. Use for missing files, external URLs, ambiguous matches, undecided semantics or stale inventory. Deferred rows remain an open migration item, block a claim that legacy conversion is complete, and must be resolved before 0029 can enforce any constraint which the row does not satisfy.

## Matching Rules

- normalize relative Files-root paths using the same code/rules as 0024;
- do not match solely by basename;
- prefer exact normalized path;
- checksum may confirm a match but must not silently substitute another historical path;
- record redirects, URL decoding and legacy prefix removal explicitly;
- classify remote HTTP(S), data URLs and unsupported formats separately;
- one catalogued Image may be reused by many conversions;
- ambiguous and missing matches require `DEFER` until reviewed.

## Migration Utility

Implement an explicitly invoked migration utility, not responder startup behaviour. It must support:

```text
analyse/dry-run
validate-manifest
apply
postflight
```

Dry-run output includes planned inserts, updates, deletes, sequence changes, MQTT effects and unresolved candidates. `apply` must be idempotent: rerunning after success reports already-applied outcomes rather than creating duplicate IMAGE Fragments.

Use a migration journal/table or equally durable record mapping each source Fragment/image ordinal to any generated Fragment ID. Execute each candidate as a transaction or use a documented batch transaction boundary that cannot leave a half-split Fragment.

Do not publish MQTT changes before database commit. After apply, run normal responder replay/reconciliation so retained state converges with PostgreSQL.

## Text/HTML Preservation

- archive the complete original Fragment text and a checksum in migration evidence;
- parse HTML with a real HTML parser;
- identify elements by reviewed ordinal/source, not broad string replacement;
- preserve all non-approved nodes, text and formatting;
- canonical serialization changes must be reported;
- sanitise rendered output through the normal consumer policy;
- never remove unresolved embedded images as a side effect of migrating another image in the same Fragment.

## Preflight and Postflight

Preflight verifies:

- every manifest Fragment and version exists;
- Page/Marquee/type state matches expectations;
- every referenced Image exists and its path/checksum matches reconciliation evidence;
- all dispositions satisfy type cardinality;
- generated sequence plan is deterministic;
- no production writer is active during apply.

Postflight verifies:

- original Fragment IDs still exist except where no approved operation permits otherwise;
- conversions have type/image/marquee relationships required by their disposition;
- splits produced exactly the journalled Fragment IDs and count;
- dates and order reconcile;
- unapproved HTML is unchanged;
- every 0022 candidate has one recorded disposition;
- DB and retained entity/topic counts reconcile;
- both applications display representative converted, split and unresolved cases.

## Detailed Implementation Steps

- [ ] Freeze and checksum the 0022 and 0024 input inventories.
- [ ] Build a combined candidate report with exact Image matches and anomalies.
- [ ] Define and review the 0028 disposition manifest schema.
- [ ] Review every candidate manually and record a disposition.
- [ ] Implement HTML parsing/extraction tests for known legacy forms.
- [ ] Implement dry-run and manifest validation.
- [ ] Implement durable idempotency/journal recording.
- [ ] Implement transactional `CONVERT_TO_IMAGE`.
- [ ] Implement transactional `SPLIT_MARQUEE_AND_IMAGE` with deterministic ordering.
- [ ] Implement no-op evidence for KEEP_LEGACY and DEFER.
- [ ] Generate preflight/postflight SQL and reconciliation reports.
- [ ] Test missing, external, duplicate, ambiguous and multi-image cases.
- [ ] Test failure/rollback between every database mutation in a candidate conversion.
- [ ] Rehearse using a restored production backup and copied Files root.
- [ ] Perform client and web visual smoke tests.
- [ ] Preserve the reviewed manifest, journal and reports with change-control evidence.

## Acceptance Criteria

- [ ] Every 0022 candidate has exactly one reviewed disposition.
- [ ] No disposition is inferred automatically from `<img>` presence alone.
- [ ] Every generated IMAGE Fragment references zero or one Image and has no Marquee.
- [ ] Every resulting MARQUEE Fragment has no Image reference.
- [ ] Multi-image legacy content creates separate ordered IMAGE Fragments when approved.
- [ ] Fragment identity, date, sequence and non-image text are preserved according to the reviewed plan.
- [ ] Missing or ambiguous files cause no speculative mutation.
- [ ] Apply is idempotent and detects stale input versions.
- [ ] Database and retained state reconcile after replay.
- [ ] Current client and web render all migrated categories without losing chronology.

## Dependencies

Requires 0022–0027 to be complete and the web reader/editor versions to be deployed. Supplies the evidence needed by 0029 final constraint and cleanup decisions.

## Deployment and Rollback

Stop writers, take a fresh verified database backup and Files-root snapshot, validate the signed-off manifest, run dry-run, compare it with rehearsal output, then apply. Any candidate transaction failure must roll back that candidate completely and stop or clearly quarantine the batch according to the runbook.

Application rollback alone does not undo converted rows. Before destructive cleanup in 0029, database rollback is the pre-migration restore or a separately tested journal-based reverse migration. Preserve original HTML and relationship evidence regardless.
