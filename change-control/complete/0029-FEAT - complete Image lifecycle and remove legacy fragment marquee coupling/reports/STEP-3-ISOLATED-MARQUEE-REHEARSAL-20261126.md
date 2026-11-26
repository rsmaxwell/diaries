# 0029-FEAT Step 3 — isolated Marquee Page retirement rehearsal

**Prepared:** 26 November 2026. **Status:** SCRIPT PREPARED — NOT EXECUTED. Step 3 remains OPEN.

## Purpose and boundaries

Rehearse `marquee.page_id` removal and reversal against a restored copy of the current development database. The source database container is `diaries-development-db` (`POSTGRES_DB=diaries`, `POSTGRES_USER=diaries`). This script only performs `pg_dump` against that source. All modifications occur in an ephemeral `postgres:18-alpine` container started with `--network none` and no published ports. It does not interact with production, alter the active development schema, or modify the MQTT broker.

## Inputs

- `tools/step3-retire-marquee-page-id.sql` (guarded forward removal; from the preceding Step 3 implementation package)
- `tools/step3-restore-marquee-page-id.sql` (guarded reverse-column reconstruction)
- Existing running development PostgreSQL container and local Docker CLI
- The current 0029 hybrid schema must already exist, and `marquee.page_id` must still be present

## Invoke

**Windows 11 Cygwin Bash, Diaries repository root:**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
bash 'change-control/in-progress/0029-FEAT - complete Image lifecycle and remove legacy fragment marquee coupling/tools/run-step3-isolated-marquee-rehearsal.sh'
```

No manual `docker rm`, database drop, or live schema mutation is required. A failure returns nonzero, prints FAIL and leaves an evidence log; the script removes only its uniquely named ephemeral container via `trap`.

## Acceptance criteria

1. The source running container identity matches the expected development database.
2. Restore of the stream succeeds into the isolated database.
3. The Step 2 `fragment.placement` column and original `marquee.page_id` are present.
4. All Marquee rows reference valid DATED Fragments and have matching Page IDs.
5. Guarded forward SQL removes only redundant Page storage; Marquee row count and ownership remain valid.
6. Guarded rollback restores the Page column with zero ownership mismatches and unchanged row count.
7. A second forward migration succeeds and leaves valid ownership.
8. Script exits zero with `SUMMARY: PASS`; preserve the timestamped log in `evidence/step-3-isolated-marquee-page-retirement/`.

## Caveats

This is a **database migration rehearsal**, not a Java+database integration test; Java tests have passed separately. It does not exercise live MQTT, the Editor/Reader or a production backup restore. A database forward migration is not approval to modify production. Inspect any failure before retrying. No previously accepted Step 2 conversion is repeated.
