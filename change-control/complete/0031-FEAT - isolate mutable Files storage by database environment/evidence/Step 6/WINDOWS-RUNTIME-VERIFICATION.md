# Step 6 Windows runtime verification

The exact launch-time pairing implementation is PowerShell because the supported local operating scripts are Windows batch/PowerShell scripts.

Run from the Diaries repository root:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\validation\verify-0031-step6.ps1
```

## First workstation run — 2026-10-02

The first run reached `validate-dataset-pair.ps1` but stopped with a PowerShell parser error caused by a variable immediately followed by a colon:

```powershell
$LocalEnvironmentFile:
$ModeName:
```

The guard was corrected to use braced interpolation:

```powershell
${LocalEnvironmentFile}:
${ModeName}:
```

The original console capture is retained as `windows-runtime-verification-20261002-first-run.txt`. The portable verifier contains a regression check for this interpolation hazard.

## Second workstation run — 2026-10-02

The second run confirmed all three isolated-default cases and all three deliberately shared-common cases. It then entered the first expected rejection case (`DIARIES_DB_DATA_DIR` overridden without `DIARIES_FILES_DIR`). The guard correctly emitted `Dataset override mismatch`, but the outer verifier used `$ErrorActionPreference = 'Stop'`, so Windows PowerShell treated the child process's expected stderr as a terminating `NativeCommandError` before the harness could inspect the expected non-zero exit code.

The harness was corrected so only the child invocation is executed with `ErrorActionPreference=Continue`, with both streams captured. It immediately restores the outer strict preference and then evaluates `$LASTEXITCODE`. The original console capture is retained as `windows-runtime-verification-20261002-second-run.txt`.

## Final workstation run — PASS — 2026-10-02

The corrected suite was run again and passed every case. The exact console output is retained as `windows-runtime-verification-20261002-success.txt`.

It passed all six valid configurations:

- isolated defaults: `development-infrastructure`;
- shared common pair: `development-infrastructure`;
- isolated defaults: `local-docker-build`;
- shared common pair: `local-docker-build`;
- isolated defaults: `local-published-smoke`;
- shared common pair: `local-published-smoke`.

It also passed all four negative assertions by confirming that the guard rejects:

- a DB-only `local.env` override;
- a Files-only `local.env` override;
- a local database paired with production `DIARIES_FILES_DIR=files`;
- a crossed approved local pair.

The run finished with:

```text
PASS: 0031-FEAT Step 6 Windows dataset-pair regression checks
```

## Result

**PASS — Windows execution evidence closed.**

The exact mismatch that motivated Step 6 is covered by a repeatable regression check, and the regression suite has passed on the supported Windows workstation environment.

The suite uses temporary `local.env` files and the real committed mode environments. It does not modify any database, NAS Files tree, MQTT state or Docker stack.
