I would **not temporarily modify the responder to perform the migration**. I would implement the 0022 data migration as an explicit, repeatable migration utility/script that operates directly on PostgreSQL, with the responder changes only responsible for understanding and maintaining the *new* schema afterwards.

That is the cleaner separation for this particular change.

The reason is that 0022 contains two quite different jobs:

```text
one-off historical transformation
    existing Fragment + Marquee data
    -> populate Fragment.page_id
    -> classify ordinary rows as MARQUEE
    -> identify legacy image candidates/orphans

ongoing application behaviour
    new Fragment creation/update/publish
    -> always maintain page_id and type correctly
```

The first belongs in a migration. The second belongs in `diaries-responder`.

### Why I would avoid a temporary responder mode

A temporary responder migration path would mean adding code whose only purpose is to run once and then be removed. It would also mix operational migration behaviour with normal MQTT/database startup and synchronisation behaviour.

That is particularly risky here because the responder does quite a lot on startup: database loading, retained-state comparison/synchronisation and MQTT publication. You would not want a half-completed migration to coexist with normal synchronisation and accidentally republish partially migrated state.

It would also be harder to answer questions like:

```text
Exactly which rows were classified?
Which image candidates were found?
Which fragments could not resolve a page?
Can I rerun the analysis safely?
Can I review the proposed changes before committing them?
```

A dedicated migration script can make those things explicit.

## I would make it a small migration package, not just one SQL statement

Because of the legacy embedded images, I would probably use **two parts**:

```text
0022 migration
├── preflight / classification utility
├── schema + backfill SQL
└── postflight verification
```

The SQL itself is ideal for the structural part:

```sql
ALTER TABLE fragment
    ADD COLUMN page_id BIGINT;

ALTER TABLE fragment
    ADD COLUMN type VARCHAR(...);
```

and the unambiguous page migration:

```sql
UPDATE fragment f
SET page_id = m.page_id
FROM marquee m
WHERE m.fragment_id = f.id;
```

But classifying legacy `<img>` fragments is easier and safer in a small program than in increasingly elaborate PostgreSQL regular expressions.

I would therefore probably implement a **Java command-line migration utility** in or alongside `diaries-responder`, but crucially **not as temporary responder runtime behaviour**.

Something like:

```text
diaries-responder/
  scripts/
    migrations/
      0022/
        preflight.sql
        migrate.sql
        postflight.sql
```

plus perhaps:

```text
src/main/java/.../migration/Migrate0022.java
```

or a standalone script under the change-control directory.

### Why Java rather than only SQL?

The current fragment `text` is HTML-capable. For identifying legacy image candidates, the migration needs to inspect things such as:

```html
<img src="/files/..." alt="Whitley Park">
```

A Java utility can parse the fragment HTML properly and report:

```text
fragment id
page id
marquee id
image count
src
alt
text preview
classification
```

rather than trying to parse HTML with SQL regexes.

I would use HTML parsing only for **classification/report generation**. It should not modify the fragment HTML in 0022.

The migration utility might produce:

```csv
fragment_id,page_id,marquee_id,classification,image_count,image_src,reason
84,85,92,LEGACY_IMAGE_CANDIDATE,1,/files/.../whitley-park.jpg,"contains img element"
85,85,93,ORDINARY_MARQUEE_CANDIDATE,0,,"no embedded image"
...
```

That becomes valuable evidence before making any changes.

## I would run 0022 in distinct phases

### Phase 1 — backup

Take the normal PostgreSQL backup first.

Given that you recently cleaned the database and established a useful starting datum, I would preserve a backup immediately before 0022.

### Phase 2 — preflight, read-only

Run the migration analyser against the live/restored database without changing anything.

It should verify at least:

```text
total Fragment rows

Fragment with exactly one Marquee
Fragment with no Marquee

Marquee with invalid/missing Page

Fragment containing <img>
Fragment containing >1 <img>

unique /files/... image paths
```

Because `Marquee.fragment_id` is already declared unique in the JPA model, multiple marquees per fragment should not normally occur, but I would still test the real database rather than assume it.

The important output is the list of:

```text
ORDINARY_MARQUEE_CANDIDATE
LEGACY_IMAGE_CANDIDATE
ORPHAN_OR_INCONSISTENT
```

You could inspect the relatively small set of legacy image candidates manually.

### Phase 3 — additive schema

Run explicit SQL:

```text
fragment.page_id nullable
fragment.type nullable
```

and the foreign key for `page_id`.

