# 0028-FEAT — Step 3 production writer-survey container-name correction

Date: 2026-11-24  
Status: Implemented in proposed ZIP; Windows/live re-verification pending.

## Trigger and observed evidence

The one-shot restore-and-writer run of 2026-11-24 10:22 UTC stopped safely before creating an isolated restore container or volume. The writer survey on `pluto` failed because it attempted `docker inspect diaries-db`.

The owner's read-only `docker ps -a` output on `pluto` identified the current service containers as:

- `diaries-postgres` (`postgres:18-alpine`)
- `diaries-mosquitto` (`eclipse-mosquitto:2`)
- `diaries-responder` (`rsmaxwell/diaries-responder:0.0.9-build-86`)
- `diaries-client` (`rsmaxwell/diaries-client:0.0.9-build-79`)
- `diaries-web` (`rsmaxwell/diaries-web:0.0.9-build-9`)

This is a writer-inventory tool defect, **not** proof of a production writer failure or a backup defect.

## Correction

In `tools/step3_writer_channel_inventory.py`:

1. Use `diaries-postgres` for Docker inspection, all read-only SQL queries, and the published-PostgreSQL-port result.
2. Inspect `diaries-mosquitto` rather than the nonexistent `diaries-mqtt`.
3. Leave the three remaining service identities unchanged.
4. Preserve redaction of Docker environment settings and all existing read-only behaviour.

Extend `tests/test_step3_retained_restore_and_writers.py` to exercise the exact production service names, read-only PostgreSQL query command and whole writer inventory. All **19** offline tests passed in the preparation environment. This is not evidence of live PostgreSQL or backup restoration success.

## Next action and gate

Apply the correction to the Windows Diaries parent repo using Beyond Compare, then rerun `tools/verify-0028-step3-retained-restore-and-writers.sh` from that repo root. The previous invocation failed **before** it reached Docker volume/container creation; the script's existing non-overwrite check remains mandatory. Do not remove an unexpected container or volume just to rerun.

The runner should collect the live writer survey before reading the pinned `production/20261124-003112Z` backup from `mars` and attempting a separate, network-disabled PostgreSQL restore. Production writer isolation, fresh writer-stopped recovery point, complete Files restore, Step 1/2 acceptance and the owner's separate production-apply authorisation all remain open.

**No production migration, backup creation, snapshot change or writer stop is authorised by this correction.**
