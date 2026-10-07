# Step 7 evidence — post-restore reconciliation, retained replay and failure-safe restart

## Status

**Complete — 2026-10-07. Permanent regression, failure-safe first attempt and successful real postflight retry recorded.**

Step 7 is the acceptance boundary for a complete restore. `pg_restore` success alone does not return the dataset to service.

## Permanent operator command

From the same local mode used for the restore:

```bat
restore-dataset.bat postflight <backup-id-or-complete-backup-directory>
```

For the current rehearsal the command is:

```bat
restore-dataset.bat postflight 20261007-105033Z
```

The command accepts only a Step-6 `applied-awaiting-step7` state, or `step7-postflight-failed` for a controlled retry. Automatic rollback remains available throughout postflight until final acceptance.

## Deterministic static reconciliation

Before any responder probe is started, postflight requires every writer to be stopped and proves:

1. the selected schema-2 complete backup is still valid and matches the effective target;
2. the mandatory safety backup remains valid;
3. PostgreSQL is queryable and the restored Image row count matches the selected backup manifest;
4. the live durable Files tree exactly matches the backup by path, size and SHA-256 while permitting only benign runtime `.image-staging`;
5. the Image catalogue reconciles to the physical Files tree.

`scripts/windows/common/complete-dataset-postflight.py` performs the read-only catalogue/physical reconciliation. Every Image row must have an existing matching file whose SHA-256 equals the database checksum. Missing files, checksum conflicts, case-fold collisions and unexplained untracked files fail postflight. The four legacy `Thumbs.db` files previously reviewed by 0031 Step 9 are the only intentionally tolerated untracked durable files; they remain non-application state.

## Responder/replay and representative content

Only after static reconciliation passes does Step 7 start a temporary responder probe for the invoking mode. The probe must prove:

- responder/MQTT RPC health succeeds;
- startup logs contain `synchronise: ok` and a database retained-map size;
- a representative `diaries/marquees/<id>` retained payload is readable JSON and matches a restored MARQUEE row;
- a representative `diaries/images/<id>` retained payload is readable JSON and matches the restored Image identity/path;
- the representative Image can be fetched through `http://localhost:<port>/files/<relativePath>` and its downloaded SHA-256 matches the Image catalogue checksum.

The probe is stopped before the prior writer-running state is restored. This keeps acceptance separate from restoring normal service state.

## Failure-safe restart and rollback close-out

If any postflight check fails, the implementation:

```text
status = step7-postflight-failed
all known responders = stopped
mandatory safety backup = retained
pre-restore Files rollback tree = retained
rollback command = still executable
```

`restore-dataset.bat rollback <backup>` explicitly accepts `step7-postflight-failed`, so failed acceptance can return to the Step-5 safety state.

Only after every Step-7 check passes does the engine restore the exact prior responder-running state and record:

```text
status = restore-complete
postflight.status = complete
rollback.status = closed-after-step7
automaticRollbackAvailable = false
```

The complete safety backup and original pre-restore Files rollback sibling are intentionally retained as evidence; Step 7 closes the automatic rollback action rather than deleting those recovery assets.

## Permanent regression

`REGRESSION.txt` records the focused Step-7 regression plus the Step-5/6, database-only and live-script guards. The synthetic catalogue fixture proves a catalogued file plus reviewed `Thumbs.db` passes, while a checksum change and an unexplained extra file are rejected. The static state-machine checks protect:

- all three local wrappers exposing `postflight`;
- postflight only after Step 6 apply/failure retry;
- database + exact Files verification before active probe;
- catalogue reconciliation;
- retained replay and MARQUEE/IMAGE checks;
- `/files` byte verification;
- prior writer restoration only after the probe is stopped and all checks pass;
- `step7-postflight-failed` writers-stopped state;
- rollback availability after failed postflight;
- rollback closure only after `restore-complete`.


## First real runtime attempt — 2026-10-07

`RUNTIME-FIRST-ATTEMPT.txt` records the first Step-7 postflight against restore source `20261007-105033Z`. The important dataset checks all passed before the temporary responder health probe:

- selected restore and safety-backup schema-2 manifests validated;
- live restored Files matched the 89-file / 100032776-byte inventory;
- Image catalogue reconciliation reported 85 Image rows, 85 catalogue/file matches and only the four reviewed legacy `Thumbs.db` objects;
- the direct responder distribution built successfully.

The run then failed before health/replay acceptance because the Java `ResponderHealthCheck` writes an informational SLF4J line to stderr. Windows PowerShell 5.1 converts redirected native stderr into an `ErrorRecord`; with `$ErrorActionPreference = 'Stop'`, that benign line became a terminating error before the script could inspect the native exit code. The failure path correctly left all writers stopped and persisted `step7-postflight-failed`, so the same postflight may be retried without repeating Steps 5 or 6.

The permanent correction introduces `Invoke-NativeCapture`, which temporarily uses non-terminating native stderr capture and treats the native process exit code as authoritative. Step-7 direct config preparation, Gradle preparation, Java health checking and retained `mosquitto_sub` capture use this boundary. The regression explicitly rejects a return to raw Java `2>&1` capture under strict error handling.

## Successful real postflight retry — 2026-10-07

`RUNTIME-FINAL-POSTFLIGHT.txt` records the successful retry of:

```bat
restore-dataset.bat postflight 20261007-105033Z
```

The retry did not repeat Step 5 preparation or Step 6 apply. It resumed from the intentional `step7-postflight-failed` state after the native-stderr correction and proved the full acceptance contract:

- restore backup `20261007-105033Z` and safety backup `20261007-114623Z` both revalidated as schema-2 complete backups;
- the live durable Files tree matched the selected backup exactly at 89 files / 100032776 bytes;
- Image catalogue reconciliation found 85 Image rows and 85 catalogue/file matches, with the four already-reviewed legacy `Thumbs.db` files as the only untracked durable files and zero unexplained missing/untracked/conflicting content;
- the direct responder distribution built successfully;
- the temporary responder probe completed the MQTT/replay checks and reported `synchronise: ok`;
- representative retained MARQUEE and IMAGE payloads were readable;
- representative Image bytes were fetched through `/files` and verified;
- the probe was stopped before restoring prior writer state;
- no responder had been running before restore, so all responders correctly remained stopped afterwards;
- safety backup `20261007-114623Z` and the original pre-restore Files rollback sibling were retained as evidence;
- automatic rollback was closed only after successful Step-7 acceptance.

The command ended at the normal command prompt with `STEP 7 POST-RESTORE VERIFICATION COMPLETE.` Step 7 is therefore complete: restore acceptance is demonstrated by the database, Files, catalogue, retained replay and HTTP/static-file surfaces together, rather than by database restore exit status alone.
