# Fragment 566 development-version selection

Status: **committed and verified on production on 2026-09-24**.

The live comparison proves that development and production have identical row
counts and canonical row digests for Diary, Image, Marquee, Page and Person.
All six identity-sequence states also match. The Fragment table excluding ID
566 has the same 2,328-row digest. For Fragment 566, every field other than
`version` and `text` matches.

Development contains the selected value at version 2 with text digest
`cb2269f86054079dbc29cf3eebb0d115`. Production contains version 3 with text
digest `88028219b08dd39f500e7ede406e3949`.

`correction.sql` is a serializable, guarded one-row transaction. It requires
the exact current production Fragment count, complete digest, unaffected-row
digest, version, text digest and non-text digest. It writes the exact UTF-8
development text bytes, restores version 2 and requires the complete resulting
Fragment digest to equal development before commit.

Fresh production backups were created before preparation:

- `diaries-production-20260924-085453.sql`;
- `diaries-production-20260924-085454.dump`.

`backup-sha256.txt` records their hashes. The SQL backup was restored into a
disposable PostgreSQL 18 container; the custom backup was successfully listed;
and the correction was executed against the disposable restore. The resulting
six table digests and six sequence states exactly match development, as recorded
in `test-after-state.txt`.

A whole-database restore is unnecessary for this selection and would replace
the production database instance to change two fields in one row.

## Production result

The guarded transaction committed exactly one update at
`2026-09-24T10:40:29Z`. Fragment 566 is now version 2 with text digest
`cb2269f86054079dbc29cf3eebb0d115`. Its non-text-field digest remains
`750ba4e3a7b2b6ce753593aa14ec5c0b`.

Post-commit verification confirms that all six application-table digests and
all six identity-sequence states now match development. Production application
writers remained stopped.

`production-before-state.txt`, `production-transaction.log`,
`production-after-state.txt`, `production-post-verification.txt` and
`production-summary.json` are the authoritative live execution evidence.
