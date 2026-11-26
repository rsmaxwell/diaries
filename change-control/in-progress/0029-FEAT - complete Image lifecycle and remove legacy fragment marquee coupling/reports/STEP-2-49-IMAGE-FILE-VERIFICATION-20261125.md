# 0029 Step 2 — catalogue file verification before isolated migration rehearsal (2026-11-25)

Status: **PENDING EXECUTION**. This package makes **no database connections**, performs **no file modifications within the Files root**, and does **not** implement a migration.

## Basis

- Latest accepted 49-row provisional placement manifest and development read-only gate: 49/49 PASS, migration approval still PENDING.
- 0028 `MigrationStore.checkCatalogue` requires the catalogue-relative path and expected database SHA-256 to match the actual image file SHA-256.
- 0029 `step2-hybrid-schema-and-data.sql` deliberately aborts on 49 additional development-only Page-less Fragments; do not weaken or execute it on live development.
- The 0028 71-conversion migration tool is intentionally limited to reviewed source scope and must not be blindly reused for these 49.

## Procedure

Run from **Windows Cygwin Bash** after applying this ZIP at the Diaries parent repository root. Supply the *Files root* that contains diary directories, for example a mounted `/cygdrive/p/.../diaries-content/files` if that is how the local files are exposed. Verify the path before running; do not guess. Command:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
FEATURE="change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling"
bash "$FEATURE/tools/step2-49-audit-files.sh" "/cygdrive/p/<verified-path>/diaries-content/files"
```

The audit hashes each catalogue-relative file (49 source occurrences, 48 distinct Image IDs) and resolves each legacy HTML src relative to its diary directory. The report records when the old relative path and catalogue path resolve to the *same* file; this is a useful path consistency check but **not proof that original historical image bytes were preserved**. This distinction is especially important for previously corrected Hermitage Image 18 and St Isaac's Image 25.

All statuses must be `SHA256_PASS` before a file-backed migration can be considered. The Python script fails on missing/mismatching/unreadable files or an unsafe path, and refuses to overwrite existing evidence. It does not approve destination Pages or conversions.

## Subsequent isolated DB rehearsal gate

1. Preserve the unmodified 49 original HTML rows and reviewed mapping; record exact parent/submodule Git revisions and local state.
2. Verify *actual* backup/restore process and isolation before altering any DB: new database instance, separate storage, no shared live volume, no MQTT connection, and no active responder pointing to the isolated instance.
3. Obtain documented assignment/content approval (including 611–613 proposed Page 756 and 84 existing link) and historical image equivalence exceptions.
4. Implement or extend the existing 0028-reviewed journal mechanism for precisely these 49, with immutable source HTML identity, destination Page and Image SHA-256 checks, explicit approval, rollback and receipts. Do not silently convert all 49 or run the production-shaped schema SQL.
5. Rehearse conversion and 0029 hybrid migration in that isolated instance; compare chronology, HTML captions/links, Marquee ownership, nine annual preambles, two dated commentary rows and rollback snapshot.

Keep Step 2 OPEN. No migration or production deployment is authorised by this audit.
