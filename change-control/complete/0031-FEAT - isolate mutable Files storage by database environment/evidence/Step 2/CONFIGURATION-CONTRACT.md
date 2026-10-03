# 0031 Step 2 — Frozen configuration contract

## Local/runtime selector

The approved selector is:

```text
DIARIES_FILES_DIR
```

Its value is a single mutable Files **leaf directory beneath the Diaries content root**.

Approved values in the target topology are:

```text
files
files-development-infrastructure
files-local-docker-build
files-local-published-smoke
files-development-common
```

For Docker-based modes the physical source resolves as:

```text
${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR}
```

and is mounted at the stable responder path:

```text
/data/files
```

For direct Windows development, the same effective leaf selector must become the responder's effective `diaries.files` value beneath the developer-owned configured root.

## Playbooks selector

The approved Diaries role variable is:

```text
diaries_files_dir
```

Production is expected to supply:

```yaml
diaries_files_dir: files
```

and the generated runtime environment is expected to contain:

```text
DIARIES_FILES_DIR=files
```

The role must not depend on an implicit fallback to `files` when the variable is absent.

## Paired local override rule

When `local.env` deliberately changes durable database identity, Files identity must follow it.

Approved normal common-local pair:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The two settings form one logical override. Subsequent implementation should fail clearly when tooling can determine that only one side of an intended pair has been overridden.

## Valid examples

Independent local mode:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/local-docker-build
DIARIES_FILES_DIR=files-local-docker-build
```

Common local dataset:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Production:

```text
database dataset: production diaries-db-data
DIARIES_FILES_DIR=files
```

## Invalid examples

Common local database with production Files:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files
```

Independent local database with the common-local Files root:

```dotenv
DIARIES_DB_DATA_DIR=./data/database/local-published-smoke
DIARIES_FILES_DIR=files-development-common
```

Separate local databases all mutating one common Files root are also invalid unless those databases are deliberately replaced by the same effective database dataset.

## Contracts not changed by storage selection

The following remain stable regardless of `DIARIES_FILES_DIR`:

```text
shared original scans: .../diaries-content/diaries
Docker logical mount:  /data/files
HTTP URL prefix:       /files/
Image.relativePath:    relative path within the selected Files root
```

`DIARIES_FILES_DIR` is configuration/deployment metadata. It must not become part of Image domain identity.
