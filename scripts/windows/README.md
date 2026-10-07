# Diaries Windows operating scripts

These scripts operate the three local Diaries modes and their durable PostgreSQL + mutable Files datasets. The central storage rule is:

```text
one effective database dataset <-> one effective mutable Files root
```

Do not infer the effective dataset from the launch mode alone.

## Environment precedence

Each local mode has a committed environment file under `config/environments/`. Supported scripts load that file first and the ignored machine-local `config/environments/local.env` second, so `local.env` wins.

The committed isolated defaults are:

| Mode | `DIARIES_DB_DATA_DIR` | `DIARIES_FILES_DIR` |
| --- | --- | --- |
| `development-infrastructure` | `./data/database/development-infrastructure` | `files-development-infrastructure` |
| `local-docker-build` | `./data/database/local-docker-build` | `files-local-docker-build` |
| `local-published-smoke` | `./data/database/local-published-smoke` | `files-local-published-smoke` |

The normal developer `local.env` may deliberately make all three modes share one durable local dataset:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

These two values are a pair. Never override only one. `scripts/windows/common/validate-dataset-pair.bat` rejects a one-sided override, a crossed approved pair, and local use of the production `files` root.

To restore the isolated committed defaults, remove/comment **both** common selector lines from `local.env` (leaving the file itself in place for credentials and other machine-local settings), or replace both with another deliberate valid matched pair.

## Files selector semantics

`DIARIES_FILES_DIR` is a leaf directory name, not an absolute path. For Docker modes it selects the NAS subtree conceptually represented as:

```text
\\<DIARIES_NAS_HOST>\<DIARIES_NAS_SHARE>\<DIARIES_NAS_CONTENT_PATH>\<DIARIES_FILES_DIR>
```

and that tree is mounted at stable `/data/files` in the responder container. The original diary scans remain a different tree at `${DIARIES_NAS_CONTENT_PATH}/diaries`, mounted read-only at `/data/diaries`.

For direct Windows development, the physical Files root is `<diaries.root>/<DIARIES_FILES_DIR>` from the developer-owned `%USERPROFILE%\.diaries\responder.json` base configuration.

Physical selection never changes the application contract: uploaded/catalogued objects are served as `/files/...`, and `Image.relativePath` remains relative to the selected Files root with no environment prefix.

## Direct Windows responder configuration

`diaries-responder\scripts\windows\run-responder.bat` and `diaries-responder\scripts\windows\migration0024ImageCatalogue.bat` call:

```text
scripts\windows\development-infrastructure\prepare-responder-config.bat
```

That helper:

1. loads `development-infrastructure.env`;
2. loads `local.env` second;
3. validates the effective database/Files pair;
4. reads the developer-owned responder JSON;
5. writes ignored `build\development-infrastructure\responder.effective.json` with only `diaries.files` changed to the effective selector.

This keeps direct development, Docker launch tooling and reconciliation on the same effective storage decision.

## Identify the effective pair before destructive work

The supported start, backup, restore and responder-preparation scripts call the common validation/reporting helpers. Read the printed **Database data**, **Files selector**, and resolved Files-root/NAS information before running upload, delete, rename, apply-mode reconciliation, reset or restore operations.

For an explicit diagnostic from a command shell, load the intended mode environment and `local.env`, then call:

```bat
call scripts\windows\common\validate-dataset-pair.bat MODE config\environments\MODE.env config\environments\local.env
call scripts\windows\common\report-effective-dataset.bat MODE
```

`report-effective-dataset.bat` expects the environment variables already to have been loaded. The normal mode scripts do this for you and are safer than manually assembling environment state.

Do not proceed with destructive Image/File lifecycle testing if the reported database and Files root are not the intended matched pair.

## Choose database-only or complete-dataset backup

Use a **database-only** backup when the task is intentionally limited to PostgreSQL and you are separately controlling the matching Files state, for example a database inspection or tightly-scoped migration rollback. The `.dataset.json` sidecar records the effective Files identity but does not contain Files bytes.

Use a **complete-dataset** backup for disaster recovery, a durable rollback point, before a risky database+Files change, or whenever the backup must be independently recoverable without separately locating a matching Files snapshot. This is the normal full-data protection command.

The complete-dataset boundary is deliberately limited to PostgreSQL durable application data plus the selected mutable Files root. It excludes the shared read-only original diary scans, MQTT retained state (rebuilt from PostgreSQL), Docker/application images, environment files, credentials and external NAS/platform backup policy.

## Backup semantics

The per-mode `backup-db-to-binary.bat` and `backup-db-to-sql.bat` commands are **database-only** backups. They derive their backup namespace from the effective database dataset and write a dataset sidecar describing the matching Files selector/root. They do not copy Files bytes.

A complete recoverable Diaries dataset backup uses the 0033 schema-2 directory contract:

```text
<dataset-backup-root>/<logical-dataset>/<YYYYMMDD-HHmmssZ>/
    dataset-manifest.json
    database/diaries.dump
    database/diaries.sql
    files/
    verification/database.sha256
    verification/files.sha256
    verification/inventory.json
```

An in-progress candidate is named `.<YYYYMMDD-HHmmssZ>.partial` and is deliberately non-restorable. `backup-dataset.bat` in each local mode delegates to the common engine, captures both database formats plus durable Files while writers are quiesced, verifies hashes/inventory, writes the schema-2 manifest and promotes the directory only after successful validation. The existing `backup-db-*` commands remain deliberately database-only.

The writer-quiescence window covers the database dumps, Files capture and final source/media verification. PostgreSQL remains available; known responder writers for the effective pair are stopped. On success only writers that were running before the backup are restored. On failure after quiescence, the safe state is stopped with a non-restorable `.partial` workspace retained for review.

