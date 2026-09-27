# 0025 Step 15.1 — Apply schema before responder binary

Completed 2026-09-27 for **development-infrastructure**, container `diaries-development-db`, database/user `diaries`, PostgreSQL 18.6, host port 5433. The schema was already applied during Step 2; this step freshly verifies readiness rather than reapplying DDL. No responder was started or restarted, and production was not accessed.

## Evidence

- **Backup/restore point:** `data/database-backups/development-infrastructure/before-0025-20260927-103724.dump`, 286244 bytes. SHA-256 `57fb8161cb3f2f8e0cf137acd3fbe07a302756548f97bd27911e7e2e7ede90f4`. Archive header identifies database diaries, creation 2026-09-27 09:37:24 UTC, PostgreSQL 18.6 and custom format. `pg_restore --list` succeeded; see `final-run/backup-archive-list.txt`. This verifies archive readability, not a fresh full restore test. A restore would replace data with that earlier state and requires separate approval.
- **Preflight/postflight:** both passed in `final-run/preflight-postflight-schema.log`. Existing checks ran in a repeatable-read transaction and created only temporary validation objects; final ROLLBACK removed them. No application rows or persistent schema objects were changed.
- **Migration output:** `migration-disposition.txt` records that no new apply was needed. The original Step 2 apply output was interrupted by the documented Windows PowerShell NOTICE-handling issue and cannot be reconstructed. [Step 2 follow-up](../../Step%202/README.md) and [original successful verification](../../Step%202/powershell51-verified/schema-verification.log) establish the prior verified state. Current evidence independently verifies it again.
- **Schema identity:** nullable BIGINT `fragment.image_id` without default; validated, nondeferrable `fragment_image_fk` referencing image(id) with NO ACTION deletion behavior; validated `fragment_image_type_check`; btree `fragment_image_id_idx`. No migration-version table was introduced: installed object definitions and the five migration SQL SHA-256 values in `final-run/result.json` identify the 0025 schema.
- **Responder candidate:** `diaries-responder-0.0.9-SNAPSHOT-fat.jar`; SHA-256 `0aadd2c0485889b08da4a8be8b88bdc2945a671e255e6c2f86894baed155c6b4`. Embedded metadata is preserved in `final-run/responder-build-info.properties`. It reports top-level Diaries commit `a8e70962898f52ac5db8baaab2e951b2bb884c36`; the responder checkout HEAD is `810444eb37289dd16a9fb3a317358c1a21b6cdcf` with uncommitted 0025 work. These commits alone do not describe the assembled implementation. `step14-source-comparison.json` confirms responder source/build inputs match the recorded Step 14 inventory; that step's full regression/build evidence remains applicable. The JAR hash identifies the specific local candidate, not a currently running deployment.
- **Environment identity:** `final-run/database-container.json` records actual container/image IDs, mounts, port and Compose project without credentials.

The database contains 10 Diaries, 683 Pages, 2329 Fragments, 2269 Marquees and 83 Images. There are zero IMAGE fragments and zero attached Image references. Preflight/postflight row/reference hashes agree within the verification snapshot; this does not claim equality to the pre-migration backup or exclude concurrent activity outside that snapshot.

## Repeating verification

Run `python verify-development.py <new-evidence-directory>` from any directory using the script's absolute path. The script targets the named local development container, checks the existing backup archive, expands the existing preflight/postflight SQL, inventories the schema and records candidate binary identity. It never executes `002-add-fragment-image-reference.sql` or launches the responder. Existing evidence directories are rejected.

The first attempt (`verified-run`) used an incorrect repository-root calculation and stopped at backup-file lookup before any SQL ran. The path was corrected; **final-run/result.json is the authoritative PASSED result**. Failed evidence is retained.

Only verification/evidence and change-control status were added. No Java/Angular implementation changed, so application tests were not repeated beyond the successful Step 14 results. The actual database preflight/postflight and backup inspection ran successfully for this step.

**15.1 is complete for development.** Step 15.2 deployment/smoke validation, 15.3 controlled IMAGE validation, and 15.4–15.5 final close-out remain outstanding. The feature stays in-progress. Production still needs its own backup/schema/deployment sequence; production authoring gate settings were not changed.
