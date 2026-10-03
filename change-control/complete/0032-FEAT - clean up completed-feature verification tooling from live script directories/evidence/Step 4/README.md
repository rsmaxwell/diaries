# 0032 Step 4 — Windows development script and validation cleanup

## Status

**Implementation prepared; Windows application/verification required.**

The prepared source after-state implements the frozen Step 2 Windows disposition without changing the supported `common/`, `development-infrastructure/`, `local-docker-build/` or `local-published-smoke/` operational commands.

The patch:

- removes the seven completed 0031 live directories (`0031-step8`, `9`, `10`, `11`, `12`, `13`, `16`);
- removes the eight validators classified `ARCHIVE` in Step 2;
- promotes fourteen permanent validators/helpers to behaviour-oriented names from `RENAME-MAP.csv`;
- reduces the mixed Step 11 validator to current effective-dataset/runtime-path assertions only;
- updates `smoke-imagefragment-reader.cjs` to import the promoted helper names;
- updates `scripts/windows/README.md` and `scripts/windows/validation/README.md` so they no longer advertise retired live commands.

No normal start/status/backup/restore/reconciliation script was changed.

## Why an apply script is required

The normal drop-in ZIP can add and replace files but cannot delete obsolete paths already present in an extracted checkout. Therefore the ZIP also supplies:

```text
evidence/Step 4/scripts/run-step4-windows-cleanup.bat
```

After extracting the ZIP over the Diaries project, run that script from any directory. It:

1. verifies every promoted successor exists;
2. verifies the Step 3 archive manifest and archived checksums for files classified `ARCHIVE`;
3. refuses to remove a `0031-step*` directory if it contains any unexpected file/subdirectory;
4. removes only the frozen Step 4 directory/file allow-list;
5. captures the required `WINDOWS-SCRIPTS-AFTER.txt` and `WINDOWS-VALIDATION-AFTER.txt` inventories;
6. proves no retired live path/filename reference remains under `scripts/windows`;
7. runs the retained dataset/Files Python regressions, exact Windows PowerShell dataset-pair guard cases, the three renamed Node helper suites, and the focused direct-development runtime/Gradle check;
8. writes the complete transcript to `VALIDATION-OUTPUT.txt`.

It deliberately does **not** run the full disposable ImageFragment lifecycle smoke suite merely for this cleanup.

## Portable verification already performed

`PORTABLE-VALIDATION-OUTPUT.txt` records the verification run against the prepared source tree in the implementation environment:

- `verify-local-dataset-layout.py` — PASS;
- `verify-direct-development-files-config.py` — PASS (23 checks);
- `verify-dataset-pair-guard.py` — PASS;
- `verify-local-backup-restore-semantics.py` — PASS;
- `verify-effective-dataset-diagnostics.py` — PASS;
- `imagefragment-retained-snapshot.test.cjs` — 4/4 PASS;
- `imagefragment-image-http.test.cjs` — 4/4 PASS;
- `imagefragment-proxy-routing.test.cjs` — 3/3 PASS.

The exact Windows PowerShell/CMD regressions remain intentionally pending because they must be run on the Windows checkout after the physical deletion step.

## Evidence files

Before the Windows run, the four required Step 4 evidence files contain `PENDING` markers. The apply script overwrites them with actual checkout evidence:

```text
WINDOWS-SCRIPTS-AFTER.txt
WINDOWS-VALIDATION-AFTER.txt
REFERENCE-CHECK.txt
VALIDATION-OUTPUT.txt
```

`EXPECTED-WINDOWS-SCRIPTS-AFTER.txt` and `EXPECTED-WINDOWS-VALIDATION-AFTER.txt` record the prepared source after-state for comparison.

## Close-out rule

Step 4 may be marked complete only when the Windows apply/verification script exits successfully and the generated four evidence files show the cleaned live tree and passing retained regressions.
