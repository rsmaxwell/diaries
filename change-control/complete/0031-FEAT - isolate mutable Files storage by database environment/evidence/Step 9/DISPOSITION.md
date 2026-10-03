# 0031-FEAT — Step 9 exception disposition

**Reviewed:** 2026-10-02

Step 9 reconciliation completed successfully for both independent effective database datasets against the frozen pre-split shared `files` tree. Both runs reported the same five non-catalogue/staging entries. They are explicitly dispositioned here so the migration may proceed to Step 10 without modifying the pre-split tree.

## Reconciliation result common to both datasets

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

The local run was against the effective `common` database and the frozen shared `files` tree. The production run was against the production database and that same shared tree. The two environments address the NAS differently (`\\nas\photo\...` locally and `//nas.tail636235.ts.net/photo/...` on production), but the exception paths, sizes and SHA-256 values are identical.

## Unsupported physical files

The four unsupported files are Windows Explorer thumbnail caches, not Diaries application content:

```text
diary-1828-and-1829-and-jan-1830/Thumbs.db
  size:   19456
  sha256: 271a4e6b72a249d2ebcca50b03fac1e1c0fdac6bc44191d47cfe018e829e1259

diary-1828-and-1829-and-jan-1830/images/Thumbs.db
  size:   522752
  sha256: b7ecff9fceec44e83568afd83abd31d0fd5ec928f9faee95caecd1d548ef11da

diary-1830/images/Thumbs.db
  size:   136192
  sha256: d5bbb36ec4f96a64ce147f7dd526cd793f2266f8d147c8c03aa38c8ab19c85e8

diary-1832/images/Thumbs.db
  size:   19968
  sha256: 5780ef5250cd8277c3acd10263ded1e89aaa1dab9dbb70e9f8158cd8bc4de4e5
```

**Disposition:** ACCEPTED AS NON-APPLICATION METADATA.

They do not represent catalogued Images, are not supported image files, and do not indicate a database/Files inconsistency. Step 9 does not delete or move them. Step 10 should not rely on them as application data; their presence or omission in a newly seeded non-production Files root is not an Image-catalogue migration requirement.

## `.image-staging` entry

Both runs reported exactly one staging entry:

```text
.image-staging/catalogue.lock
size:   0
sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
```

This is the empty catalogue lock file, not recoverable image payload.

**Disposition:** ACCEPTED AS TRANSIENT/CONTROL STATE; DO NOT BLINDLY PROPAGATE.

The file is retained in the Step 8 rollback snapshot so that rollback remains exact. It is not content that must be copied into the new dataset-specific Files root during Step 10. The target environment may create its own lock/control state when the relevant tooling runs.

## Decision

The non-zero anomaly counts are fully explained. No repair to either database and no mutation of the frozen shared Files tree is required.

The Step 9 completion condition is satisfied because every independent effective database has been reconciled against the shared tree and every reported exception now has an explicit reviewed disposition.
