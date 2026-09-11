# 0022 production migration workflow

This package separates read-only analysis from explicitly approved mutation.
It does not run from responder startup and it does not contain production
credentials.

## Migration baselines

Keep two different baselines and do not overwrite either one:

- the database backup made for 0022 is the static, reproducible migration
  baseline;
- the production database remains the live baseline until the maintenance
  window and must not be changed by analysis or rehearsal tooling.

The source tree is reconciled with each database baseline using the sibling
`diaries-importer` project before any corrective importer or migration is
designed. Run its `manifest` mode first, then its read-only `reconcile` mode.
Each source directory is identified by its normalized path relative to the
configured input root, for example:

```text
fragments/1829/07/07-img2900-left
fragments/1829/07/07-img2900-right
```

Sequence is an attribute only. It must never be used as source identity or as
the sole basis for linking a source record to a database Fragment.

The manifest also accepts explicit typed IMAGE source records. These may omit
`fragment.html` and carry a singular `image` object plus an optional
`placeAfter` source key. For the final baseline, supply the importer's
`--files-root` option so referenced files are checked and their size/SHA-256 is
recorded. An IMAGE source without HTML is source-only for legacy reconciliation
and must not be matched to a database row by date, Page or sequence alone.

Archive the following importer reports with the migration evidence:

```text
source-manifest.json
source-manifest.csv
source-key-collisions.csv
legacy-import-identity-collisions.csv
source-reconciliation.json
source-reconciliation.csv
database-reconciliation.csv
summary.json
```

Only `MATCHED_EXACT` rows are established matches. Possible edited,
missing, ambiguous, invalid and database-only rows require review. The reports
do not authorize a database update. See the `diaries-importer/README.md` for
commands and the complete status definitions.

## Generated inventory

From the `diaries` repository root (where `gradlew.bat` is located), run:

```powershell
.\gradlew.bat :diaries-responder:migration0022Inventory `
  -PmigrationConfig=C:\path\to\responder-config.json `
  -PmigrationOutput=C:\path\to\new-empty-0022-output
```

The database user configured as `db.admin` needs read access for inventory and
appropriate schema/data privileges when the SQL is executed separately.

The task creates:

```text
0022-inventory.csv
0022-safe-marquee-candidates.csv
0022-legacy-image-candidates.csv
0022-anomalies.csv
0022-summary.json
005-apply-safe-types.generated.sql
```

The generated SQL contains the reviewed Fragment IDs, expected versions,
inferred Pages and text checksums. It refuses to classify rows if the database
has changed since inventory generation.

## Reviewed migration planner

After the file-validated reconciliation, review ledger and fresh 0022 inventory
have been frozen, run the standalone planner in the sibling project:

```text
../diaries-migration-planner
```

Build it with `mvn clean package`, then run its executable JAR with
`--reconciliation-dir`, `--inventory-dir`, `--review-ledger` and a new or empty
`--output-dir`. See that project's `README.md` for the complete command.

The planner has no JDBC dependency and performs no mutation. It verifies the
ledger's reconciliation checksums and complete review coverage, incorporates
all 73 database Fragments containing one embedded image as IMAGE candidates,
honours reviewed type overrides, and allocates deterministic proposed sequence
values for reviewed `CREATE_MISSING` decisions. Existing sequence values are
never changed.

Archive all seven planner outputs with the frozen evidence. A `VALID` report is
necessary but does not authorize an apply: IMAGE work is marked deferred and
unknown Page ownership is left unresolved rather than guessed.

## Rehearsal

1. Restore the static 0022 backup into a disposable environment.
2. Run the importer `manifest` mode against the source tree and archive the
   output.
3. Run the importer `reconcile` mode against the restored database and archive
   the output.
4. Review every non-exact reconciliation status. Do not repair the database as
   part of this read-only stage.
5. Run `migration0022Inventory` into a new empty directory.
6. Review every CSV, especially image candidates and anomalies.
7. Run the reviewed migration planner and archive all seven outputs.
8. Confirm its validation report is `VALID` and reconcile every count and
   warning with the approved review ledger.
