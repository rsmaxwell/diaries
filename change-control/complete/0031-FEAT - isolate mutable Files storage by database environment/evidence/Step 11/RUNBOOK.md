# 0031-FEAT Step 11 runtime runbook

Run these checks on the Windows development workstation from the Diaries project root. Keep the **production responder stopped** throughout Step 11.

The normal `local.env` should contain the matched common pair:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

Do not proceed if any local `start.bat` reports a different or unpaired selection.

## 1. Direct Windows development

Start only the development infrastructure:

```bat
scripts\windows\development-infrastructure\start.bat
scripts\windows\development-infrastructure\status.bat
```

In a second Command Prompt, start the responder and capture its startup/runtime log:

```bat
if not exist build mkdir build

diaries-responder\scripts\windows\run-responder.bat > build\0031-step11-direct-responder.log 2>&1
```

Leave that responder running. In the first Command Prompt run:

```bat
scripts\windows\0031-step11\capture-local-mode.bat development-infrastructure -ProductionWriteFreezeConfirmed build\0031-step11-direct-responder.log
```

After it reports PASS, stop the responder with `Ctrl+C`, then stop the infrastructure:

```bat
scripts\windows\development-infrastructure\stop.bat
```

## 2. Local Docker build

Start and inspect the mode normally:

```bat
scripts\windows\local-docker-build\start.bat
scripts\windows\local-docker-build\status.bat
```

Capture Step 11 evidence:

```bat
scripts\windows\0031-step11\capture-local-mode.bat local-docker-build -ProductionWriteFreezeConfirmed
```

Then stop it before moving to the next mode:

```bat
scripts\windows\local-docker-build\stop.bat
```

## 3. Local published smoke

Start and inspect the mode normally:

```bat
scripts\windows\local-published-smoke\start.bat
scripts\windows\local-published-smoke\status.bat
```

Capture Step 11 evidence:

```bat
scripts\windows\0031-step11\capture-local-mode.bat local-published-smoke -ProductionWriteFreezeConfirmed
```

Then stop it:

```bat
scripts\windows\local-published-smoke\stop.bat
```

## 4. Compare the three captures

Run:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\0031-step11\compare-local-mode-evidence.ps1
```

Expected final messages for the normal common override include:

```text
PASS: all three local modes resolve the common database + files-development-common pair.
PASS: every runtime report retains /files and includes responder startup/runtime logs.
PASS: Step 11 cross-mode summary written ...
```

Do not perform upload/delete lifecycle tests yet. Step 12 first reconciles the newly selected database + Files pair against the Step 9 baseline.
