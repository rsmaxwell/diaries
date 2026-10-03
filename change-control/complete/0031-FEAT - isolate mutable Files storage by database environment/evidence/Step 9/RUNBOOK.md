# 0031-FEAT — Step 9 runbook

> **Completed 2026-10-02.** This runbook is retained as the audit procedure used for the successful local and production reconciliations. See `CLOSE-OUT.md` and `DISPOSITION.md` for the final decision.

Step 8 is already complete. Keep both responder write paths stopped throughout
this runbook. Do not restart either responder between the local and production
reconciliation runs.

## 1. Run local reconciliation once

On Windows, from the Diaries project root, with the same one local database
container left running from Step 8:

```bat
scripts\windows\0031-step9\reconcile-local-shared-files.bat
```

When `local.env` selects `./data/database/common`, this one run is the
reconciliation for all three local execution modes. Do not run it three times.

Review the generated `STEP9-REPORT.md` and `STEP9-REPORT.json` under:

```text
change-control/in-progress/0031-FEAT - isolate mutable Files storage by database environment/evidence/Step 9/runtime/local-common-YYYYMMDD-HHMMSS/
```

## 2. Put the production helper on pluto without restarting the stack

The Playbooks source contains:

```text
roles/diaries/files/sync/scripts/step9-reconcile-production.sh
```

Because production is already frozen, avoid a full playbook run solely to
install this helper if that run would trigger a stack restart. Copy this one file
to:

```text
/home/richard/projects/diaries/scripts/step9-reconcile-production.sh
```

and make it executable:

```bash
chmod +x /home/richard/projects/diaries/scripts/step9-reconcile-production.sh
```

## 3. Run production reconciliation

On pluto:

```bash
cd /home/richard/projects/diaries
./scripts/step9-reconcile-production.sh
```

The helper refuses to proceed if `diaries-responder` is running or if
`DIARIES_FILES_DIR` is no longer `files`.

Retain the generated directory under:

```text
/home/richard/projects/diaries/data/0031-step9/production-YYYYMMDD-HHMMSS/
```

Copy the generated directory back into the permanent Step 9 evidence before
closing the step.

## 4. Decide whether Step 9 can close

For both reports inspect:

```text
catalogue.imageRowCount
catalogue.matchingPhysicalFiles
catalogue.missingPhysicalFiles
catalogue.untrackedPhysicalFiles
catalogue.untrackedSupportedImageFiles
catalogue.unsupportedPhysicalFiles
catalogue.metadataOrChecksumConflicts
catalogue.reconciliationConflictRows
staging.fileCount
step10Ready
requiresExplicitDisposition
```

If either report says `requiresExplicitDisposition=true`, do not start Step 10
until each item is explained and its treatment is written into the Step 9
evidence. In particular, do not blindly propagate the known pre-split
`.image-staging` recovery content into the new local Files root.

Do not run the 0024 reconciliation in `apply` mode as part of Step 9. This step
is inventory/reconciliation only.
