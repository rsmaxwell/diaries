# 0031-FEAT Step 16 final runbook

Run this against the source state that you intend to close as 0031. Do not make source edits between the successful final regression capture and the close-out review unless the regression is repeated.

## 1. Apply the Step 16 source package

Apply the Diaries overlay, then run the local portable Step 16 gate once:

```bat
cd C:\Users\Richard\git\github.com\rsmaxwell\diaries-application\diaries
python scripts\windows\validation\verify-0031-step16.py
```

The Playbooks repository remains on the Ansible controller `mango` at `/home/richard/playbooks`; no Windows checkout is required. The final regression command below SSHes to `mango` and runs the existing Playbooks 0031 validators there.

## 2. Run the exact-candidate final regression

From the Diaries root:

```bat
scripts\windows\0031-step16\run-final-regression.bat
```

The script verifies Playbooks remotely using the normal defaults:

```text
SSH host: mango
remote repository: /home/richard/playbooks
```

If necessary these can be overridden with `-PlaybooksSshHost` and `-RemotePlaybooksRoot`.

A close-out-quality run must not use `-SkipJavaTests` or `-SkipClientBuild`.

Expected final lines:

```text
PASS: 0031-FEAT Step 16 final source/application regression completed.
Evidence: ...\evidence\Step 16\runtime\final-regression-YYYYMMDD-HHMMSS
Next: run rehearse-common-restore.bat and preserve that evidence before closing 0031.
```

Review `FINAL-REGRESSION-SUMMARY.txt`. The paired-override fixtures are temporary files inside the evidence directory; the script does not edit the real ignored `local.env`.

## 3. Stop local responders for the restore rehearsal

The Files reconciliation must see a stable local common root. Stop `diaries-local-responder`, `diaries-published-smoke-responder`, and any direct Windows responder on TCP/8081. The rehearsal checks this and refuses to continue if one is active.

Production does not need to be stopped: production now has its own mutable Files root and Step 14 has already established its explicit production pairing.

## 4. Confirm the normal common local pair

The real ignored `config\environments\local.env` must currently select both:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

The rehearsal uses the same shared dataset-pair validator as normal launch tooling and stops on any mismatch.

## 5. Run the disposable restore/reconciliation rehearsal

```bat
scripts\windows\0031-step16\rehearse-common-restore.bat
```

The default Step 8 backup is:

```text
data\database-backups\common\diaries-common-step8-premigration-20261002-142614.dump
```

with frozen SHA-256:

```text
d1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7
```

If the preserved dump has moved:

```bat
scripts\windows\0031-step16\rehearse-common-restore.bat ^
  -Step8Dump "D:\path\diaries-common-step8-premigration-20261002-142614.dump"
```

Expected final lines:

```text
PASS: Step 16 disposable common-dataset restore/reconciliation rehearsal succeeded.
Step 8 backup: ...
Files root: ...\files-development-common
Evidence: ...\evidence\Step 16\runtime\restore-rehearsal-YYYYMMDD-HHMMSS
```

The live common database is never restored or replaced. The Step 8 dump is restored only into a disposable Docker PostgreSQL container. The selected Files root is scanned read-only by the 0024 dry-run reconciliation.

## 6. Review the rehearsal evidence

`RESTORE-REHEARSAL-SUMMARY.json` must say:

```text
status = PASSED
effectiveDbDataDir = ./data/database/common
effectiveFilesDir = files-development-common
restoredDatabase = disposable Docker PostgreSQL; live local database not modified
reconciliationOutcome = DRY_RUN_COMPLETE
expectedCatalogueMatches = 85
conflicts = 0
```

`0024-conflicts.csv` must contain only its header.

## 7. Review acceptance and rollback

Read:

```text
evidence\Step 16\ACCEPTANCE-MATRIX.md
evidence\Step 16\ROLLBACK.md
```

The matrix deliberately references earlier authoritative runtime evidence rather than repeating destructive tests. There must be no unresolved criterion after the two Step 16 captures are added.

## 8. Feature close-out

After review:

1. update the Step 16 `CLOSE-OUT.md` decision to COMPLETE with the two authoritative runtime paths;
2. change the top-level 0031 status to Complete and check every acceptance criterion;
3. update the Step 16 block in `IMPLEMENTATION-STEPS.md` with the successful identities;
4. regenerate Step 16 `SHA256SUMS.txt`; and
5. move the full feature directory from `change-control/in-progress` to `change-control/complete`.

Do not move the feature while either Step 16 runtime capture is missing or failed.
