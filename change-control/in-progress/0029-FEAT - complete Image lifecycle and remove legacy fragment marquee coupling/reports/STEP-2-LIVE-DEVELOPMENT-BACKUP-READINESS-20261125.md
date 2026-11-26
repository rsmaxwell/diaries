# 0029 Step 2 — Live-development backup/readiness gate (2026-11-25)

## Evidence basis

The user-provided terminal log `note(20261125-201130).txt` establishes an isolated PostgreSQL 18 restore, 49 source receipts and archives, 48 in-place IMAGE conversions plus one existing Whitley Park IMAGE link, followed by successful unchanged `step2-hybrid-schema-and-data.sql` execution. The resulting dataset contains 51 dated IMAGE Fragments, 2,271 dated TEXT Fragments, nine PREAMBLE TEXT Fragments, and zero invalid ownership relationships. This was **not a live development migration**.

## Recovery limitation discovered

`step2-hybrid-schema-rollback.sql` explicitly reverses only the schema/data portion for its reviewed original 11-record baseline. It does not restore the 49 additional legacy embedded-image HTML rows or reverse caption rewrites made during the isolated conversion. Therefore, a fresh complete logical backup and a coordinated application/MQTT rollback are necessary before live migration; the schema rollback script **alone is inadequate**.

## Package scope

`tools/step2-live-development-backup-readiness.sh` reads the already-running `diaries-development-db` container, confirms development database identity, collects current Git/submodule state, saves a PostgreSQL custom-format logical backup under this feature's `evidence/step-2-live-development-readiness/`, verifies the archive's table of contents with `pg_restore --list`, and creates an SHA-256 and receipt. It **does not** run any migration SQL, stop services, edit the live database, or touch production. The backup is a preparatory recovery artefact, not an approval to proceed or a full restore test.

Before live development migration, establish and record: editor/responder/reader source revision and service state; an explicit quiescence procedure for responder writers and retained MQTT topics; editorial approval of proposed Page assignment and caption transformations; current Files-root consistency; a tested full restore process with its own isolated target; an application-level postflight and MQTT retained-tree republish/cleanup plan; and explicit authorisation. Re-run a fresh backup immediately before the authorised live change, since the database may change in the meantime.

## Local checks

ZIP integrity and Bash syntax validation performed when preparing this package. No user database operations performed from the assistant environment.
