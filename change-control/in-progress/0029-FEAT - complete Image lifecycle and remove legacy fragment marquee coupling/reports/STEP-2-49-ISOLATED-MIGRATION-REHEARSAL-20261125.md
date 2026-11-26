# 0029-FEAT Step 2 — guarded isolated migration rehearsal

## Scope

This package implements a **simulation on an ephemeral, network-isolated PostgreSQL 18 container**; it does NOT authorise or apply a live database migration. It streams a logical backup from the Compose development database with `pg_dump` and restores it only to the temporary container. No port is published and no responder is started. The temporary container is removed on exit.

It requires the already-applied 49-record mapping and checksum audit. It embeds that reviewed **provisional** mapping in `step2-49-isolated-conversion.sql` to make the execution reproducible and rejects any drift in source HTML MD5, date, sequence, catalogue ID/checksum and destination Page/Diary. No production-shaped 0029 guard is relaxed.

## Rehearsal logic

* Archive all 49 original Fragment rows in the isolated database, including original HTML and other metadata, and record all 49 source-to-destination receipts.
* Recognise the existing Whitley Park IMAGE Fragment 2338; remove only its redundant legacy source Fragment 84 in the ephemeral clone.
* Convert the other 48 Page-less legacy HTML records into dated IMAGE Fragments on the reviewed provisional Pages, reusing catalogue images; preserve their IDs, dates and sequences. Simplified display HTML uses `<p>` captions for this rehearsal; HTML semantics and editorial placement still require review.
* Require exactly 11 Page-less Fragments after the conversion, then execute the **unchanged** `step2-hybrid-schema-and-data.sql`, which validates the approved 11-row hybrid ownership model.
* Print ownership/chronology validation and receipts for the historical Hermitage, St Isaac's Church, Alexander Nevsky, and two commentary examples.

## Outstanding approval and limitations

This is **not a signed-off 0028 journal migration** and does not write the `migration0028_source` journal. The `migration0029_legacy_image_archive` table is a rehearsal-only substitute, with distinct provenance. Source-HTML preservation, catalogue integrity and provisional destination selection are different checks from formally approved content conversion. The three Alexander Nevsky Page 756 assignments, the other provisional Page assignments, caption semantics, shared sequence collisions and historical original-file bytes require editorial acceptance. Whitley Park existing-link equivalence also remains to be approved.

The temporary database is destroyed at end of run; retain the terminal log under this feature's `evidence/step-2-isolated-rehearsal/`. Do not store a full database dump there unless specifically needed. A successful `pg_restore` is useful evidence, not a full operational restore/rollback test. This script must NOT be used for live deployment.

## Invocation

Windows 11 Cygwin Bash, from the Diaries parent repo:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
FEATURE="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
bash "$FEATURE/tools/step2-49-isolated-rehearsal.sh"
```

Status: **not executed against the user's database**. Step 2 remains OPEN.
