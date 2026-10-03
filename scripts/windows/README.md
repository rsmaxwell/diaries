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

## Backup semantics

The per-mode `backup-db-to-binary.bat` and `backup-db-to-sql.bat` commands are **database-only** backups. They derive their backup namespace from the effective database dataset and write a dataset sidecar describing the matching Files selector/root. They do not copy Files bytes.

A complete recoverable Diaries dataset backup is:

```text
PostgreSQL dump
+ matching mutable Files snapshot/copy
+ dataset/path identity manifest
+ preferably a deterministic checksum inventory
```

Freeze mutable responder writers that can access the pair before taking the matched database and Files captures. Keep the original diary scan tree separate; it is shared read-only source material, not the mutable Files side of this invariant.

## Restore semantics

Before restoring:

1. stop/freeze the responder that can write the target pair;
2. identify and validate the effective database + Files selection;
3. select a database dump and Files snapshot captured from that same pair;
4. preserve the current database/Files copies until recovery is verified;
5. restore the matching Files snapshot to the selected Files root;
6. run the appropriate `restore-db-from-*.bat` for the database side;
7. perform read-only reconciliation/checksum review before re-enabling writes.

A sidecar-backed database restore rejects a configured Files selector/root that does not match the backup identity, but that check cannot prove that the current Files **bytes** are the matching snapshot. A database-only reset/restore must therefore be labelled as potentially requiring Files reconciliation.

## Re-sharing and rollback warning

Do not roll back by pointing two independently changed databases at one old shared Files root. A later delete or overwrite from one dataset can damage the other dataset's bytes. If roots have diverged, keep separate copies and reconcile them explicitly. If intentionally returning all local modes to the common model, restore **both** `DIARIES_DB_DATA_DIR=./data/database/common` and `DIARIES_FILES_DIR=files-development-common` together.

For migration-specific 0031 capture/reconciliation tooling, see the `0031-step*` subdirectory READMEs. The rules above are the normal operating contract after 0031 is complete.
