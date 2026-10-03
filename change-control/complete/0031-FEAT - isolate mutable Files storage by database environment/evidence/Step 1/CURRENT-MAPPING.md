# 0031 Step 1 — Current effective dataset/storage map

This table distinguishes committed mode defaults from the **effective durable dataset identity**. The three local modes are treated as one logical database dataset because the current ignored `local.env` selects `./data/database/common` after the mode-specific environment has been loaded.

| Mode | Committed DB storage default | Effective DB dataset | Database runtime / name | Effective Files selector | Physical mutable Files root | MQTT broker / namespace | Sharing classification |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `development-infrastructure` | `./data/database/development-infrastructure` | `./data/database/common` | container `diaries-development-db`; host port `5433` by default; database `diaries` | developer-owned `%USERPROFILE%\.diaries\responder.json`; current documented Files child is `files` | same physical NAS `photo/.../diaries-content/files` tree as the Docker local modes; Windows host path is machine-local and intentionally not copied | `diaries-development-mqtt`; retained volume `diaries-development-mqtt-data`; application topics `diaries/#`, sync topics `diaries-sync/#` | intentionally shares DB + Files with the other two local modes; **accidentally shares Files only with production** |
| `local-docker-build` | `./data/database/local-docker-build` | `./data/database/common` | container `diaries-local-db`; responder reaches service `diaries-db:5432`; database defaults to `diaries` | implicit Compose mount `${DIARIES_NAS_CONTENT_PATH}/files -> /data/files` | `//nas.localdomain/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files` | `diaries-local-mqtt`; retained volume `diaries-local-mqtt-data`; `diaries/#`, `diaries-sync/#` | intentionally shares DB + Files with the other local modes; **accidentally shares Files only with production** |
| `local-published-smoke` | `./data/database/local-published-smoke` | `./data/database/common` | container `diaries-published-smoke-db`; responder reaches service `diaries-db:5432`; database `diaries` in the current local dataset convention | implicit Compose mount `${DIARIES_NAS_CONTENT_PATH}/files -> /data/files` | `//nas.localdomain/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files` | `diaries-published-smoke-mqtt`; retained volume `diaries-published-smoke-mqtt-data`; `diaries/#`, `diaries-sync/#` | intentionally shares DB + Files with the other local modes; **accidentally shares Files only with production** |
| `production` | not a host bind; Compose named volume `diaries-db-data` | production `diaries-db-data` dataset | responder host `diaries-db:5432`; database `diaries` (also identified by the included production dump) | implicit Playbooks Compose mount `${DIARIES_NAS_CONTENT_PATH}/files -> /data/files` | production NAS content root + `/files`; current 0031 baseline identifies this as the same physical `.../diaries-content/files` tree used by local modes | production service `diaries-mqtt`; retained volumes `diaries-mqtt-data`/`diaries-mqtt-log`; `diaries/#`, `diaries-sync/#` | database is intentionally separate; **Files root is accidentally shared with the local dataset and violates the invariant** |

## Dataset-level view

The mode table reduces to two durable database datasets before 0031:

```text
LOCAL DATASET
  database: ./data/database/common
  modes: development-infrastructure, local-docker-build, local-published-smoke
  mutable Files: .../diaries-content/files

PRODUCTION DATASET
  database: production Compose volume diaries-db-data / database diaries
  mode: production
  mutable Files: .../diaries-content/files
```

Therefore:

```text
LOCAL database dataset ------+
                             +---- same mutable Files root   INVALID ACROSS DATASETS
PRODUCTION database dataset --+
```

The three local execution modes are not three datasets when `local.env` selects the common database. Step 2 must choose one Files root for that common local dataset, not one Files root per local mode merely because three mode files exist.
