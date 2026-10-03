# 0031 Step 1 — Source anchors

The excerpts below identify the exact source locations used to construct the current mapping. They intentionally omit secrets.

## Committed local database defaults

`config/environments/development-infrastructure.env:1`

```text
DIARIES_DB_DATA_DIR=./data/database/development-infrastructure
```

`config/environments/local-docker-build.env:1,3-5`

```text
DIARIES_DB_DATA_DIR=./data/database/local-docker-build
DIARIES_NAS_CONTENT_PATH=nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content
DIARIES_NAS_HOST=nas.localdomain
DIARIES_NAS_SHARE=photo
```

`config/environments/local-published-smoke.env:1,3-5`

```text
DIARIES_DB_DATA_DIR=./data/database/local-published-smoke
DIARIES_NAS_CONTENT_PATH=nancy-and-ronald-maxwell/documents/sea-captains-chest/diaries-content
DIARIES_NAS_HOST=nas.localdomain
DIARIES_NAS_SHARE=photo
```

## Local override precedence and common dataset

`config/environments/local.env.example:1-8,17`

```text
# Machine-local overrides shared by all three local Diaries modes.
# ... scripts load the mode-specific environment first and local.env second,
# so values here take precedence.
# Using one PostgreSQL data directory means development-infrastructure,
# local-docker-build, and local-published-smoke see the same Diaries database.
DIARIES_DB_DATA_DIR=./data/database/common
```

The launch scripts implement that order directly. For example `scripts/windows/local-docker-build/start.bat` loads `local-docker-build.env` and then `local.env`; `scripts/windows/development-infrastructure/start.bat` does the same for its mode file.

## Local Docker database and mutable Files mounts

`compose.local-docker-build.yaml:5-16,24-39,68-86`

```text
diaries-db container: diaries-local-db
POSTGRES_DB: ${DIARIES_DB_NAME:-diaries}
DB data: ${DIARIES_DB_DATA_DIR}:/var/lib/postgresql
MQTT container: diaries-local-mqtt
MQTT retained volume: diaries-local-mqtt-data
after NAS mount selection:
  ${DIARIES_NAS_CONTENT_PATH}/files -> /data/files (read/write)
```

`compose.local-published-smoke.yaml:6-17,26-41,54-87`

```text
diaries-db container: diaries-published-smoke-db
DB data: ${DIARIES_DB_DATA_DIR}:/var/lib/postgresql
MQTT container: diaries-published-smoke-mqtt
MQTT retained volume: diaries-published-smoke-mqtt-data
after NAS mount selection:
  ${DIARIES_NAS_CONTENT_PATH}/files -> /data/files (read/write)
```

## Direct development responder configuration ownership

`diaries-responder/scripts/windows/run-responder.bat:61-67`

```text
The development responder configuration is stored beneath the current user's profile.
CONFIG_FILE=%USERPROFILE%\.diaries\responder.json
```

`diaries-responder/README.md:204-211`

```json
{
  "diaries": {
    "root": "/path/to/diaries/root",
    "diaries": "diaries",
    "files": "files"
  }
}
```

`diaries-responder/README.md:565-577` is the decisive current-topology statement:

```text
The three local modes use the same database data directory when local.env sets
DIARIES_DB_DATA_DIR=./data/database/common, and their responder configurations
address the same physical NAS Files tree.
...
The development configuration sees the NAS through a Windows path, while the
Docker configurations see /data/files.
```

## Production database and Files mapping

Playbooks `roles/diaries/templates/.env.j2:1-12` renders the production NAS content path and database name into `.env`.

Playbooks `roles/diaries/templates/compose.yaml.j2:50-61` establishes:

```text
production database service: diaries-db
production durable database storage: diaries-db-data:/var/lib/postgresql
```

Playbooks `roles/diaries/templates/config/responder/responder.json.j2:23-25` establishes the responder database endpoint:

```text
host: diaries-db
port: 5432
database: {{ diaries_db_name }}
```

Playbooks `roles/diaries/templates/compose.yaml.j2:112-124` establishes the current production mutable Files mount:

```text
${DIARIES_NAS_CONTENT_PATH}/files -> /data/files (read/write)
```

The included `diaries-production-20260908-174443.dump` contains a PostgreSQL archive database declaration for `diaries`; it is used here only as an additional non-mutating identity anchor. No restore was performed.

## MQTT namespace

`config/mosquitto/aclfile.txt:10-21` grants the responder access to:

```text
diaries/rpc/...
diaries-sync/#
diaries/diaries/#
diaries/pages/#
diaries/fragments/#
diaries/marquees/#
diaries/images/+
diaries/dates/#
diaries/people/#
diaries/roles/#
```

The modes use separate Mosquitto containers/named volumes, so the topic names are shared conventions while retained state is broker-specific.
