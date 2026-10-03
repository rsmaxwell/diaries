# 0031 Step 2 — Final dataset-to-Files-root decision

Completed 2026-10-01.

Step 2 freezes the target durable-storage map and the configuration names that subsequent implementation steps must use. It makes **no runtime or data change**: no NAS directory is created, no file is copied, no database is changed, and no developer or production configuration is rewritten in this step.

The decision is based on the Step 1 frozen baseline and the approved mapping proposed in `IMPLEMENTATION-STEPS.md`.

## Decision

The durable invariant remains:

```text
one effective database dataset <-> one effective mutable Files root
```

The following names are now approved and no longer provisional:

```text
production                      -> files
development-infrastructure      -> files-development-infrastructure
local-docker-build              -> files-local-docker-build
local-published-smoke           -> files-local-published-smoke
common local dataset            -> files-development-common
shared read-only diary scans    -> diaries
```

The **normal developer configuration** intentionally makes all three local modes one logical durable dataset. When it selects:

```text
DIARIES_DB_DATA_DIR=./data/database/common
```

it must also select:

```text
DIARIES_FILES_DIR=files-development-common
```

The modes may share because both durable sides are shared together. Sharing the common database with three different Files roots, or sharing one Files root between the common local database and production, is invalid.

## Configuration contract frozen by Step 2

Local/runtime selector:

```text
DIARIES_FILES_DIR
```

Playbooks role variable:

```text
diaries_files_dir
```

`DIARIES_FILES_DIR` is a **leaf directory name beneath the configured Diaries content root**, not a complete NAS path. Docker therefore resolves the mutable source as:

```text
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

while direct Windows development can apply the same selected value to responder `diaries.files` beneath its already configured root.

This keeps physical storage selection outside Java domain logic and preserves all environment-neutral contracts:

```text
Docker runtime path: /data/files
browser/static route: /files/...
Image.relativePath:   relative to the selected Files root
```

## Production decision

Production keeps its existing mutable directory name:

```text
files
```

and therefore keeps the existing physical production root:

```text
.../diaries-content/files
```

This deliberately places the migration burden on non-production. Production storage does not need to be renamed or moved merely to achieve isolation.

## Evidence

- `FINAL-DATASET-TO-FILES-MAP.md` — approved committed-default map and normal effective common-local map.
- `CONFIGURATION-CONTRACT.md` — approved selector names, value semantics, stable runtime/public contracts, and invalid combinations.
- `RATIONALE.md` — why the common local sharing is intentional and why production retains `files`.
- `ROLLBACK-MAPPING.md` — pre-feature mapping and the conditions under which reverting to it is safe or unsafe.
- `SHA256SUMS.txt` — hashes of the Step 2 evidence files, excluding the checksum file itself.

The current pre-change topology and source anchors remain in `../Step 1/`; Step 2 does not duplicate that evidence.

## Completion assessment

Step 2 is complete because every independent target database dataset has exactly one explicit mutable Files root, the intentionally shared local dataset has one matching common root, the read-only diary source remains explicitly shared, the configuration names are frozen, and the pre-feature rollback mapping is documented.

Implementation of this decision starts at Step 3.
