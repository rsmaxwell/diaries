# 0032 Step 2 — Final tooling disposition

## Status

**APPROVED / COMPLETE — 2026-10-03.**

Step 2 reviewed all 60 candidates frozen by Step 1 and assigns every candidate exactly one final disposition.

Final totals:

```text
ARCHIVE          43
PROMOTE/RENAME   17
KEEP-OPERATIONAL  0
KEEP-REGRESSION   0
REMOVE            0
-------------------
TOTAL             60
```

`REMOVE` is intentionally unused: historical tooling is preserved before live cleanup. `KEEP-REGRESSION` is also intentionally unused for feature/step-numbered candidates; lasting regression coverage is renamed to describe the behaviour it protects.

The machine-readable row-by-row decision is `FINAL-DISPOSITION.csv`.

## Explicit 0024 migration decision

`roles/diaries/files/sync/scripts/migration0024ImageCatalogue.sh` is **ARCHIVE**.

This is decision **B — completed migration tooling** from the Step 2 plan. The 0024 feature record says the development and production catalogue reconciliations were completed and 0024 was closed. The wrapper's interface is explicitly migration-oriented (`dry-run` / reviewed `apply`, 0024 evidence names and the `Migration0024ImageCatalogue` entry point). It therefore does not become a feature-neutral supported production administration command.

Approved archive path:

```text
change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/evidence/tooling/production/migration0024ImageCatalogue.sh
```

Later cleanup removes the Playbooks sync copy and the deployed `pluto` copy only after this historical copy is preserved. Other 0024-named source wrappers outside the frozen 60-candidate Step 1 inventory are not silently added to Step 2 scope.

## Permanent behaviour-oriented promotions

| Repo | Current path | Final live path | Historical copy |
| --- | --- | --- | --- |
| diaries | `scripts/windows/validation/step13-image-http.cjs` | `scripts/windows/validation/imagefragment-image-http.cjs` |  |
| diaries | `scripts/windows/validation/step13-image-http.test.cjs` | `scripts/windows/validation/imagefragment-image-http.test.cjs` |  |
| diaries | `scripts/windows/validation/step13-proxy-routing.cjs` | `scripts/windows/validation/imagefragment-proxy-routing.cjs` |  |
| diaries | `scripts/windows/validation/step13-proxy-routing.test.cjs` | `scripts/windows/validation/imagefragment-proxy-routing.test.cjs` |  |
| diaries | `scripts/windows/validation/step13-retained-snapshot.cjs` | `scripts/windows/validation/imagefragment-retained-snapshot.cjs` |  |
| diaries | `scripts/windows/validation/step13-retained-snapshot.test.cjs` | `scripts/windows/validation/imagefragment-retained-snapshot.test.cjs` |  |
| diaries | `scripts/windows/validation/verify-0026-step13.ps1` | `scripts/windows/validation/verify-imagefragment-reader.ps1` |  |
| diaries | `scripts/windows/validation/verify-0031-step11.py` | `scripts/windows/validation/verify-effective-dataset-diagnostics.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step11.py` |
| diaries | `scripts/windows/validation/verify-0031-step3.py` | `scripts/windows/validation/verify-local-dataset-layout.py` |  |
| diaries | `scripts/windows/validation/verify-0031-step4-runtime.bat` | `scripts/windows/validation/verify-direct-development-files-runtime.bat` |  |
| diaries | `scripts/windows/validation/verify-0031-step4.py` | `scripts/windows/validation/verify-direct-development-files-config.py` |  |
| diaries | `scripts/windows/validation/verify-0031-step6.ps1` | `scripts/windows/validation/verify-dataset-pair-guard.ps1` |  |
| diaries | `scripts/windows/validation/verify-0031-step6.py` | `scripts/windows/validation/verify-dataset-pair-guard.py` |  |
| diaries | `scripts/windows/validation/verify-0031-step7.py` | `scripts/windows/validation/verify-local-backup-restore-semantics.py` |  |
| playbooks | `roles/diaries/tests/verify-0031-backup-semantics.py` | `roles/diaries/tests/verify-production-backup-restore-semantics.py` |  |
| playbooks | `roles/diaries/tests/verify-0031-step14.py` | `roles/diaries/tests/verify-production-deployment-contract.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/playbooks/verify-0031-step14.py` |
| playbooks | `roles/diaries/tests/verify-0031-storage-isolation.py` | `roles/diaries/tests/verify-production-storage-isolation.py` |  |


Two promotions are deliberate **splits**, not blind renames:

- `scripts/windows/validation/verify-0031-step11.py` becomes `verify-effective-dataset-diagnostics.py` containing only current diagnostics/start/status/mount/public-route assertions. Assertions that only validate the retired Step 11 capture/comparison harness or Step 11 evidence are archived with the original validator.
- `roles/diaries/tests/verify-0031-step14.py` becomes `verify-production-deployment-contract.py` containing current broker queue policy, explicit Files selection, no-local-override and deployment-policy assertions. Assertions that only validate `step14-production-deployment.sh` or its historical runbook are archived with the original validator.

The two `verify-0031-step16.py` files are **not** promoted. They are final feature-closeout aggregation gates, tied to 0031 Step 16 tooling/evidence and to other feature-numbered validators. Their lasting lower-level behaviour is retained by the neutral tests above; both Step 16 gates are archived.

## Historical tooling to archive