After a completed backup, independently verify the media before relying on it:

```powershell
python .\scripts\windows\common\complete-dataset-manifest.py verify --backup-dir .\data\dataset-backups\<dataset>\<backup-id>
```

The validator rechecks the schema-2 completion markers, component paths, database hashes, exact Files inventory and Files hashes. A successful normal verification must target the promoted directory, never a `.partial` candidate.

Keep the original diary scan tree separate; it is shared read-only source material, not the mutable Files side of this invariant.

## Restore semantics

0033 Step 5 adds a common local complete-restore preparation engine with thin wrappers in all three local modes. The restore input is a **completed complete-backup directory** or its backup ID; an arbitrary `.dump`, `.sql` or `.dataset.json` database-only artifact is not accepted.

Use the non-mutating preflight first:

```bat
restore-dataset.bat preflight YYYYMMDD-HHmmssZ
```

It validates the current effective database/Files pair, the schema-2 manifest and every recorded backup hash/inventory, validates the custom dump with `pg_restore --list`, checks target staging state, checks known free space where Windows can report it, and reports every writer which can reach the target pair. It does not stop writers or create restore work.

Step-5 preparation is then:

```bat
restore-dataset.bat prepare YYYYMMDD-HHmmssZ
```

The command requires the operator to type `RESTORE`. It then quiesces every target writer, rechecks `.image-staging`, creates and independently validates a fresh **complete-dataset safety backup**, copies the selected backup's durable Files into a sibling staging directory, and revalidates that staged tree by exact relative path, size and SHA-256 inventory. Successful preparation leaves writers stopped and records the prior writer-running state under `data\dataset-restores\<dataset>\<backup-id>.prepared\restore-state.json`.

Step 5 deliberately does **not** drop/recreate/restore PostgreSQL and does **not** replace or merge the live Files root. If preparation fails after quiescence, writers remain stopped and the `.preparing` work directory / staged Files directory are retained for diagnosis rather than silently returning the dataset to service.

Step 6 applies an already-prepared restore with:

```bat
restore-dataset.bat apply YYYYMMDD-HHmmssZ
```

The command revalidates the source complete backup, mandatory safety backup, prepared state and staged Files, then requires the exact token `APPLY`. It restores **only** `database/diaries.dump` using the proven drop/recreate/custom `pg_restore --exit-on-error --no-owner --no-privileges` path; `database/diaries.sql` is not applied afterwards. The staged Files directory is promoted by same-parent rename rather than merged: the old live Files root is first renamed to `.<files-leaf>.pre-restore-<backup-id>.rollback`, then the exact staged tree takes the live name. This guarantees that durable files absent from the selected backup do not survive merely because they existed before restore. A new empty `.image-staging` directory is created after the swap; stale staging payloads are never restored.

Successful Step-6 apply ends in `applied-awaiting-step7`. The old live Files directory and mandatory complete safety backup remain present, and **all writers remain stopped** until Step 7 postflight/reconciliation succeeds. If either half fails, `restore-state.json` records whether the database and/or Files root changed and the command prints the rollback assets. Before Step 7 acceptance the operator can restore the pre-restore safety state with:

```bat
restore-dataset.bat rollback YYYYMMDD-HHmmssZ
```

Rollback restores PostgreSQL from the safety backup custom dump and restores the preserved original live Files directory where available, independently verifies the safety Files inventory, retains a failed replacement tree for diagnosis when useful, and still leaves writers stopped for review.

Step 7 accepts an applied restore with:

```bat
restore-dataset.bat postflight YYYYMMDD-HHmmssZ
```

Postflight keeps normal writers stopped while it rechecks the restored database/Image count, exact live Files inventory and Image-catalogue/physical reconciliation. It then runs a controlled responder startup probe, requires MQTT RPC health and `synchronise: ok` retained replay, reads representative MARQUEE and IMAGE retained payloads, and fetches the representative Image through `/files` with a matching SHA-256. The probe is stopped before the exact prior writer-running state is restored. Any failure records `step7-postflight-failed`, stops all known responders and leaves `rollback` executable. Success records `restore-complete` and closes automatic rollback while retaining the complete safety backup and pre-restore Files rollback sibling as evidence.

The older `restore-db-from-*.bat` commands remain **database-only** restore tools. Their sidecar pairing check cannot prove current Files bytes are the matching snapshot, so they must not be confused with complete-dataset restore.

## Re-sharing and rollback warning

Do not roll back by pointing two independently changed databases at one old shared Files root. A later delete or overwrite from one dataset can damage the other dataset's bytes. If roots have diverged, keep separate copies and reconcile them explicitly. If intentionally returning all local modes to the common model, restore **both** `DIARIES_DB_DATA_DIR=./data/database/common` and `DIARIES_FILES_DIR=files-development-common` together.


## Live tooling lifecycle

The live `scripts/windows` tree contains only supported operational/admin commands and permanent regression/safety tooling. Completed-feature migration, evidence-capture and step-specific verification helpers belong under the corresponding completed change-control record rather than in this operator-facing tree.

Before closing a feature, classify every script it introduced as permanent operational tooling, permanent regression tooling, or historical feature tooling. Archive/remove historical tooling from `scripts/windows` and update callers atomically. A historical-looking name that really is permanent must be explicitly classified in `scripts/windows/validation/verify-live-script-policy.py`; do not bypass the guard by weakening its patterns.

Run the recurrence guard with:

```text
python scripts/windows/validation/verify-live-script-policy.py
```

Completed-feature migration and evidence-capture tooling is not kept in this live script tree. Historical tooling is preserved with the corresponding completed change-control evidence under `change-control/complete/`. The rules above are the supported operating contract.
