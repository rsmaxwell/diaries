# 0031-FEAT Step 11 Windows tooling

This tooling implements the evidence capture for **Step 11 — Repoint local modes and verify resolved runtime paths after overrides**.

It does not upload, delete, rename, restore, reconcile, or otherwise mutate catalogue/file data. The capture operations are limited to rendered configuration, mount inspection, `SELECT`, directory listing, responder-log capture, and HTTP `HEAD` reads. Starting a responder may recreate its normal transient staging/control state; Step 12 owns the subsequent post-split reconciliation.

## Preconditions

Step 10 must be complete and the required non-production Files root must already exist. Production must remain on the Step 8 write freeze while local Step 11 checks are performed.

For the normal workstation configuration, the ignored `config\environments\local.env` must select the already-created common pair:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The existing `validate-dataset-pair.bat` guard rejects a one-sided/crossed pair and rejects local use of production `files`.

## Capture one running mode

The requested mode must already be running. From the Diaries project root:

```bat
scripts\windows\0031-step11\capture-local-mode.bat local-docker-build -ProductionWriteFreezeConfirmed
scripts\windows\0031-step11\capture-local-mode.bat local-published-smoke -ProductionWriteFreezeConfirmed
```

For direct Windows development, start `development-infrastructure`, then run the direct responder in a separate console with its output redirected to a log. Pass that log to the capture command:

```bat
scripts\windows\development-infrastructure\start.bat

if not exist build mkdir build

diaries-responder\scripts\windows\run-responder.bat > build\0031-step11-direct-responder.log 2>&1

scripts\windows\0031-step11\capture-local-mode.bat development-infrastructure -ProductionWriteFreezeConfirmed build\0031-step11-direct-responder.log
```

The direct responder must still be running while the capture command performs the `/files/...` and `/diaries/...` HTTP `HEAD` checks. Stop it with `Ctrl+C` after the capture succeeds, then stop `development-infrastructure` before starting another local mode.

Each run writes a timestamped directory under:

```text
change-control\in-progress\0031-FEAT - isolate mutable Files storage by database environment\evidence\Step 11\runtime\
```

The collector stores only redacted rendered configuration. It never copies `local.env` or an unredacted responder configuration into evidence.

## Cross-mode comparison

After one passing capture exists for each mode, run:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\0031-step11\compare-local-mode-evidence.ps1
```

With the normal common override, this requires all three modes to resolve the same effective database directory and the same `files-development-common` selector. With isolated defaults, it requires each mode to use its frozen Step 2 Files selector. Every report must retain the public `/files` context and include responder startup/runtime logs.

Do not start Step 12 until all three Step 11 mode captures and the cross-mode comparison pass.
