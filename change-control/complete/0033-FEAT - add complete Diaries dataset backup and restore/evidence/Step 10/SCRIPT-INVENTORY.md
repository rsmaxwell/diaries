# 0033 final script inventory and classification

0032 requires each feature-added script to be classified before close-out. The 0033 live tooling is intentionally feature-neutral in name and purpose.

## Diaries local — KEEP-OPERATIONAL

```text
scripts/windows/common/backup-dataset.ps1
scripts/windows/common/restore-dataset.ps1
scripts/windows/common/complete-dataset-manifest.py
scripts/windows/common/complete-dataset-verification.py
scripts/windows/common/complete-dataset-restore-stage.py
scripts/windows/common/complete-dataset-postflight.py
scripts/windows/development-infrastructure/backup-dataset.bat
scripts/windows/development-infrastructure/restore-dataset.bat
scripts/windows/local-docker-build/backup-dataset.bat
scripts/windows/local-docker-build/restore-dataset.bat
scripts/windows/local-published-smoke/backup-dataset.bat
scripts/windows/local-published-smoke/restore-dataset.bat
```

These are the supported local complete-dataset operator entry points and common implementation/verification helpers.

## Diaries local — KEEP-REGRESSION

```text
scripts/windows/validation/verify-complete-dataset-manifest.py
scripts/windows/validation/verify-local-complete-dataset-backup-engine.py
scripts/windows/validation/verify-local-complete-dataset-finalisation.py
scripts/windows/validation/verify-local-complete-dataset-restore-preparation.py
scripts/windows/validation/verify-local-complete-dataset-restore-apply.py
scripts/windows/validation/verify-local-complete-dataset-restore-postflight.py
```

These permanently protect the schema-2 media and local backup/restore safety contracts.

## Playbooks production — KEEP-OPERATIONAL

```text
roles/diaries/files/sync/scripts/backup-dataset.sh
roles/diaries/files/sync/scripts/restore-dataset.sh
roles/diaries/files/sync/scripts/production-complete-dataset.py
roles/diaries/files/sync/scripts/complete-dataset-manifest.py
roles/diaries/files/sync/scripts/complete-dataset-verification.py
roles/diaries/files/sync/scripts/complete-dataset-restore-stage.py
roles/diaries/files/sync/scripts/complete-dataset-postflight.py
```

These are the supported production complete-dataset commands and common helpers deployed by the role.

## Playbooks production — KEEP-REGRESSION

```text
roles/diaries/tests/verify-complete-dataset-manifest.py
roles/diaries/tests/verify-production-complete-dataset-tooling.py
```

Existing production deployment/storage/backup regressions also exercise the new tooling but were introduced by earlier features and are not reclassified here.

## ARCHIVE/REMOVE feature-only tooling

The Step-9 disposable rehearsal driver remains only here:

```text
change-control/complete/0033-FEAT - add complete Diaries dataset backup and restore/evidence/Step 9/tooling/run-disposable-rehearsal.ps1
```

It is historical evidence, not a live command. No `0033-*`, `step10-*` or rehearsal helper is added to `scripts/windows`, the Playbooks synchronized production script allow-list, or the deployed production script directory.

Python `__pycache__/` / `*.pyc` files are generated interpreter cache, not supported tooling. The Playbooks managed-script sync already excludes and deletes them from production; they should not be committed as source artifacts.
