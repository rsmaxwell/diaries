# 0031 Step 1 — Redacted effective configuration selections

Only non-secret values relevant to dataset/root identity are recorded. Passwords, tokens, usernames where unnecessary, and the contents of developer-owned responder JSON files are deliberately omitted.

## Local override applied after each mode file

```dotenv
# config/environments/local.env — non-secret selection only
DIARIES_DB_DATA_DIR=./data/database/common
```

Effective precedence:

```text
<mode>.env -> local.env -> effective process/Compose environment
```

This makes all three local modes one durable database dataset.

## Local Docker NAS selection from committed mode files

```dotenv
DIARIES_NAS_HOST=nas.localdomain
DIARIES_NAS_SHARE=photo
DIARIES_NAS_CONTENT_PATH=nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content
```

Current mutable mount in both local Docker Compose files:

```text
${DIARIES_NAS_CONTENT_PATH}/files -> /data/files
```

Canonical physical root:

```text
//nas.localdomain/photo/nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content/files
```

## Direct Windows development responder

```text
configuration file: %USERPROFILE%\.diaries\responder.json
Files child:        files
physical identity:  same NAS Files tree used by the Docker local modes
```

The exact Windows host path is machine-local and is intentionally not copied into evidence. Source documentation explicitly states that the three local responder configurations address the same physical NAS Files tree when the common database override is used.

## Production templates

```text
database service:   diaries-db:5432
database storage:   Compose volume diaries-db-data
database name:      diaries
mutable Files:      ${DIARIES_NAS_CONTENT_PATH}/files -> /data/files
```

The production `DIARIES_NAS_CONTENT_PATH` value itself is supplied by deployment variables outside the source bundle. The existing 0031 feature baseline records the production Files path as the existing `.../diaries-content/files` root, which is the same physical tree currently used by local modes.

## MQTT retained-state identity

Each mode has its own broker/runtime storage, but uses the same application topic conventions:

```text
diaries/#
diaries-sync/#
```

Retained MQTT state is therefore runtime-isolated by broker, not by a different topic prefix. It is rebuildable and is not part of the durable database/Files pair.
