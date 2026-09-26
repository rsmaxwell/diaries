# Phase 11 production reconciliation — 2026-09-23

This evidence records the production Image catalogue reconciliation performed
on `pluto`. Production application writers remained stopped throughout; only
PostgreSQL and Mosquitto remained running.

## Result

The production database now contains the same 83 Image rows as development.
The final independent reconciliation dry run found:

| Check | Result |
| --- | --- |
| Image rows | 83 |
| `CATALOGUED_MATCH` files | 83 |
| Remaining creates | 0 |
| Metadata conflicts | 0 |
| Candidate cross-reference | 73 of 73 `MATCHED_ONE_IMAGE` |
| Unsupported files | 4 known `Thumbs.db` files |
| Image identity sequence | 83, called |
| Fragment 566 | Development version selected; version 2 |

The final dry run reports `verified: true`, has no conflict rows and records the
reviewed candidate SHA-256
`f12f69cd56797c50dec2fd73ff151de1734ebc15fa54eb2e3ac6ff9a041a43e0`.

## Production sequence

1. A fresh production SQL backup was retained at
   `/home/richard/projects/diaries/data/database-backups/production/diaries-production-20260923-193936.sql`.
   Its SHA-256 is
   `a4a8757d47fe08b1fef374a503c274d376d38bbb9266c494382df6317e8a34c6`.
   It was restored successfully into a disposable PostgreSQL 18 container and
   contained 71 Images plus Fragment 566 at version 3.
2. The two extension corrections were applied together on production. The
   transaction updated Images 65 and 68 and Fragment 1461 while preserving
   Fragment 566.
3. The reviewed reconciliation apply stopped before changing the database. Its
   outcome was `ROLLED_BACK_OR_NOT_APPLIED`, `failureType: IOException` and
   `insertedRows: 0`. The production CIFS mount presented `.image-staging` as
   mode 0755 while the catalogue service requires owner-only mode 0700.
4. The existing production Images 1–71 were proved row-for-row equivalent to
   development with aggregate digest
   `230067aaca271267faba1d1692c69d79`.
5. Images 72–83 were imported from development by a guarded transaction. The
   SQL required the exact 71-row digest, IDs and sequence before inserting. It
   then required the exact 12-row and complete 83-row digests before commit and
   advanced `image_id_seq` to 83. The same transaction was first exercised on a
   disposable PostgreSQL 18 restore.
6. A new production dry run independently compared the database with the Files
   root and produced the zero-create result above.
7. A full live comparison found Fragment 566 to be the sole remaining data
   difference between development and production. Fresh SQL and custom-format
   production backups were created and restore-tested. A guarded one-row
   transaction selected the development text and version on production. The
   final six application-table digests and six identity-sequence states all
   match development.

The targeted Image transaction changed only `public.image` and its identity
sequence. The later Fragment selection changed only the `version` and `text`
fields of Fragment 566. Neither transaction changed files or ImageFragment data.

## Evidence

- `extension-correction-20260923/` contains the guarded extension correction
  SQL, report and manifest.
- `failed-apply-staging-permissions-20260923/` proves the normal apply stopped
  before inserting rows.
- `targeted-image-import-20260923/` contains the guarded SQL, execution runner,
  before and after state, transaction log, backup reference, verification and
  manifest.
- `final-idempotency-dry-run-20260923/` contains the final inventory, empty
  conflict list, zero-create plan, complete candidate cross-reference,
  verification, summary and manifest.
- `fragment-566-development-selection-20260924/` contains the full live
  comparison, fresh backup references, guarded one-row SQL, disposable restore
  test and verified production execution.

Every child evidence manifest was rechecked after copying from `pluto`.

## Remaining production gate

Production storage capability remains unresolved. The CIFS Files mount reports
`dir_mode=0755,file_mode=0755,nounix`, so it cannot currently satisfy the
catalogue service's owner-only staging-directory check. Retained Image replay,
production upload/guard smoke testing and re-enabling normal editing must wait
until the deployment filesystem passes the Phase 11 staging, locking, hard-link
and atomic-move checks.
