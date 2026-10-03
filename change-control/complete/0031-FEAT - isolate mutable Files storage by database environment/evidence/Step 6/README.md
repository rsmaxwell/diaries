# 0031-FEAT — Step 6 evidence

## Result

**COMPLETE — 2026-10-02.**

Step 6 adds a launch-time guard against accidentally re-sharing mutable Files storage with a different database dataset.

The previous scripts checked only the **effective** values after loading the committed mode environment and `local.env`. That could not detect the motivating failure mode: `local.env` could override `DIARIES_DB_DATA_DIR` alone while the old mode-specific `DIARIES_FILES_DIR` remained defined and appeared valid.

The common preflight reads the two files separately and requires durable-dataset overrides to be paired. It also rejects the production `files` selector in local modes and checks the frozen 0031 pairing whenever the effective database leaf is one of:

```text
development-infrastructure
local-docker-build
local-published-smoke
common
```

## Launch paths guarded

```text
scripts/windows/development-infrastructure/start.bat
scripts/windows/local-docker-build/start.bat
scripts/windows/local-published-smoke/start.bat
scripts/windows/development-infrastructure/prepare-responder-config.bat
```

The last path is shared by the direct Java responder and Image catalogue reconciliation/migration scripts, so those tools cannot bypass the same pair validation.

## Regression coverage

`scripts/windows/validation/verify-0031-step6.py` passes and proves:

- the three isolated committed defaults have three distinct database roots and three distinct Files roots;
- none of those local defaults selects production `files`;
- `local.env.example` contains the paired common override;
- all three local modes resolve exactly the same common database + Files pair when that override is applied;
- both local Docker responder mounts use `DIARIES_NAS_CONTENT_PATH/DIARIES_FILES_DIR`;
- the shared diary scans remain under `DIARIES_NAS_CONTENT_PATH/diaries`;
- the old hard-coded mutable `/files` subpath is absent from local Compose;
- direct/local launch paths invoke the common pair guard;
- the stable public URL remains `/files/...` and the Step 4 responder URL regression remains present;
- the corrected PowerShell source does not contain the unbraced `$variable:` interpolation hazard;
- the Windows verifier handles expected child-process rejection output without converting it into a parent-suite failure.

The Playbooks repository regression `roles/diaries/tests/verify-0031-storage-isolation.py` also passes. It proves the production role keeps an explicit Files selector, has no role fallback to production `files`, preserves the shared `/diaries` scan mount, and validates both mutable and read-only rendered mount contracts.

## Windows execution evidence

The exact Windows suite is:

```bat
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windowsalidationerify-0031-step6.ps1
```

Three workstation runs are retained because the first two found useful verifier defects:

1. `windows-runtime-verification-20261002-first-run.txt` — exposed invalid PowerShell interpolation of `$LocalEnvironmentFile:` / `$ModeName:`. The guard was corrected to braced interpolation.
2. `windows-runtime-verification-20261002-second-run.txt` — proved the positive cases and the DB-only rejection, then exposed verifier-only handling of expected child stderr under `ErrorActionPreference=Stop`.
3. `windows-runtime-verification-20261002-success.txt` — final successful run after both corrections.

The successful run reports PASS for:

```text
isolated defaults: development-infrastructure
shared common pair: development-infrastructure
isolated defaults: local-docker-build
shared common pair: local-docker-build
isolated defaults: local-published-smoke
shared common pair: local-published-smoke
reject DB-only local.env override
reject Files-only local.env override
reject local database with production Files root
reject crossed approved local pair
```

and finishes with:

```text
PASS: 0031-FEAT Step 6 Windows dataset-pair regression checks
```

This closes the remaining execution evidence. The mismatch that motivated 0031 is now covered by a repeatable guard and by successful execution on the supported Windows tooling.

## Responder URL test

A focused Gradle invocation was attempted, but Gradle 9.6.1 was not already available and the packaging environment had no external network access. The wrapper therefore failed while trying to reach `services.gradle.org`; see `gradle-regression-attempt.txt`. Step 6 does not change responder Java. The existing Step 4 URL regression remains in source and is checked statically by the Step 6 verifier.

## Data safety

No database, NAS Files content, Docker volume, MQTT retained state or production inventory was modified while implementing or verifying Step 6.

## Completion decision

Step 6 is complete because:

- the approved isolated and intentionally shared dataset pairings are guarded;
- one-sided and crossed overrides are rejected;
- accidental local use of the production Files root is rejected;
- the portable Diaries and Playbooks regression checks pass; and
- the exact Windows guard suite passes all positive and negative cases.
