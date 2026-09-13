# 0024 Phase 2: additive Image schema

This migration adds only `public.image`, its identity sequence, five named
checks, primary key and two secondary indexes. It creates no Image rows and
does not modify Diary, Page, Fragment, Marquee, files or MQTT state.

Use PostgreSQL **18 with UTF8**, as configured by the local Compose modes.
The strict catalogue contract was validated on PostgreSQL 18.6. A server
upgrade that changes catalogue rendering must be reviewed and tested before
regenerating the contract; never regenerate it from an unexpected live schema.
The Windows runner and test harness were validated in PowerShell 7.6.5.

## Files and workflow

- `001-preflight.sql`: repeatable-read, read-only transaction; reports database,
  server, target schema, timestamp, login/current application role, privileges,
  collation and Image-like relations/types. Reports 0022 ownership/type anomalies
  and full-row SHA-256 fingerprints for all four chronology tables. Existing
  unresolved 0022 cases are reported, not reclassified.
- `002-add-image-catalogue.sql`: requires preflight in the same psql session.
  Acquires a migration advisory lock and SHARE locks on the four existing
  tables, repeats all prerequisite checks, and rejects intervening chronology
  changes. Creates the schema only when absent. Existing exact schemas are
  accepted, including populated catalogues, without changing their rows.
- `003-postflight.sql`: checks exact structure and before/after integrity.
  It runs inside the apply transaction **before COMMIT**, then once more in
  a read-only transaction when supplied as the third psql file. New tables must
  be empty; reruns must retain the previous Image row count.
- `schema.sql`, `prerequisites.sql`, `integrity.sql`,
  `catalog-shape.sql`, `assert-image-schema.sql`: shared includes; do not run
  schema.sql directly against an application database.
- `run-migration.ps1`: runs all three phases via Docker, verifies that a
  supplied custom-format backup is readable by pg_restore, and saves SQL copies,
  output, container/image identity, backup filename/hash and an evidence manifest.
- `tests/`: repeatable integration tests against an isolated backup restore.

Run as the application database owner, not a different administrator whose
privileges could hide application access failures. CONNECT, public USAGE/CREATE,
and access to the four existing tables are required. Creating a table as its
owner permits creation of its owned identity sequence, indexes and constraints.
A pre-existing Image table additionally requires application SELECT, INSERT,
UPDATE, DELETE and identity-sequence USAGE/SELECT. No GRANTs are added silently.

The scripts use fully qualified application names and set search_path to
`pg_catalog, public`; the reported current schema is consequently pg_catalog
and the explicitly reported target schema is public. A five-second lock timeout
prevents indefinite waiting behind a running application transaction. A failed
preflight or postflight exits psql nonzero through ON_ERROR_STOP; before-commit
failures roll back the entire schema addition.

## Exact schema and path identity

Columns are the ten fields specified in Phase 2, with identity BY DEFAULT on
bigint id, version default zero, positive width/height, and caption/alt_text
default empty strings. Named checks are:

- `image_version_check`, `image_width_check`, `image_height_check`;
- `image_mime_type_check`: image/jpeg, image/png, image/gif, image/webp only;
- `image_checksum_check`: exactly 64 lowercase hexadecimal characters.

`image_relative_path_ci_uq` is unique on:

```sql
lower(relative_path COLLATE pg_catalog.pg_unicode_fast)
```

This is the agreed database case identity: PostgreSQL 18 deterministic Unicode
lowercasing, independent of database/OS locale. Original path case is preserved.
Phase 3 must normalize paths to NFC and use this same SQL expression for lookup
and collision guards; do not substitute locale-dependent application lowercasing.
The Phase 1 inventory contains ASCII paths and has zero collisions under this
rule. Filesystem real-path validation and canonical path validation remain in
the later application service work.

`image_checksum_idx` is deliberately non-unique: identical bytes at different
historical paths are allowed.

