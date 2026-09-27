# 0025 Step 2 — Fragment Image reference schema

Additive PostgreSQL migration. No backfill and no authoring enablement. Application/JPA changes are Step 3 and later.

## Objects

- public.fragment.image_id: nullable BIGINT, no default.
- fragment_image_fk: single-column FK to public.image(id), immediate/nondeferrable MATCH SIMPLE, ON UPDATE/DELETE NO ACTION. Never CASCADE.
- fragment_image_id_idx: valid nonunique full B-tree on image_id.
- fragment_image_type_check: image_id IS NULL OR (type IS NOT NULL AND type = 'IMAGE'). The explicit null test prevents SQL UNKNOWN from admitting a null type with a reference.

IMAGE can have no Image yet. MARQUEE cannot reference an Image. Multiple IMAGE fragments can share one Image. The inverse IMAGE/no-Marquee rule spans tables and remains service enforcement in later 0025 steps; it is not added here.

## Preflight and preservation

001-preflight.sql checks prerequisite tables/columns, the validated MARQUEE/IMAGE type constraint, orphan Page references and any existing image_id values. It rejects an incompatible column/default, wrong named FK/check/index or an unexpected differently named FK using image_id. It accepts the two equivalent type-check cast forms found in the source SQL and frozen database. Other shapes require explicit review rather than silent acceptance.

Snapshots record counts and ordered JSON digests of diary, page, fragment, marquee and image. The Fragment digest excludes only the newly added image_id column; a separate digest records all per-Fragment references, treating absent/new-null references alike. Existing chronology, Image rows and references must match both the original preflight snapshot and the in-transaction postflight.

002-add-fragment-image-reference.sql requires successful preflight in the same psql session, acquires a migration advisory lock plus table locks, rechecks preflight identity/data/schema, adds missing objects, and validates both constraints before commit. A compatible partial schema is completed; incompatible partial schemas fail closed. No existing rows are updated. Postflight validates the final object shapes and data digests.

A maintenance window is required: chronology/Image writes are blocked while checks and DDL run, with a 5-second lock timeout and 60-second per-statement timeout. NOT VALID then VALIDATE is used for safe constraint creation, but this is not an online/concurrent-index migration.

## Apply explicitly

Confirm target mode/container/database and a recent database backup before applying. The user applied this migration to the development database on 2026-09-27; subsequent schema verification passed. Production has not been migrated by this work.

PowerShell wrapper (requires Docker and a PostgreSQL custom-format backup):

```powershell
./run-migration.ps1 -Container <database-container> -Database <database> -User <database-user> -BackupFile <backup.dump> -EvidenceDirectory <new-directory>
```

The wrapper checks the backup archive with pg_restore --list, captures target image identity and backup hash, copies SQL and captures logs/results. Archive readability is not proof of backup freshness or correspondence; the operator must confirm those. It does not restore or delete the target database. It leaves its unique /tmp/diaries-0025-* SQL/backup directory for inspection.

Alternatively, after confirming a backup, run all files in the same psql process from this directory:

```text
psql -X -v ON_ERROR_STOP=1 -f 001-preflight.sql -f 002-add-fragment-image-reference.sql -f 003-postflight.sql
```

On a repeat/recovery run where non-null references are explicitly expected, use -AllowExistingReferences with the PowerShell wrapper or -v allow_existing_references=true with psql. This permits already-valid references only; it never bypasses schema, type or FK integrity checks. Default mode rejects non-null references.

Postflight runs inside the DDL transaction before commit and is repeated outside by the wrapper. A post-commit verification failure must be investigated rather than assumed to mean rollback. Stop on errors and retain logs. Do not automatically drop the column or restore a database: after Image references are in use, either action could lose data.

## Disposable verification

```powershell
./tests/run-tests.ps1 -EvidenceDirectory <new-directory>
```

This runner restores the checksum-pinned frozen 0024 backup into a new private PostgreSQL 18 container (no published ports, tmpfs storage), creates the 0024 Image schema, and tests first/repeated apply, constraints, malformed-schema rejection and partial/referenced recovery. Constraint fixtures roll back; committed reference fixtures are explicitly removed from this owned test database. Before/after snapshots must match. Only the owned container is stopped/removed.

See ../evidence/Step 2/README.md for actual results. Never run tests/constraints.sql against a live database; use the disposable runner.

## Windows PowerShell notices

The wrapper supports Windows PowerShell 5.1 and PowerShell 7. PostgreSQL NOTICE
messages are captured as diagnostics; native exit codes determine success. If an
older wrapper reports `NativeCommandError` on a NOTICE, do not assume rollback:
PostgreSQL may already have committed. Verify the current schema before retrying.
The 2026-09-27 development incident and verification are recorded in Step 2 evidence.
