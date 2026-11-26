# Step 2 — Isolated rehearsal Compose-free runner correction (2026-11-25)

## Evidence
The first rehearsal stopped at Docker Compose configuration because `DIARIES_DB_DATA_DIR` was unset, yielding `invalid spec: :/var/lib/postgresql`. No database restore or migration occurred.

## Correction
The runner now accesses only the existing running container `diaries-development-db` for the logical `pg_dump` source and no longer evaluates the Compose definition. It validates the container is running and its PostgreSQL environment declares user/database `diaries`, then streams the backup to the isolated `--network none` Postgres container. Original conversion, unchanged hybrid SQL, evidence capture and automatic cleanup are preserved.

## Acceptance
Reapply ZIP to the Windows Diaries repository and run `bash "$FEATURE/tools/step2-49-isolated-rehearsal.sh"` from the parent repository root. Review the full run log. The fix is script-only and has not been exercised against the user's development database.
