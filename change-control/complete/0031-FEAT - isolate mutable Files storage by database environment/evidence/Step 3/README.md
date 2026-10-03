# 0031-FEAT — Step 3 evidence

## Step

**Step 3 — Add one paired database/Files override contract to all three local modes**

## Result

**COMPLETE — 2026-10-01**

Step 3 changes only configuration selection and validation. It does not create, copy, rename or delete any physical NAS Files directory and does not mutate any PostgreSQL dataset.

The local configuration contract is now explicit:

| Local mode | committed database default | committed mutable Files default |
|---|---|---|
| `development-infrastructure` | `./data/database/development-infrastructure` | `files-development-infrastructure` |
| `local-docker-build` | `./data/database/local-docker-build` | `files-local-docker-build` |
| `local-published-smoke` | `./data/database/local-published-smoke` | `files-local-published-smoke` |

The machine-local example deliberately overrides both halves together:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The ignored developer-owned `config/environments/local.env` is not present in the source bundle and is not copied into evidence because it can contain credentials. On a machine that already uses the common database override, it must be updated to include the matching `DIARIES_FILES_DIR=files-development-common` setting before running the updated local Docker modes.

## Docker mutable Files mount

Both local Docker responder modes now use:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/${DIARIES_FILES_DIR:?DIARIES_FILES_DIR must be set}
```

for the volume mounted at:

```text
/data/files
```

The `:?` form is intentionally a required-variable guard. There is no `:-files` or equivalent fallback to the old shared/production directory.

The original diary scans remain unchanged and read-only:

```yaml
subpath: ${DIARIES_NAS_CONTENT_PATH}/diaries
```

## Repeatable verification

Run from the Diaries project root:

```text
python scripts/windows/validation/verify-0031-step3.py
```

The verifier checks:

- every committed local mode has the Step 2 approved database and Files defaults;
- applying `local.env.example` second produces the common matched pair for all three modes;
- both local Docker Compose files use the explicit required `DIARIES_FILES_DIR` selector for `/data/files`;
- neither local Docker Compose file retains `subpath: ${DIARIES_NAS_CONTENT_PATH}/files`;
- the shared diary scans continue to use `${DIARIES_NAS_CONTENT_PATH}/diaries`;
- the mutable selector uses Compose required-variable interpolation, so an entirely absent `DIARIES_FILES_DIR` does not silently fall back to `files`.

The captured passing run is in `verification-output.txt`. Hashes of the changed implementation/documentation files are recorded in `SOURCE-SHA256SUMS.txt`.

## Scope boundary

Step 3 does **not** yet make the direct Windows `development-infrastructure` responder consume `DIARIES_FILES_DIR`; that is Step 4. It also does not yet add production/Ansible selection or the stronger half-override mismatch guard; those are later steps in `IMPLEMENTATION-STEPS.md`.

## Changed implementation files

```text
config/environments/development-infrastructure.env
config/environments/local-docker-build.env
config/environments/local-published-smoke.env
config/environments/local.env.example
compose.local-docker-build.yaml
compose.local-published-smoke.yaml
scripts/windows/validation/verify-0031-step3.py
```

Feature documentation is also updated to record Step 3 completion.
