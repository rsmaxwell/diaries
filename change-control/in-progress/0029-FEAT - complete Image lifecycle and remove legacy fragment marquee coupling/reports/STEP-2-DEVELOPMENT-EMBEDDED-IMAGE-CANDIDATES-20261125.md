# 0029 Step 2 — 0028 embedded-image candidate reconciliation (25 November 2026)

**State: prepared, unexecuted.** This package is a read-only development diagnostic, not a database migration or a data-deletion approval. Source baseline: diaries-sources-20261125-171359.zip and accepted read-only diagnostic from 17:34 UTC.

## Observed baseline

The local development database contains 60 Page-less Fragments, 11 reviewed for 0029 and 49 additional NULL-type rows. All 49 contain image HTML and none has an `image_id` or Marquee. 0028 migration journal tables are absent. Therefore 0028 status and identity matching are unknown. 2,269 Marquees had no ownership discrepancies.

## Candidate evidence

The script extracts each quoted `<img src=...>` from the 49 legacy HTML records using PostgreSQL regex; shows only the final filename segment, not the full URL; compares against catalogue `image.original_filename` and the basename/suffix of `image.relative_path`, and counts dated IMAGE Fragments on the same calendar day and using any candidate Image ID. It prints all 49 sources even when no src attribute can be parsed. The output is intended to identify which IDs need investigation and to distinguish a possible correspondence from an absent filename candidate.

**No filename, URL path or matching date is proof of identical image bytes, same source Fragment, successful 0028 migration, or safe disposal.** Additional checks will require the 0028 review manifest, receipts, actual image checksums/bytes and destination Fragment identities. The previously accepted 0028 evidence is not included in the latest source bundle, and the 0028 journal tables are absent from this development database. A source HTML URL can differ from a catalogue path even when the image matches; renames and percent-encoding yield false negatives. No record may be classified as definitively migrated using this report alone.

## Run

From Windows Cygwin at the Diaries parent repository root: `bash "change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/step2-development-embedded-image-candidates.sh"`. It checks the standard development Docker Compose environment, runs PostgreSQL in an explicit `REPEATABLE READ READ ONLY` transaction and stores the dated output under `evidence/step-2-development-preflight/`. It does not invoke MQTT, access production, change PostgreSQL, create 0028 journals, or execute the 0029 migration SQL.

## Follow-up

Review the complete per-occurrence output and classify unambiguous candidates vs unmatched/ambiguous. Obtain accepted 0028 migration receipts/manifests from the feature's separate historical evidence before deciding on retirement or transfer of legacy rows. Preserve production-shaped 11-ID guard and the existing database until a reversible rehearsal on an isolated restored database is approved.
