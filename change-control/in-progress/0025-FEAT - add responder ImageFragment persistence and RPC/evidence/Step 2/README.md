# 0025 Step 2 — Add fragment.image_id schema

Completed 2026-09-27. Migration implemented and verified on disposable PostgreSQL only. No active development or production schema/data changed.

## Delivered

Migration files under ../../migration: 001-preflight.sql, 002-add-fragment-image-reference.sql, 003-postflight.sql; shared assert-schema.sql and snapshot.sql; explicit run-migration.ps1 wrapper; tests/constraints.sql and tests/run-tests.ps1; operating documentation.

Adds nullable BIGINT image_id, restrictive/no-action FK, lookup index and a validated same-row type/reference check. No backfill. Valid partial/repeat schemas are accepted; incompatible objects are rejected before changes. Non-null references require explicit repeat/recovery opt-in and remain subject to FK/type validation. Existing chronology/Image rows and references are snapshot-checked under locks.

## Actual validation

**verified-run/result.json: PASSED — 13 scenario groups**:

1. First apply on frozen pre-0025 data.
2. Repeat apply without changes.
3. Constraint tests: MARQUEE/null and IMAGE/null/existing accepted; missing Image, MARQUEE/reference and null-type/reference rejected; referenced Image deletion blocked; Fragment deletion does not delete Image.
4. Reject existing image_id default.
5. Reject wrong column type.
6. Reject cascading FK.
7. Reject index on wrong column.
8. Reject a weak check that admits null-type references.
9. Reject missing prerequisite type check.
10. Complete partial schema with only image_id retained.
11. Validate compatible existing NOT VALID FK/check.
12. Reject unexpected non-null references by default.
13. Accept explicit expected-reference recovery without changing those rows.

The restored database started with 10 Diaries, 683 Pages, 2329 Fragments, 2269 Marquees and zero Images. All original counts and ordered row/reference digests were unchanged at the end. The owned container stopped successfully. Backup SHA-256 and PostgreSQL image ID are recorded in result.json. No live database/NAS access occurred.

Runs 01–04 preserve failed development attempts: preflight rejected the frozen database's explicit varchar-to-text form of fragment_type_check. No migration was applied during these attempts. Run 05 passed the initial ten groups; verified-run additionally covers unvalidated and expected-reference recovery. Failed artifacts are retained, not overwritten.

PowerShell scripts were syntax-checked. The SQL sequence is exercised directly in the disposable runner; the operator-facing backup-wrapper invocation was not used against an active database. No Java/Angular source changed, so the Step 1 passing responder build/tests remain the application baseline rather than being rerun for SQL-only work.

## Boundaries

This is the additive schema capability only. JPA/DTO/RPC changes are later steps. Cross-table IMAGE/no-Marquee enforcement and explicit referenced-image 409 handling remain required later in 0025. Production authoring remains disabled pending 0026/0027.

See source-sha256.csv for the migration/test source identities used. Schema compatibility checks are deliberately conservative; unrecognized but equivalent definitions should be reviewed, not bypassed. Migration requires a short write-blocking maintenance window and a confirmed database backup. No commit or push performed.

## Development apply follow-up � 2026-09-27

The user ran the operator wrapper against `diaries-development-db` / `diaries`
after creating `before-0025-20260927-103724.dump`. Windows PowerShell reported
`NativeCommandError` on a harmless psql NOTICE from `assert-schema.sql`. The wrapper
used `ErrorActionPreference=Stop` while redirecting native stderr, which Windows
PowerShell 5.1 treats as ErrorRecords. This interrupted wrapper logging; it did not
establish that PostgreSQL had rolled back or stopped.

Read-only inspection subsequently found `image_id`, both validated constraints and
the index. Preflight plus postflight (without apply SQL) passed against the current
development schema. See `powershell51-verified/schema-verification.log`. The schema
is ready for Step 3; another apply is unnecessary. These fresh snapshots prove the
verification left current rows unchanged, not equality to the user's pre-migration
backup. The interrupted invocation's original transaction log was not recovered.

`run-migration.ps1` now captures native stdout/stderr with a function-local Continue
preference and checks the captured exit code; genuine SQL failures still stop the
runner after its evidence is written. The helper also supports PowerShell 7's native
error preference. `migration/tests/test-native-output.ps1` loads only the helper
functions and runs notice/error probes, never the migration body.

Both PowerShell 5.1.26100.9444 and 7.6.5 checks passed: notice exit 0, deliberate
exception exit 1, checked helper rejects failure. Results and runner hashes are in
`powershell51-verified/result.json` and `powershell7-verified/result.json`.
The earlier `powershell51-fix` attempt exposed multiple Docker executable matches;
selection was corrected before the successful runs. No application rows were
modified and no migration was reapplied during this diagnosis. Java/client builds
were not repeated for this PowerShell-only fix.
