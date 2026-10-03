# 0031-FEAT final effective dataset/Files path map

## Isolated committed defaults

| Local mode | Database selector | Mutable Files selector | Runtime/public contract |
| --- | --- | --- | --- |
| `development-infrastructure` | `./data/database/development-infrastructure` | `files-development-infrastructure` | direct responder resolves `<diaries.root>/files-development-infrastructure`; public URL remains `/files/...` |
| `local-docker-build` | `./data/database/local-docker-build` | `files-local-docker-build` | `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}` -> `/data/files`; public URL remains `/files/...` |
| `local-published-smoke` | `./data/database/local-published-smoke` | `files-local-published-smoke` | `${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}` -> `/data/files`; public URL remains `/files/...` |

## Normal intentionally shared local override

The ignored `local.env` is applied **after** the selected mode environment. When it supplies:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

all three local launch modes intentionally resolve to the same durable dataset:

```text
./data/database/common <-> files-development-common
```

They may still have separate local MQTT brokers/runtime state. That retained state is rebuildable and is not part of the durable pair.

Removing both common override keys returns each mode to its committed isolated pair. Overriding only one key is rejected by `validate-dataset-pair.ps1`.

## Production

Production is independent:

```text
production PostgreSQL dataset <-> diaries_files_dir: files
```

Ansible renders:

```text
DIARIES_FILES_DIR=files
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR} -> /data/files
```

The original scan tree remains separately shared/read-only:

```text
${DIARIES_NAS_CONTENT_PATH}/diaries -> /data/diaries:ro
```

Production does not consume local `local.env`.

## Stable identities

Physical selectors such as `files-development-common` are deployment configuration, not application identity. They must not appear in `Image.relativePath`. The responder-facing Docker path remains `/data/files`, and browser URLs remain `/files/...`.