The verifier compares column positions, names, exact types, defaults, nullability,
identity/generation and collations; check/primary-key definitions, names and
validation/deferral state; full index expressions, uniqueness and readiness;
identity-sequence configuration and ownership; and table properties. Unexpected
extra columns, indexes, user triggers, policies, rules, inheritance and RLS fail.
An orphan sequence, a view named image, or other unexpected public Image-like
relations also fail. There is no repair-by-ALTER or CREATE IF NOT EXISTS shortcut.

## Backup and operational prerequisites

1. Confirm the intended host, mode, container, database, application role and
   running PostgreSQL image/version. Phase 2 requires the completed 0022 schema.
2. Pause application writes for the migration window; do not let startup
   reconciliation or another database migration run concurrently.
3. Take a fresh backup using the mode's existing backup script. Check its exit
   code and nonzero size, record its SHA-256, and test restoration into a separate
   empty database. A readable archive listing alone is not a restore test.
4. Keep the responder's effective Hibernate DDL action at `validate` or `none`,
   never `update`, `create` or `create-drop`. Check
   `DbConfig.additionalConnectionProperties`, including
   `hibernate.hbm2ddl.auto` and `jakarta.persistence.schema-generation.database.action`.
   GetEntityManager passes those properties through. Phase 2 does not register
   an Image entity or change runtime configuration; explicit SQL owns this schema.
5. Review read-only preflight output. Existing 0022 anomalies need not be zero,
   but the before/after counts and full-row digests must be identical.

## Exact development commands

From the Diaries repository root in PowerShell:

```powershell
& .\scripts\windows\development-infrastructure\backup-db-to-binary.bat
if ($LASTEXITCODE -ne 0) { throw 'Backup failed' }
$migration = Join-Path (Get-Location) 'change-control/in-progress/0024-FEAT - introduce reusable persistent Image catalogue/migration'
# Set these to the fresh backup printed above and a NEW evidence directory.
$backup = 'data/database-backups/development-infrastructure/diaries-development-YYYYMMDD-HHMMSS.dump'
$evidence = 'change-control/in-progress/0024-FEAT - introduce reusable persistent Image catalogue/evidence/phase-02-schema/development-YYYYMMDD-HHMMSS'
& "$migration/run-migration.ps1" -Container diaries-development-db -Database diaries -User diaries -BackupFile $backup -EvidenceDirectory $evidence
```

For an independent read-only preview (no backup or apply):

```powershell
$remote = '/tmp/diaries-0024-preflight-' + [guid]::NewGuid().ToString('N')
docker cp $migration "diaries-development-db:$remote"
if ($LASTEXITCODE -ne 0) { throw 'Copy failed' }
docker exec diaries-development-db psql -X -U diaries -d diaries -v ON_ERROR_STOP=1 -f "$remote/001-preflight.sql"
if ($LASTEXITCODE -ne 0) { throw 'Preflight failed' }
```

For local-docker-build or local-published-smoke use that mode's corresponding
backup script and its verified database container; do not assume it shares
the development database. The runner otherwise takes the same parameters.

## Production commands (run on the verified production Docker host)

Production deployment is a later phase and was not executed as part of Phase 2.
Use the actual container/database/role from the deployed configuration. The
following Bash commands take them as required environment values, so no
development target is silently reused:

```bash
: "${DIARIES_DB_CONTAINER:?set the verified production database container}"
: "${DIARIES_DB_NAME:?set the verified production database name}"
: "${DIARIES_DB_USERNAME:?set the application database owner}"
: "${MIGRATION_DIR:?set the absolute path to this reviewed migration directory}"
: "${BACKUP_FILE:?set the absolute path to the fresh verified production backup}"
: "${EVIDENCE_DIR:?set a new absolute production evidence directory}"
test -s "$BACKUP_FILE" || exit 1
mkdir "$EVIDENCE_DIR" || exit 1
docker inspect --format '{{.Config.Image}} {{.Image}}' "$DIARIES_DB_CONTAINER" > "$EVIDENCE_DIR/container-image.txt" || exit 1
sha256sum "$BACKUP_FILE" > "$EVIDENCE_DIR/backup-sha256.txt" || exit 1
remote="/tmp/diaries-0024-$(date -u +%Y%m%dT%H%M%SZ)-$$"
docker cp "$MIGRATION_DIR" "$DIARIES_DB_CONTAINER:$remote" || exit 1
docker exec "$DIARIES_DB_CONTAINER" psql -X -U "$DIARIES_DB_USERNAME" -d "$DIARIES_DB_NAME" -v ON_ERROR_STOP=1 \
  -f "$remote/001-preflight.sql" -f "$remote/002-add-image-catalogue.sql" -f "$remote/003-postflight.sql" \
  > "$EVIDENCE_DIR/preflight-apply-postflight.txt" 2>&1
result=$?
cat "$EVIDENCE_DIR/preflight-apply-postflight.txt"
test "$result" -eq 0 || exit "$result"
cp -R "$MIGRATION_DIR" "$EVIDENCE_DIR/migration-source" || exit 1
(cd "$EVIDENCE_DIR" && find . -type f ! -name SHA256SUMS.txt -print0 | sort -z | xargs -0 sha256sum > SHA256SUMS.txt)
```

