# 0031-FEAT — Step 9 close-out

**Decision:** COMPLETE — 2026-10-02

Step 9 — **Reconcile each independent effective database against the existing shared Files tree** — is closed.

Both independent effective database datasets were reconciled in read-only/dry-run mode against the frozen pre-split shared `files` tree while the mutable responder write paths remained frozen:

```text
local common database -> shared files
production database   -> shared files
```

The three local launch modes were correctly treated as one durable dataset because their effective `local.env` configuration selects the same `./data/database/common` database and `files-development-common` target pair.

## Local `common` reconciliation

Runtime evidence:

```text
runtime/local-common-20261002-151207-console.txt
runtime/local-common-20261002-151207-exception-review.txt
```

The run recorded:

```text
Image rows:                  85
Matching physical files:     85
Missing physical files:      0
Untracked physical files:     4
Untracked supported images:  0
Unsupported physical files:  4
Metadata/checksum conflicts: 0
Conflict rows:               0
.image-staging files:        1
```

The dry-run completed successfully. The wrapper reconciled the effective `common` database against the old shared `files` tree rather than the future `files-development-common` target.

## Production reconciliation

Runtime evidence:

```text
runtime/production-20261002-153306-console.txt
runtime/production-20261002-153306-exception-review.txt
```

The production run recorded the same reconciliation counts:

```text
Image rows:                  85
Matching physical files:     85
Missing physical files:      0
Untracked physical files:     4
Untracked supported images:  0
Unsupported physical files:  4
Metadata/checksum conflicts: 0
Conflict rows:               0
.image-staging files:        1
```

The production helper ran the existing 0024 reconciliation in dry-run mode against the deployed production database while the normal responder remained stopped. Its generated report explicitly recorded `DRY_RUN_COMPLETE` and stated that it did not apply the 0024 create plan, mutate Image rows, or change Files bytes.

## Exception review

The same four unsupported physical files were reported by both datasets, with identical paths, byte sizes and SHA-256 hashes. All four are `Thumbs.db` Windows thumbnail-cache files.

Both datasets also reported the same single staging entry: zero-byte `.image-staging/catalogue.lock` with the SHA-256 value for an empty file.

These findings are explicitly dispositioned in [`DISPOSITION.md`](DISPOSITION.md):

- the four `Thumbs.db` files are accepted as non-application metadata;
- `.image-staging/catalogue.lock` is accepted as transient/control state;
- no database repair is required;
- no mutation of the frozen shared Files tree is required; and
- the lock file must not be blindly propagated into the new local Files root merely because it exists in the rollback snapshot.

The generated scripts reported `REVIEW REQUIRED` because they intentionally cannot make these semantic decisions automatically. The reviewed disposition above satisfies that gate; the raw `step10Ready=false` value from those runs is therefore not an unresolved blocker.

## Completion decision

Step 9 is complete because:

- every independent effective database dataset was reconciled separately against the frozen pre-split shared Files tree;
- both runs completed in dry-run/read-only mode;
- each database contains 85 catalogued Image rows;
- all 85 catalogued Images have matching physical files for both datasets;
- neither dataset has a missing physical file;
- neither dataset has an untracked supported Image file;
- neither dataset has a metadata/checksum conflict;
- neither dataset has a reconciliation conflict row;
- the only four untracked/unsupported files are identical `Thumbs.db` caches and have an explicit reviewed disposition; and
- the only staging entry is the identical empty `catalogue.lock` and has an explicit reviewed disposition.

The shared Files tree is therefore understood relative to both independent databases, and no unexplained mismatch needs to be carried into the storage split.

## Operational hand-off

Keep both responder write paths frozen while beginning Step 10. Step 10 may now create/seed the candidate `files-development-common` root from the verified frozen source tree, applying the Step 8/Step 9 staging disposition rather than blindly copying transient recovery/control state.

**Next implementation step:** Step 10 — create one Files root per independent non-production database dataset.