9. Run `001-preflight.sql` and save its complete output.
10. Stop writers in the disposable environment.
11. Run `002-additive-schema.sql`.
12. Run `004-backfill-page.sql`.
13. Review and run the generated `005-apply-safe-types.generated.sql` only for
    the safe typed-Fragment stage.
14. Generate the guarded SQL with the sibling
    `diaries-reconciliation-applier` and review all seven outputs.
15. Run and preserve the successful read-only
    `009-preflight-reviewed-safe-reconciliation.generated.sql` output.
16. Run
    `010-apply-reviewed-safe-reconciliation.generated.sql` with the explicit
    psql approval variable.
17. Run its read-only
    `011-verify-reviewed-safe-reconciliation.generated.sql`.
18. Run `006-postflight.sql`.
19. Compare the original 2,307 rows separately from the 22 reviewed additions
    and 15 reviewed text corrections. Deferred IMAGE actions are not applied.
20. Start the updated responder and verify retained-state reconciliation.
21. Smoke-test the current client and web application.

Use `psql` with stop-on-error enabled. For example:

```powershell
psql --set ON_ERROR_STOP=on --file 001-preflight.sql <connection-options>
```

Supply credentials through the normal secured environment or password-file
mechanism; do not place them in this change-control directory or command logs.

## Production apply

1. Announce the maintenance window and prevent edits.
2. Stop the responder and verify no writer remains.
3. Take a fresh binary/custom PostgreSQL backup and verify it can be read.
4. Preserve the exact deployed application versions and current retained-topic
   diagnostics.
5. Run and archive `001-preflight.sql` output.
6. Generate and archive a fresh source manifest.
7. Reconcile the source manifest with the live production database using the
   importer read-only mode.
8. Compare its reports with the static-baseline rehearsal and resolve every
   unexpected difference before continuing.
9. Generate a fresh production 0022 inventory into a new empty directory.
10. Compare it with the rehearsed inventory. Stop on unexpected differences.
11. Regenerate the migration plan and reconciliation SQL from the fresh
    production evidence. Compare both with rehearsal and stop on any
    unexplained difference.
12. Review and explicitly approve the production CSVs and generated SQL.
13. Apply `002-additive-schema.sql`.
14. Apply `004-backfill-page.sql`.
15. Apply the newly generated `005-apply-safe-types.generated.sql`.
16. Run and archive the successful read-only generated reconciliation
    preflight.
17. Apply the reviewed safe reconciliation SQL with its explicit approval
    variable; do not execute any deferred IMAGE action.
18. Run the generated reconciliation verification and archive its output.
19. Run and archive `006-postflight.sql` output.
20. Confirm every original row is accounted for, together with exactly the
    reviewed additions and text corrections.
21. Deploy and start the 0022 responder.
22. Observe database-map/topic-tree synchronization and investigate every
    unexpected difference.
23. Verify representative ordinary, embedded-image and orphan cases in both
    applications.
24. Preserve manifests, reconciliation reports, inventory, planner/applier
    output, SQL, command output
    and approval evidence with the
    completed change record.

Do not run the mutation scripts automatically as one unchecked command.
The inventory review between analysis and apply is a required control.

## Expected unresolved rows

Legacy image candidates receive Page ownership but intentionally retain
`type=NULL` until 0028. Fragments without an inferable Page remain unchanged and
must be resolved explicitly. `fragment.page_id` and `fragment.type` remain
nullable until 0029.

## Rollback

Before the updated responder is started, restore the pre-migration database if
schema or data verification fails. After a successful additive migration, an
old responder may be redeployed because the new columns are nullable and
`marquee.page_id` plus legacy MQTT fields remain intact. Do not drop the new
columns merely to roll back the application.

If production data itself is suspect, stop writers and restore the verified
pre-migration backup. Application rollback alone does not reverse a data
migration.
