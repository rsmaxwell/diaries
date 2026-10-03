# 0031 Step 2 — Approved final dataset-to-Files-root map

## Common physical content root

For the local Docker modes, the committed NAS configuration identifies the common content root as:

```text
//nas.localdomain/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content
```

The tables below show Files roots as children of `.../diaries-content`. Direct Windows development may expose the same physical NAS content root through a different host path; the selected **leaf directory name** remains the same.

## Committed defaults

These defaults allow each local mode to be run as an independent durable dataset when no `local.env` common-dataset override is applied.

| Mode / dataset | Database dataset | `DIARIES_FILES_DIR` | Mutable Files root | Classification |
| --- | --- | --- | --- | --- |
| production | production Compose volume `diaries-db-data`, database `diaries` | `files` | `.../diaries-content/files` | independent production dataset; existing physical root retained |
| development-infrastructure default | `./data/database/development-infrastructure` | `files-development-infrastructure` | `.../diaries-content/files-development-infrastructure` | isolated local default |
| local-docker-build default | `./data/database/local-docker-build` | `files-local-docker-build` | `.../diaries-content/files-local-docker-build` | isolated local default |
| local-published-smoke default | `./data/database/local-published-smoke` | `files-local-published-smoke` | `.../diaries-content/files-local-published-smoke` | isolated local default |

The three local default database directories are independent datasets. Therefore each has an independent Files root.

## Normal developer effective mapping

The normal developer override intentionally groups the three local execution modes into **one durable local dataset**:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The resulting effective mapping is:

| Mode | Effective database dataset | Effective `DIARIES_FILES_DIR` | Effective mutable Files root |
| --- | --- | --- | --- |
| development-infrastructure | `./data/database/common` | `files-development-common` | `.../diaries-content/files-development-common` |
| local-docker-build | `./data/database/common` | `files-development-common` | `.../diaries-content/files-development-common` |
| local-published-smoke | `./data/database/common` | `files-development-common` | `.../diaries-content/files-development-common` |

This three-mode sharing is intentional and valid because all three modes select the **same database dataset and the same mutable Files root**.

## Shared read-only source material

All modes may continue to use:

```text
.../diaries-content/diaries
```

for original diary scans. That tree is outside mutable Image catalogue lifecycle ownership and remains shared/read-only.

## Dataset-level target view

With the normal common local override in use, the active target topology is:

```text
LOCAL DURABLE DATASET
  database:    ./data/database/common
  Files root:  .../diaries-content/files-development-common
  modes:       development-infrastructure
               local-docker-build
               local-published-smoke

PRODUCTION DURABLE DATASET
  database:    production volume diaries-db-data / database diaries
  Files root:  .../diaries-content/files
  mode:        production

SHARED READ-ONLY SOURCE
  diary scans: .../diaries-content/diaries
```

Therefore:

```text
LOCAL database ---------- LOCAL Files root

PRODUCTION database ----- PRODUCTION Files root

both may read ------------ shared diary scans
```

No mutable Files root crosses the local/production dataset boundary.

## Stable logical/public paths

The physical directory name is not part of persisted or client-visible identity:

```text
Docker responder mount: /data/files
HTTP/static route:      /files/...
Image.relativePath:     unchanged; relative to selected Files root
```

No environment prefix is to be written into `Image.relativePath`.
