# 0031 Step 2 — Rollback mapping

This document records the **pre-feature configuration mapping** so later implementation has an explicit rollback reference. It is not an instruction to re-share divergent mutable data blindly.

## Pre-0031 mapping

Before isolation, the durable mappings frozen by Step 1 are:

```text
normal common local database: ./data/database/common
local mutable Files:          .../diaries-content/files

production database:          diaries-db-data / database diaries
production mutable Files:     .../diaries-content/files
```

Thus both independent database datasets use the same mutable physical tree:

```text
LOCAL DB ------+
               +---- .../diaries-content/files
PRODUCTION DB -+
```

For the committed local defaults, the equivalent old selector was also effectively `files` because the Compose mounts were hard-coded to `${DIARIES_NAS_CONTENT_PATH}/files`.

## Configuration rollback values

The old local/runtime mapping can be represented conceptually as:

| Dataset/mode | Database selection | Pre-feature Files selector |
| --- | --- | --- |
| common local | `./data/database/common` | `files` |
| development-infrastructure default | `./data/database/development-infrastructure` | `files` |
| local-docker-build default | `./data/database/local-docker-build` | `files` |
| local-published-smoke default | `./data/database/local-published-smoke` | `files` |
| production | `diaries-db-data` / `diaries` | `files` |

Production remains at `files` in the target mapping, so production itself does not require a directory-name rollback.

## When this rollback is safe

Reverting non-production to the old shared tree is safe only while one of these conditions is true:

1. no independently isolated Files root has been mutated; or
2. the operator has deliberately reconciled the selected database against the shared root and has a verified matched backup/restore plan; or
3. mutable Image/File lifecycle operations are disabled and the shared tree is being used only temporarily for controlled recovery/inspection.

## When this rollback is unsafe

After production and non-production Files roots have changed independently, simply setting local `DIARIES_FILES_DIR=files` would reintroduce a cross-dataset mutable store and can immediately recreate the defect addressed by 0031.

Do **not**:

```text
copy only one side and assume the database still matches
merge divergent Files roots automatically
delete an isolated copy before reconciliation/evidence is complete
repoint an independent database to another dataset's Files root for destructive testing
```

If the normal three-mode local sharing is restored after a local rollback, restore both sides together:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The approved common-local pair remains the safe local target even though the pre-feature tree was `files`.
