# 0031-FEAT Step 16 runtime tooling

Step 16 closes 0031 only after the exact Diaries + Playbooks candidate passes the final regression gate **and** the preserved Step 8 common database backup is successfully restored into a disposable PostgreSQL instance and reconciled read-only against the intended `files-development-common` root.

The tooling deliberately does not overwrite the live local database, production database, production Files tree, or the common local Files root.

## 1. Final cross-repository regression

From the Diaries project root on Windows:

```bat
scripts\windows\0031-step16\run-final-regression.bat
```

The Playbooks repository is verified **remotely on the Ansible controller**. The defaults match the normal installation:

```text
SSH host: mango
Playbooks root: /home/richard/playbooks
```

So the normal command remains:

```bat
scripts\windows\0031-step16\run-final-regression.bat
```

If either remote value ever changes, override it explicitly:

```bat
scripts\windows\0031-step16\run-final-regression.bat ^
  -PlaybooksSshHost mango ^
  -RemotePlaybooksRoot /home/richard/playbooks
```

This runs all current 0031 portable Diaries checks locally, invokes the existing Playbooks 0031 checks over SSH on `mango`, an explicit temporary precedence test for isolated defaults/common paired override/one-sided rejection, the full Gradle Java test suite, and the Angular client production build. It records an exact-candidate SHA-256 identity set and a final effective path map under Step 16 runtime evidence.

`-SkipJavaTests` and `-SkipClientBuild` exist only for diagnosis. A run using either switch is not sufficient for feature close-out unless the omission is explicitly reviewed and replaced by equivalent evidence.

## 2. Disposable restore/reconciliation rehearsal

Stop local responders first; the script refuses to run when a local Docker responder or TCP/8081 listener is active.

Then run:

```bat
scripts\windows\0031-step16\rehearse-common-restore.bat
```

The default dump is the Step 8 backup:

```text
data\database-backups\common\diaries-common-step8-premigration-20261002-142614.dump
```

and its frozen SHA-256 must be:

```text
d1af825c12ea21084d6dd240af15dfb22be96ee33db6f36ad0368f0bf67afcb7
```

If the backup lives elsewhere, pass `-Step8Dump` explicitly.

The rehearsal:

1. requires the real ignored `local.env` to select `./data/database/common` + `files-development-common`;
2. reuses the normal dataset-pair validator;
3. verifies the Step 8 dump checksum before starting;
4. starts a disposable `postgres:18-alpine` container on an ephemeral localhost port;
5. restores the Step 8 dump into that disposable database;
6. builds a minimal temporary responder migration configuration selecting the actual `files-development-common` root;
7. runs 0024 reconciliation in `dry-run` mode only;
8. requires 85 catalogue matches, no conflict rows and no unsafe reconciliation statuses; and
9. removes the temporary config and disposable PostgreSQL container.

No database restore is performed against the normal local database container. The Files tree is scanned read-only by the reconciliation command.

## 3. Close-out

Preserve the two successful evidence directories referenced by:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 16/LATEST-FINAL-REGRESSION.txt
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 16/LATEST-RESTORE-REHEARSAL.txt
```

Then review the Step 16 acceptance matrix and rollback instructions. Only after every acceptance criterion is evidenced should the feature directory be moved from `change-control/in-progress` to `change-control/complete`.