| Repo | Current live path | Approved archive path |
| --- | --- | --- |
| diaries | `scripts/windows/0031-step10/seed-local-files-root.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step10/seed-local-files-root.bat` |
| diaries | `scripts/windows/0031-step10/seed-local-files-root.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step10/seed-local-files-root.ps1` |
| diaries | `scripts/windows/0031-step11/capture-local-mode.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step11/capture-local-mode.bat` |
| diaries | `scripts/windows/0031-step11/capture-local-mode.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step11/capture-local-mode.ps1` |
| diaries | `scripts/windows/0031-step11/compare-local-mode-evidence.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step11/compare-local-mode-evidence.ps1` |
| diaries | `scripts/windows/0031-step12/compare-step9-step12.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step12/compare-step9-step12.py` |
| diaries | `scripts/windows/0031-step12/reconcile-common-pair.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step12/reconcile-common-pair.bat` |
| diaries | `scripts/windows/0031-step12/reconcile-common-pair.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step12/reconcile-common-pair.ps1` |
| diaries | `scripts/windows/0031-step13/run-local-lifecycle.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step13/run-local-lifecycle.bat` |
| diaries | `scripts/windows/0031-step13/run-local-lifecycle.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step13/run-local-lifecycle.ps1` |
| diaries | `scripts/windows/0031-step13/step13-rpc.cjs` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step13/step13-rpc.cjs` |
| diaries | `scripts/windows/0031-step16/rehearse-common-restore.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step16/rehearse-common-restore.bat` |
| diaries | `scripts/windows/0031-step16/rehearse-common-restore.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step16/rehearse-common-restore.ps1` |
| diaries | `scripts/windows/0031-step16/run-final-regression.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step16/run-final-regression.bat` |
| diaries | `scripts/windows/0031-step16/run-final-regression.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step16/run-final-regression.ps1` |
| diaries | `scripts/windows/0031-step8/capture-local-database-backup.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/capture-local-database-backup.bat` |
| diaries | `scripts/windows/0031-step8/capture-local-database-backup.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/capture-local-database-backup.ps1` |
| diaries | `scripts/windows/0031-step8/capture-shared-files-snapshot.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/capture-shared-files-snapshot.bat` |
| diaries | `scripts/windows/0031-step8/capture-shared-files-snapshot.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/capture-shared-files-snapshot.ps1` |
| diaries | `scripts/windows/0031-step8/freeze-local-writes.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/freeze-local-writes.bat` |
| diaries | `scripts/windows/0031-step8/freeze-local-writes.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step8/freeze-local-writes.ps1` |
| diaries | `scripts/windows/0031-step9/reconcile-local-shared-files.bat` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step9/reconcile-local-shared-files.bat` |
| diaries | `scripts/windows/0031-step9/reconcile-local-shared-files.ps1` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/step9/reconcile-local-shared-files.ps1` |
| diaries | `scripts/windows/validation/test-verify-0026-step14.py` | `change-control/complete/0026-FEAT - render ImageFragments in diaries-web/evidence/tooling/validation/test-verify-0026-step14.py` |
| diaries | `scripts/windows/validation/verify-0026-step14.ps1` | `change-control/complete/0026-FEAT - render ImageFragments in diaries-web/evidence/tooling/validation/verify-0026-step14.ps1` |
| diaries | `scripts/windows/validation/verify-0026-step14.py` | `change-control/complete/0026-FEAT - render ImageFragments in diaries-web/evidence/tooling/validation/verify-0026-step14.py` |
| diaries | `scripts/windows/validation/verify-0031-step10.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step10.py` |
| diaries | `scripts/windows/validation/verify-0031-step13.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step13.py` |
| diaries | `scripts/windows/validation/verify-0031-step16.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step16.py` |
| diaries | `scripts/windows/validation/verify-0031-step8.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step8.py` |
| diaries | `scripts/windows/validation/verify-0031-step9.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/diaries/verify-0031-step9.py` |
| playbooks | `roles/diaries/files/sync/scripts/migration0024ImageCatalogue.sh` | `change-control/complete/0024-FEAT - introduce reusable persistent Image catalogue/evidence/tooling/production/migration0024ImageCatalogue.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step12-compare-reconciliation.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step12-compare-reconciliation.py` |
| playbooks | `roles/diaries/files/sync/scripts/step12-reconcile-production.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step12-reconcile-production.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step13-capture-production-control.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step13-capture-production-control.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step14-production-deployment.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step14-production-deployment.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step8-capture-production-database-backup.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step8-capture-production-database-backup.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step8-freeze-writes.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step8-freeze-writes.sh` |
| playbooks | `roles/diaries/files/sync/scripts/step9-reconcile-production.sh` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/step9-reconcile-production.sh` |
| playbooks | `roles/diaries/tests/verify-0031-step13.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/playbooks/verify-0031-step13.py` |
| playbooks | `roles/diaries/tests/verify-0031-step16.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/playbooks/verify-0031-step16.py` |
| playbooks | `roles/diaries/tests/verify-0031-step8.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/playbooks/verify-0031-step8.py` |
| playbooks | `roles/diaries/tests/verify-0031-step9.py` | `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/validation/playbooks/verify-0031-step9.py` |


## Caller-update rule

A rename/archive is not complete merely because the file moved. Each implementation step must use the Step 1 `REFERENCE-MAP.md` and update all active callers atomically. In particular:

- `smoke-imagefragment-reader.cjs` must import the three renamed ImageFragment helper modules;
- `verify-imagefragment-reader.ps1` must invoke the three renamed helper test files;
- the 0026 Step 14 historical verifier must be archived rather than kept as a caller of the renamed 0026 Step 13 wrapper;
- the 0031 final regression runners/validators are archived, so they must not remain as live callers of renamed validators;
- the production Step 14 → Step 12 → migration0024 chain is historical and is archived as one dependency cluster rather than partially kept alive.

## Safety boundary

Step 2 changes only change-control decisions. It does **not** move, rename, delete or deploy any live script/test and does not change application data, PostgreSQL, Files data, MQTT retained state or production services.