I would **not depend on Hibernate to alter the schema**. Your 0022 specification already says this, and I agree with it.

The current `persistence.xml` does not contain a managed Flyway/Liquibase migration mechanism, so an explicit migration script is especially appropriate.

### Phase 4 — page backfill

For every Fragment with a valid existing Marquee:

```text
Fragment.page_id = Marquee.page_id
```

This part is deterministic and should be done in SQL.

For example:

```sql
UPDATE fragment f
SET page_id = m.page_id
FROM marquee m
JOIN page p ON p.id = m.page_id
WHERE m.fragment_id = f.id
  AND f.page_id IS NULL;
```

Then compare the affected row count against the preflight count.

### Phase 5 — type assignment

Here I would use the **reviewed classification results**, not simply:

```sql
UPDATE fragment SET type='MARQUEE';
```

For ordinary rows:

```sql
UPDATE fragment
SET type = 'MARQUEE'
WHERE id IN (...approved ordinary IDs...);
```

Legacy image candidates remain:

```text
type = NULL
```

for now.

That makes the data tell the truth: we have not yet decided whether they will ultimately be `MARQUEE` or `IMAGE`.

If there are only a handful of image candidates, I would actually favour a generated SQL file containing the explicit IDs. It makes the migration completely reviewable.

For example:

```sql
-- Generated from 0022 preflight inventory.
-- Reviewed 2026-09-xx.

UPDATE fragment
SET type = 'MARQUEE'
WHERE id IN (
    1,
    2,
    3,
    ...
);

-- Intentionally left unclassified pending Image migration:
-- fragment 84 / Whitley Park
-- fragment 137 / ...
```

### Phase 6 — deploy the new responder

Only **after the schema/data migration** would I start the updated responder.

The new responder should know about:

```java
Fragment.page
Fragment.type
```

and `AddFragment` should explicitly create:

```text
page = requested page
type = MARQUEE
```

so no newly created rows can return to the old ambiguous state.

It should publish the additive:

```json
{
  "pageId": 85,
  "type": "MARQUEE",
  "marqueeId": 92
}
```

while retaining the legacy fields needed by the current client/web.

That is where responder modification belongs: **maintaining the migrated model from now onward**, not migrating old records itself.

## There is one subtle issue with retained MQTT state

After changing the database, retained Fragment topics will still contain the old payload until the responder republishes/synchronises them.

I would deliberately include that in the deployment procedure.

Something like:

```text
1. Stop Diaries stack/responder.
2. Backup DB.
3. Run 0022 preflight.
4. Review inventory.
5. Run schema migration.
6. Run data migration.
7. Run postflight validation.
8. Start updated responder.
9. Let Synchronise rebuild/update retained Fragment payloads.
10. Verify database and retained topic tree agree.
11. Smoke-test existing diaries-client and diaries-web.
```

That avoids modifying data under a running responder.

Given the way Diaries uses PostgreSQL **and** the retained MQTT topic tree as representations of the same domain state, I think stopping the responder during migration is important.

## Where I would store the migration

Because this is tied directly to feature 0022 and is not a generic production service, I would probably put all migration artefacts under the change-control feature itself:

```text
change-control/
  todo/
    0022-FEAT - migrate fragments to explicit page ownership and type/
      README.md
      migration/
        001-preflight.sql
        002-classify-legacy-fragments.*
        003-add-schema.sql
        004-backfill.sql
        005-postflight.sql
        README.md
```

If the classifier is Java, either:

```text
migration/Migration0022.java
```

as a small self-contained utility,

or make it a proper responder-side command line class so it can reuse the responder's PostgreSQL configuration and HTML libraries.

I slightly favour the latter **provided it is invoked explicitly**, for example:

```text
gradlew runMigration0022
```

rather than being called by `Responder.main()`.

That gives you Java's parsing/testability while keeping the migration outside normal responder behaviour.

## So the division of responsibility I recommend is

```text
Explicit migration utility/scripts
----------------------------------
analyse existing records
detect legacy <img> candidates
produce migration report
add columns
backfill page_id
assign reviewed MARQUEE types
verify results


Updated diaries-responder
-------------------------
map Fragment.page
map Fragment.type
create all new AddFragment rows with:
    pageId
    type=MARQUEE
publish additive pageId/type fields
operate correctly after migration
```

I think this is safer than temporarily teaching the responder “if I find an old row, migrate it while starting.”

It also fits your change-control style well: **0022 can carry the exact migration artefacts used on the production database**, so six months later you can see precisely how the old data was transformed.