Take the production backup using the deployment's established backup workflow
before these commands. Deployment inventory and backup paths are not present
in this task, so none are invented here. Do not use `psql --single-transaction`
around these scripts: they manage their own read-only and apply transactions.
Do not run each numbered SQL file in a separate connection: the before-state
psql variables deliberately bind the workflow to one session.

## Expected output and evidence

Success includes `0024 PREFLIGHT PASS (read-only)`,
`0024 exact Image schema verified`, `0024 POSTFLIGHT PASS`,
`0024 APPLY PASS (committed)`, and a final postflight PASS.
For first application `image_rows=0`, `expected_image_rows=0`,
`image_table_empty=t`, `exact_schema_verified=t` and
`chronology_unchanged=t`. A safe populated rerun instead retains its original
Image count. An error is a failed run even if some earlier PASS lines exist;
always check the final process exit code.

Runner evidence filenames:

- `preflight-apply-postflight.txt`;
- `backup-archive-list.txt`, `run-result.json`;
- `sql/*.sql`: exact migration input copies;
- `.gitattributes`, `SHA256SUMS.txt`.

Integration test evidence comprises `test-results.json` and named per-scenario
logs. Test-only fault injection remains under the disposable build directory.
Database content is not exported to these logs: only counts and SHA-256 digests.

## Rollback

A failure inside 002 leaves no partially created catalogue: PostgreSQL rolls back
its transaction when psql exits. Investigate and rerun preflight with fresh
evidence. Do not repair a partial schema automatically.

After a successful commit, rollback is **database restore from the verified
pre-migration backup**, in a maintenance window with explicit authorization to
replace the target database. For development use the existing
`scripts/windows/development-infrastructure/restore-db-from-binary.bat` and its
documented confirmation flow after verifying container, database and backup.
Production uses the deployment's established restore workflow. Restore loses
changes made after the backup; preserve those separately before replacement.
Do not drop the Image table as an improvised rollback, delete Docker volumes,
modify NAS files, or automatically run any restore. No restore of the existing
development or production database is part of this implementation.

## Repeatable tests

Create a fresh isolated PostgreSQL 18 container with no published ports/network
and temporary storage, then run the tests with a fresh real database backup:

```powershell
docker run --detach --rm --name diaries-0024-schema-test --network none --tmpfs /var/lib/postgresql -e POSTGRES_HOST_AUTH_METHOD=trust -e POSTGRES_USER=diaries -e POSTGRES_DB=diaries postgres:18-alpine
# Wait until pg_isready succeeds.
docker exec diaries-0024-schema-test pg_isready -U diaries -d diaries
& "$migration/tests/run-tests.ps1" -Container diaries-0024-schema-test -BackupFile $backup -EvidenceDirectory 'build/0024-schema-tests-NEW'
# After inspecting results, stop only this disposable test container.
docker stop diaries-0024-schema-test
```

The suite creates new databases inside that container for all mutations.
It tests read-only preflight, fresh apply, idempotency, populated reruns,
identity/defaults, duplicate checksums, ASCII/Unicode case collisions, invalid
metadata, twelve incompatible-schema variants, orphan objects, privileges,
missing preflight, chronology drift and before-commit postflight rollback.
