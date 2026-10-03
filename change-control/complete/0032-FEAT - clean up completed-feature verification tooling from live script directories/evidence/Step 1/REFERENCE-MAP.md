# 0032 Step 1 - Reference map

Captured from the supplied Diaries and Playbooks source snapshots on 2026-10-03.

## Search boundary

- Diaries snapshot: `diaries-sources-20261003-120114.zip` (`75e91b5c3f22a60a32c5e64e81ded06bf519d6252b6591b916dd2ae9632c7d82`).
- Playbooks snapshot: `playbook-sources-20261003-115130.zip` (`0cacf4845e3b55aa3189d39eee0556929304d0a3863cc76684ef5bbf3c3638e6`).
- Searches cover both supplied repositories and the change-control records present in the source snapshot.
- Historical evidence payload directories are intentionally absent from the current Diaries source bundle, so references that exist only inside excluded runtime evidence are outside this source-reference scan. They are historical by definition and cannot be active runtime/build/deployment callers.
- A reference is not treated as a blocker merely because it exists. Active code/test/documentation callers are distinguished below from historical records and 0032 itself.

## Reference categories

| Category | Meaning |
| --- | --- |
| `ACTIVE-CODE-CALLER` | current non-test script/source invokes or imports the candidate |
| `FEATURE-TOOL-CALLER` | another feature-step helper invokes/requires the candidate |
| `DIRECTORY-DEPLOYMENT-CALLER` | Ansible deploys the containing sync tree, even without a filename literal |
| `TEST/VALIDATION-CALLER` | current test or validation code reads/invokes the candidate |
| `LIVE-DOCUMENTATION` | current operator/developer documentation names the candidate |
| `HISTORICAL-RECORD` | completed change-control/history reference |
| `CURRENT-0032-RECORD` | the cleanup feature itself names the candidate |
| `PACKAGE-METADATA` | checksum/apply/validation packaging metadata; not a runtime caller |
| `LIVE-SOURCE-REFERENCE` | other live source reference requiring review |

## Important active dependency clusters

- `smoke-imagefragment-reader.cjs` actively imports `step13-image-http.cjs`, `step13-proxy-routing.cjs`, and `step13-retained-snapshot.cjs`. Those helpers therefore cannot simply be archived; Step 2 should promote/rename them or update the smoke runner atomically.
- `verify-0026-step13.ps1` runs the three `step13-*.test.cjs` suites. The wrapper is feature-numbered but the underlying checks still exercise current reader/MQTT/HTTP behaviour.
- Every file beneath `roles/diaries/files/sync/scripts/` is also an implicit active deployment input because `roles/diaries/tasks/copy.yaml` synchronizes the whole `sync/` tree; the task does not need a filename literal for a script to be deployed.
- `step14-production-deployment.sh` actively invokes `step12-reconcile-production.sh`, which actively invokes both `migration0024ImageCatalogue.sh` and `step12-compare-reconciliation.py`. These production helpers are a dependency cluster and must be disposed of together rather than independently.
- `migration0024ImageCatalogue.sh` also has current responder documentation and a responder-side sibling script/task. This confirms the explicit Step 2 decision is required.
- `verify-0031-step16.py` and the Step 16 final-regression harness aggregate earlier 0031 verifiers. These are active source references today, but they are feature-close-out callers rather than normal application/runtime callers.

## Candidate-by-candidate references

### `diaries:scripts/windows/0031-step10/seed-local-files-root.bat`

- **Purpose:** 0031 Step 10 one-time Files-root seeding tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 28 | `seed-local-files-root.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step10/README.md` | 48 | `scripts\windows\0031-step10\seed-local-files-root.bat -ProductionWriteFreezeConfirmed` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step10/README.md` | 58 | `scripts\windows\0031-step10\seed-local-files-root.bat ^` |

### `diaries:scripts/windows/0031-step10/seed-local-files-root.ps1`

- **Purpose:** 0031 Step 10 one-time Files-root seeding tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 29 | `seed-local-files-root.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step10/seed-local-files-root.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%seed-local-files-root.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step10.py` | 19 | `script = (STEP10 / "seed-local-files-root.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/0031-step11/capture-local-mode.bat`

- **Purpose:** 0031 Step 11 effective runtime-path evidence capture/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 33 | `capture-local-mode.bat` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step11/capture-local-mode.ps1` | 314 | `'Direct responder log was not supplied. Re-run capture-local-mode.bat with the log path before Step 11 close-out.' \|` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step11/README.md` | 25 | `scripts\windows\0031-step11\capture-local-mode.bat local-docker-build -ProductionWriteFreezeConfirmed` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step11/README.md` | 26 | `scripts\windows\0031-step11\capture-local-mode.bat local-published-smoke -ProductionWriteFreezeConfirmed` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step11/README.md` | 38 | `scripts\windows\0031-step11\capture-local-mode.bat development-infrastructure -ProductionWriteFreezeConfirmed build\0031-step11-direct-responder.log` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step11.py` | 44 | `wrapper = text(STEP11 / "capture-local-mode.bat")` |

### `diaries:scripts/windows/0031-step11/capture-local-mode.ps1`

- **Purpose:** 0031 Step 11 effective runtime-path evidence capture/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 34 | `capture-local-mode.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step11/capture-local-mode.bat` | 29 | `set "COLLECTOR=%PROJECT_DIR%\scripts\windows\0031-step11\capture-local-mode.ps1"` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step11.py` | 45 | `collector = text(STEP11 / "capture-local-mode.ps1")` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step11.py` | 82 | `for name, script in (("capture-local-mode.ps1", collector), ("compare-local-mode-evidence.ps1", comparer)):` |

### `diaries:scripts/windows/0031-step11/compare-local-mode-evidence.ps1`

- **Purpose:** 0031 Step 11 effective runtime-path evidence capture/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 35 | `compare-local-mode-evidence.ps1` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 690 | `All three resolved the common pair `./data/database/common` + `files-development-common`. The two Docker modes proved the effective database mount, selected NAS subpath -> `/dat...` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step11/README.md` | 56 | `powershell -NoProfile -ExecutionPolicy Bypass -File scripts\windows\0031-step11\compare-local-mode-evidence.ps1` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step11.py` | 46 | `comparer = text(STEP11 / "compare-local-mode-evidence.ps1")` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step11.py` | 82 | `for name, script in (("capture-local-mode.ps1", collector), ("compare-local-mode-evidence.ps1", comparer)):` |

### `diaries:scripts/windows/0031-step12/compare-step9-step12.py`

- **Purpose:** 0031 Step 12 post-split reconciliation/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 38 | `compare-step9-step12.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step12/reconcile-common-pair.ps1` | 77 | `$comparator = Join-Path $scriptDir 'compare-step9-step12.py'` |
| `PACKAGE-METADATA` | `diaries:PACKAGE-SHA256SUMS.txt` | 4 | `fe5452e778eadafbe35c5cea2b3ad069f5606cd5cbc4d9f0dc9f23c9efdefce3  ./scripts/windows/0031-step12/compare-step9-step12.py` |
| `PACKAGE-METADATA` | `diaries:VALIDATION-STEP12.txt` | 4 | `- compare-step9-step12.py: Python byte-compilation PASS.` |

### `diaries:scripts/windows/0031-step12/reconcile-common-pair.bat`

- **Purpose:** 0031 Step 12 post-split reconciliation/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 39 | `reconcile-common-pair.bat` |
| `PACKAGE-METADATA` | `diaries:PACKAGE-SHA256SUMS.txt` | 5 | `8dbc105ebc37b3e56b057ceaa220f6f58e64ecfcccb9d3f03c419882326168df  ./scripts/windows/0031-step12/reconcile-common-pair.bat` |
| `PACKAGE-METADATA` | `diaries:README-STEP12-APPLY.txt` | 13 | `scripts\windows\0031-step12\reconcile-common-pair.bat -ProductionWriteFreezeConfirmed` |

### `diaries:scripts/windows/0031-step12/reconcile-common-pair.ps1`

- **Purpose:** 0031 Step 12 post-split reconciliation/comparison tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 40 | `reconcile-common-pair.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step12/reconcile-common-pair.bat` | 6 | `pwsh -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-common-pair.ps1" %*` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step12/reconcile-common-pair.bat` | 8 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-common-pair.ps1" %*` |
| `PACKAGE-METADATA` | `diaries:PACKAGE-SHA256SUMS.txt` | 6 | `4bda72319c0ea1dffbede4b6a1417044e8d64ea47c65f32d5facbe82458dc424  ./scripts/windows/0031-step12/reconcile-common-pair.ps1` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 100 | `step12 = text("scripts/windows/0031-step12/reconcile-common-pair.ps1")` |

### `diaries:scripts/windows/0031-step13/run-local-lifecycle.bat`

- **Purpose:** 0031 Step 13 controlled cross-dataset Image lifecycle evidence tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 44 | `run-local-lifecycle.bat` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 769 | `**Step 13 implementation note — 2026-10-02.** Repeatable runtime tooling was implemented to support the controlled runtime proof. `scripts/windows/0031-step13/run-local-lifecycl...` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step13/README.md` | 11 | `scripts\windows\0031-step13\run-local-lifecycle.bat -Action upload` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step13/README.md` | 12 | `scripts\windows\0031-step13\run-local-lifecycle.bat -Action observe -RunDirectory "<run-directory>"` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step13/README.md` | 13 | `scripts\windows\0031-step13\run-local-lifecycle.bat -Action delete -RunDirectory "<run-directory>"` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step13/README.md` | 20 | `scripts\windows\0031-step13\run-local-lifecycle.bat -Action cleanup -ImageId <id>` |

### `diaries:scripts/windows/0031-step13/run-local-lifecycle.ps1`

- **Purpose:** 0031 Step 13 controlled cross-dataset Image lifecycle evidence tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 45 | `run-local-lifecycle.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step13/run-local-lifecycle.bat` | 3 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run-local-lifecycle.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step13.py` | 23 | `ps = (LOCAL / "run-local-lifecycle.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/0031-step13/step13-rpc.cjs`

- **Purpose:** 0031 Step 13 controlled cross-dataset Image lifecycle evidence tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 46 | `step13-rpc.cjs` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step13/run-local-lifecycle.ps1` | 253 | `$helper = Join-Path $ScriptDir 'step13-rpc.cjs'` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step13.py` | 24 | `rpc = (LOCAL / "step13-rpc.cjs").read_text(encoding="utf-8")` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step13.py` | 59 | `"step13-rpc.cjs cleanup" not in ps,` |

### `diaries:scripts/windows/0031-step16/rehearse-common-restore.bat`

- **Purpose:** 0031 Step 16 final regression / rollback rehearsal harness
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 319 | `Write-Host 'Next: run rehearse-common-restore.bat and preserve that evidence before closing 0031.'` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step16/README.md` | 47 | `scripts\windows\0031-step16\rehearse-common-restore.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 252 | `Static verification is not sufficient to close Step 16. The Windows runtime gate under `scripts/windows/0031-step16/` must also be run. `run-final-regression.bat` executes the e...` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 5 | `separate: run-final-regression.bat and rehearse-common-restore.bat.` |

### `diaries:scripts/windows/0031-step16/rehearse-common-restore.ps1`

- **Purpose:** 0031 Step 16 final regression / rollback rehearsal harness
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/rehearse-common-restore.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%rehearse-common-restore.ps1" %*` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 268 | `'scripts/windows/0031-step16/rehearse-common-restore.ps1',` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 124 | `rehearsal = text("scripts/windows/0031-step16/rehearse-common-restore.ps1")` |

### `diaries:scripts/windows/0031-step16/run-final-regression.bat`

- **Purpose:** 0031 Step 16 final regression / rollback rehearsal harness
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step16/README.md` | 12 | `scripts\windows\0031-step16\run-final-regression.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step16/README.md` | 25 | `scripts\windows\0031-step16\run-final-regression.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step16/README.md` | 31 | `scripts\windows\0031-step16\run-final-regression.bat ^` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 252 | `Static verification is not sufficient to close Step 16. The Windows runtime gate under `scripts/windows/0031-step16/` must also be run. `run-final-regression.bat` executes the e...` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 5 | `separate: run-final-regression.bat and rehearse-common-restore.bat.` |

### `diaries:scripts/windows/0031-step16/run-final-regression.ps1`

- **Purpose:** 0031 Step 16 final regression / rollback rehearsal harness
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%run-final-regression.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 123 | `runner = text("scripts/windows/0031-step16/run-final-regression.ps1")` |

### `diaries:scripts/windows/0031-step8/capture-local-database-backup.bat`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 14 | `capture-local-database-backup.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 17 | `3. Windows: capture-local-database-backup.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 36 | `## `capture-local-database-backup.bat`` |

### `diaries:scripts/windows/0031-step8/capture-local-database-backup.ps1`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 15 | `capture-local-database-backup.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-local-database-backup.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%capture-local-database-backup.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step8.py` | 22 | `db = (STEP8 / "capture-local-database-backup.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.bat`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 16 | `capture-shared-files-snapshot.bat` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-local-database-backup.ps1` | 210 | `Write-Evidence 'The shared Files bytes are NOT captured by this script; run capture-shared-files-snapshot.bat only after production writes are also frozen.'` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 19 | `5. Windows: capture-shared-files-snapshot.bat -ProductionWriteFreezeConfirmed` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 62 | `## `capture-shared-files-snapshot.bat`` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 77 | `capture-shared-files-snapshot.bat ^` |

### `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.ps1`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 17 | `capture-shared-files-snapshot.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%capture-shared-files-snapshot.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step8.py` | 23 | `files = (STEP8 / "capture-shared-files-snapshot.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/0031-step8/freeze-local-writes.bat`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 18 | `freeze-local-writes.bat` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-local-database-backup.ps1` | 84 | `throw "Local responder container '$container' is running. Run freeze-local-writes.bat before taking the Step 8 backup."` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.ps1` | 70 | `if ($running -contains $container) { throw "Local responder '$container' is running. Re-run freeze-local-writes.bat." }` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.ps1` | 73 | `if ($listeners.Count -gt 0) { throw 'TCP/8081 is listening locally. Re-run freeze-local-writes.bat and stop the direct responder.' }` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 15 | `1. Windows: freeze-local-writes.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 24 | `## `freeze-local-writes.bat`` |

### `diaries:scripts/windows/0031-step8/freeze-local-writes.ps1`

- **Purpose:** 0031 Step 8 write-freeze / pre-migration backup / shared Files snapshot tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 19 | `freeze-local-writes.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/freeze-local-writes.bat` | 4 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%freeze-local-writes.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step8.py` | 21 | `freeze = (STEP8 / "freeze-local-writes.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/0031-step9/reconcile-local-shared-files.bat`

- **Purpose:** 0031 Step 9 read-only reconciliation against pre-split shared Files
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 23 | `reconcile-local-shared-files.bat` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step9/README.md` | 3 | ``reconcile-local-shared-files.bat` performs the local half of Step 9 against the` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step9/README.md` | 26 | `scripts\windows\0031-step9\reconcile-local-shared-files.bat` |

### `diaries:scripts/windows/0031-step9/reconcile-local-shared-files.ps1`

- **Purpose:** 0031 Step 9 read-only reconciliation against pre-split shared Files
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/windows/`
- **Reason:** completed 0031 migration/evidence/runtime harness

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 24 | `reconcile-local-shared-files.ps1` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step9/reconcile-local-shared-files.bat` | 8 | `powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%reconcile-local-shared-files.ps1" %*` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 96 | `step9 = text("scripts/windows/0031-step9/reconcile-local-shared-files.ps1")` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step9.py` | 17 | `script = (STEP9 / "reconcile-local-shared-files.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/validation/step13-image-http.cjs`

- **Purpose:** Image byte/path diagnostics used by current ImageFragment smoke runner
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/smoke-imagefragment-reader.cjs` | 13 | `const { inspectImageBytes } = require('./step13-image-http.cjs');` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/step13-image-http.test.cjs` | 5 | `const {cataloguePublicPath, inspectImageBytes} = require('./step13-image-http.cjs');` |

### `diaries:scripts/windows/validation/step13-image-http.test.cjs`

- **Purpose:** focused regression tests for corresponding ImageFragment smoke helper
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step13.ps1` | 73 | `& node (Join-Path $PSScriptRoot 'step13-image-http.test.cjs')` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.py` | 272 | `for filename in ['step13-retained-snapshot.test.cjs', 'step13-image-http.test.cjs', 'step13-proxy-routing.test.cjs']:` |

### `diaries:scripts/windows/validation/step13-proxy-routing.cjs`

- **Purpose:** mutable local proxy helper used by current ImageFragment smoke runner
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/smoke-imagefragment-reader.cjs` | 14 | `const { startMutableProxy, setPublishedPort } = require('./step13-proxy-routing.cjs');` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/step13-proxy-routing.test.cjs` | 5 | `const {setPublishedPort,startMutableProxy}=require('./step13-proxy-routing.cjs');` |

### `diaries:scripts/windows/validation/step13-proxy-routing.test.cjs`

- **Purpose:** focused regression tests for corresponding ImageFragment smoke helper
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 189 | ``step13-proxy-routing.test.cjs` regression suite before the clean build.` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step13.ps1` | 77 | `& node (Join-Path $PSScriptRoot 'step13-proxy-routing.test.cjs')` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.py` | 272 | `for filename in ['step13-retained-snapshot.test.cjs', 'step13-image-http.test.cjs', 'step13-proxy-routing.test.cjs']:` |

### `diaries:scripts/windows/validation/step13-retained-snapshot.cjs`

- **Purpose:** retained MQTT snapshot helper used by current ImageFragment smoke runner
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 137 | `The runner uses `step13-retained-snapshot.cjs` to snapshot the Image and Fragment` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/smoke-imagefragment-reader.cjs` | 12 | `const { makeRetainedSnapshot } = require('./step13-retained-snapshot.cjs');` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/step13-retained-snapshot.test.cjs` | 7 | `const { makeRetainedSnapshot } = require('./step13-retained-snapshot.cjs');` |

### `diaries:scripts/windows/validation/step13-retained-snapshot.test.cjs`

- **Purpose:** focused regression tests for corresponding ImageFragment smoke helper
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 135 | `Before building, the wrapper runs `step13-retained-snapshot.test.cjs` to exercise` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step13.ps1` | 69 | `& node (Join-Path $PSScriptRoot 'step13-retained-snapshot.test.cjs')` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.py` | 272 | `for filename in ['step13-retained-snapshot.test.cjs', 'step13-image-http.test.cjs', 'step13-proxy-routing.test.cjs']:` |

### `diaries:scripts/windows/validation/test-verify-0026-step14.py`

- **Purpose:** 0026 Step 14 full regression/artifact-verifier tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

No references outside the candidate file were found in either supplied repository snapshot.

### `diaries:scripts/windows/validation/verify-0026-step13.ps1`

- **Purpose:** disposable cross-component ImageFragment reader verification wrapper
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 79 | ``verify-0026-step13.ps1` runs the controlled cross-component development verification for` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 85 | `.\scripts\windows\validation\verify-0026-step13.ps1 `` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.py` | 335 | `script = SCRIPTS / 'verify-0026-step13.ps1'` |

### `diaries:scripts/windows/validation/verify-0026-step14.ps1`

- **Purpose:** 0026 Step 14 full regression/artifact-verifier tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 193 | ``verify-0026-step14.ps1` runs the Java 25 full web suite/build, requires non-skipped selected` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.py` | 4 | `Run via verify-0026-step14.ps1 from the Diaries root. Stdlib-only so it can` |

### `diaries:scripts/windows/validation/verify-0026-step14.py`

- **Purpose:** 0026 Step 14 full regression/artifact-verifier tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/test-verify-0026-step14.py` | 9 | `p = Path(__file__).with_name('verify-0026-step14.py')` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0026-step14.ps1` | 15 | `$arguments = @((Join-Path $PSScriptRoot 'verify-0026-step14.py'), '--evidence', $EvidenceDirectory)` |

### `diaries:scripts/windows/validation/verify-0031-step10.py`

- **Purpose:** structural verification of 0031 Step 10 seeding tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 74 | `verify-0031-step10.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 169 | `'verify-0031-step10.py',` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 225 | ``verify-0031-step10.py` performs portable source/contract checks for the Step 10` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 235 | `python scripts/windows/validation/verify-0031-step10.py` |

### `diaries:scripts/windows/validation/verify-0031-step11.py`

- **Purpose:** mixed current diagnostics checks and 0031 Step 11 evidence-tooling checks
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 75 | `verify-0031-step11.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 170 | `'verify-0031-step11.py',` |

### `diaries:scripts/windows/validation/verify-0031-step13.py`

- **Purpose:** structural verification of 0031 Step 13 lifecycle tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 76 | `verify-0031-step13.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 171 | `'verify-0031-step13.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 187 | `'verify-0031-step13.py',` |

### `diaries:scripts/windows/validation/verify-0031-step16.py`

- **Purpose:** 0031 final release-candidate gate tied to Step 16 tooling/evidence
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 172 | `'verify-0031-step16.py'` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 269 | `'scripts/windows/validation/verify-0031-step16.py'` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 244 | ``verify-0031-step16.py` is the portable static gate for the final 0031 release candidate. It checks the committed independent defaults, paired `local.env` precedence, fail-fast ...` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 249 | `python scripts/windows/validation/verify-0031-step16.py` |

### `diaries:scripts/windows/validation/verify-0031-step3.py`

- **Purpose:** local database/Files selector and Compose mount contract
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 66 | `verify-0031-step3.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 163 | `'verify-0031-step3.py',` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 310 | `**Completed 2026-10-01.** The three committed local mode environments now carry explicit Files defaults, and `local.env.example` carries the approved common database/Files pair....` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/README.md` | 27 | `- **Step 3 complete — 2026-10-01:** all three committed local mode environments now define an explicit `DIARIES_FILES_DIR`; `local.env.example` demonstrates the paired common ov...` |

### `diaries:scripts/windows/validation/verify-0031-step4-runtime.bat`

- **Purpose:** runtime check for generated responder config and stable public URL
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 68 | `verify-0031-step4-runtime.bat` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 376 | `**Implemented 2026-10-01.** Direct Windows responder and Image reconciliation now share one effective-config preparation path. The helper loads `development-infrastructure.env` ...` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step4.py` | 28 | `runtime_bat = text("scripts/windows/validation/verify-0031-step4-runtime.bat")` |

### `diaries:scripts/windows/validation/verify-0031-step4.py`

- **Purpose:** direct Windows generated responder configuration and stable /files contract
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 67 | `verify-0031-step4.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 164 | `'verify-0031-step4.py',` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 376 | `**Implemented 2026-10-01.** Direct Windows responder and Image reconciliation now share one effective-config preparation path. The helper loads `development-infrastructure.env` ...` |

### `diaries:scripts/windows/validation/verify-0031-step6.ps1`

- **Purpose:** Windows execution coverage for dataset-pair guard positive/negative cases
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 69 | `verify-0031-step6.ps1` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 473 | `**Complete — 2026-10-02.** `scripts/windows/common/validate-dataset-pair.ps1` is the common local preflight, with a small batch wrapper for launch-script reuse. It inspects the ...` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step6.py` | 4 | `The exact PowerShell guard is exercised by verify-0031-step6.ps1 on Windows.` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step6.py` | 130 | `ps_test = (ROOT / "scripts/windows/validation/verify-0031-step6.ps1").read_text(encoding="utf-8")` |

### `diaries:scripts/windows/validation/verify-0031-step6.py`

- **Purpose:** portable local storage-isolation and dataset-pair guard regression
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 70 | `verify-0031-step6.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 165 | `'verify-0031-step6.py',` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 473 | `**Complete — 2026-10-02.** `scripts/windows/common/validate-dataset-pair.ps1` is the common local preflight, with a small batch wrapper for launch-script reuse. It inspects the ...` |

### `diaries:scripts/windows/validation/verify-0031-step7.py`

- **Purpose:** local database-only backup/restore pairing and manifest semantics
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `scripts/windows/validation/<feature-neutral-name>`
- **Reason:** contains current behavioural regression coverage or is imported by a current generic smoke runner

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 71 | `verify-0031-step7.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 166 | `'verify-0031-step7.py',` |

### `diaries:scripts/windows/validation/verify-0031-step8.py`

- **Purpose:** structural verification of 0031 Step 8 migration tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 72 | `verify-0031-step8.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 167 | `'verify-0031-step8.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 185 | `'verify-0031-step8.py',` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 205 | ``verify-0031-step8.py` performs portable source checks for the Step 8 Windows` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 215 | `python scripts/windows/validation/verify-0031-step8.py` |

### `diaries:scripts/windows/validation/verify-0031-step9.py`

- **Purpose:** structural verification of 0031 Step 9 reconciliation tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed feature evidence/tooling archive`
- **Reason:** primarily validates completed-feature step tooling/evidence rather than a stable behaviour contract

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 73 | `verify-0031-step9.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 168 | `'verify-0031-step9.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 186 | `'verify-0031-step9.py',` |

### `playbooks:roles/diaries/files/sync/scripts/migration0024ImageCatalogue.sh`

- **Purpose:** production wrapper for Image catalogue migration/reconciliation JavaExec
- **Initial classification:** `PENDING`
- **Initial final location:** `TBD in Step 2`
- **Reason:** explicit 0024 migration-vs-supported-administration decision required by 0032 Step 2

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `ACTIVE-CODE-CALLER` | `diaries:diaries-responder/scripts/files/migration0024ImageCatalogue.sh` | 6 | `# migration0024ImageCatalogue.sh` |
| `ACTIVE-CODE-CALLER` | `diaries:diaries-responder/scripts/files/migration0024ImageCatalogue.sh` | 13 | `#     migration0024ImageCatalogue.sh dry-run [0022_CANDIDATES_CSV]` |
| `ACTIVE-CODE-CALLER` | `diaries:diaries-responder/scripts/files/migration0024ImageCatalogue.sh` | 14 | `#     migration0024ImageCatalogue.sh apply   [0022_CANDIDATES_CSV]` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 77 | ``migration0024ImageCatalogue.sh` requires an explicit supported-vs-historical decision.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 106 | `9. Treat `migration0024ImageCatalogue.sh` as an explicit design decision, not an automatic cleanup candidate.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 246 | `### `migration0024ImageCatalogue.sh`` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 284 | `Every candidate has an approved final classification/path and `migration0024ImageCatalogue.sh` has an explicit decision.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 414 | `3. implement the Step 2 decision for `migration0024ImageCatalogue.sh`:` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 696 | `\| `migration0024ImageCatalogue.sh` has explicit disposition \| Steps 2 and 5 \|` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 713 | `6. the `migration0024ImageCatalogue.sh` decision is implemented and documented;` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 120 | `migration0024ImageCatalogue.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 101 | `migration0024ImageCatalogue.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 257 | `## `migration0024ImageCatalogue.sh` Decision` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 259 | ``migration0024ImageCatalogue.sh` needs an explicit decision rather than automatic removal.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 358 | `- [ ] Decide whether `migration0024ImageCatalogue.sh` is promoted to a supported feature-neutral reconciliation command or archived.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 376 | `- [ ] The disposition of `migration0024ImageCatalogue.sh` is explicit and documented.` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 398 | `The 0024/0030 Image catalogue lifecycle should be consulted only for the `migration0024ImageCatalogue.sh` disposition. No data migration dependency is introduced.` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `FEATURE-TOOL-CALLER` | `playbooks:roles/diaries/files/sync/scripts/step12-reconcile-production.sh` | 28 | `MIGRATION="${SCRIPT_DIR}/migration0024ImageCatalogue.sh"` |
| `LIVE-DOCUMENTATION` | `diaries:diaries-responder/README.md` | 596 | ``migration0024ImageCatalogue.sh` under the production project's `scripts`` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step14.py` | 60 | `require("migration0024ImageCatalogue.sh" not in script and "--mode apply" not in script,` |

### `playbooks:roles/diaries/files/sync/scripts/step12-compare-reconciliation.py`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 72 | `step12-compare-reconciliation.py` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 103 | `step12-compare-reconciliation.py` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 107 | `step12-compare-reconciliation.py` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 215 | `step12-compare-reconciliation.py` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `FEATURE-TOOL-CALLER` | `playbooks:roles/diaries/files/sync/scripts/step12-reconcile-production.sh` | 29 | `COMPARATOR="${SCRIPT_DIR}/step12-compare-reconciliation.py"` |
| `PACKAGE-METADATA` | `playbooks:PACKAGE-SHA256SUMS.txt` | 3 | `fe5452e778eadafbe35c5cea2b3ad069f5606cd5cbc4d9f0dc9f23c9efdefce3  ./roles/diaries/files/sync/scripts/step12-compare-reconciliation.py` |
| `PACKAGE-METADATA` | `playbooks:README-STEP12-APPLY.txt` | 7 | `roles/diaries/files/sync/scripts/step12-compare-reconciliation.py` |
| `PACKAGE-METADATA` | `playbooks:README-STEP12-APPLY.txt` | 16 | `chmod +x scripts/step12-reconcile-production.sh scripts/step12-compare-reconciliation.py` |
| `PACKAGE-METADATA` | `playbooks:VALIDATION-STEP12.txt` | 4 | `- step12-compare-reconciliation.py: Python byte-compilation PASS.` |

### `playbooks:roles/diaries/files/sync/scripts/step12-reconcile-production.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 71 | `step12-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 104 | `step12-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 108 | `step12-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 214 | `step12-reconcile-production.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `FEATURE-TOOL-CALLER` | `playbooks:roles/diaries/files/sync/scripts/step14-production-deployment.sh` | 50 | `STEP12_RUNNER="${SCRIPT_DIR}/step12-reconcile-production.sh"` |
| `PACKAGE-METADATA` | `playbooks:PACKAGE-SHA256SUMS.txt` | 4 | `900184c6f0e3570ad3004af7c3828feddbe38adb800257ec6a854a5aebda4327  ./roles/diaries/files/sync/scripts/step12-reconcile-production.sh` |
| `PACKAGE-METADATA` | `playbooks:README-STEP12-APPLY.txt` | 6 | `roles/diaries/files/sync/scripts/step12-reconcile-production.sh` |
| `PACKAGE-METADATA` | `playbooks:README-STEP12-APPLY.txt` | 16 | `chmod +x scripts/step12-reconcile-production.sh scripts/step12-compare-reconciliation.py` |
| `PACKAGE-METADATA` | `playbooks:README-STEP12-APPLY.txt` | 17 | `./scripts/step12-reconcile-production.sh --write-freeze-confirmed` |
| `PACKAGE-METADATA` | `playbooks:VALIDATION-STEP12.txt` | 5 | `- step12-reconcile-production.sh: bash -n PASS.` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step14.py` | 55 | `require("step12-reconcile-production.sh" in script and "--write-freeze-confirmed" in script,` |

### `playbooks:roles/diaries/files/sync/scripts/step13-capture-production-control.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 73 | `step13-capture-production-control.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 105 | `step13-capture-production-control.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 109 | `step13-capture-production-control.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 216 | `step13-capture-production-control.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 769 | `**Step 13 implementation note — 2026-10-02.** Repeatable runtime tooling was implemented to support the controlled runtime proof. `scripts/windows/0031-step13/run-local-lifecycl...` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 126 | `./scripts/step13-capture-production-control.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 136 | `./scripts/step13-capture-production-control.sh before` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 137 | `./scripts/step13-capture-production-control.sh after /home/richard/projects/diaries/data/0031-step13/production-before-YYYYMMDD-HHMMSS` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 146 | `Copy only `step13-capture-production-control.sh` into the deployed project's` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step13.py` | 7 | `SCRIPT = ROOT / "roles/diaries/files/sync/scripts/step13-capture-production-control.sh"` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step13.py` | 33 | `require("0031 Step 13" in readme and "step13-capture-production-control.sh" in readme,` |

### `playbooks:roles/diaries/files/sync/scripts/step14-production-deployment.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 74 | `step14-production-deployment.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 106 | `step14-production-deployment.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 110 | `step14-production-deployment.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 217 | `step14-production-deployment.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 155 | `./scripts/step14-production-deployment.sh` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step14.py` | 7 | `SCRIPT = ROOT / "roles/diaries/files/sync/scripts/step14-production-deployment.sh"` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step14.py` | 66 | `require("0031 Step 14" in readme and "step14-production-deployment.sh" in readme,` |

### `playbooks:roles/diaries/files/sync/scripts/step8-capture-production-database-backup.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 69 | `step8-capture-production-database-backup.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 437 | `- step8-capture-production-database-backup.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 100 | `step8-capture-production-database-backup.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 104 | `step8-capture-production-database-backup.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 212 | `step8-capture-production-database-backup.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 18 | `4. pluto:   ./scripts/step8-capture-production-database-backup.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 61 | `./scripts/step8-capture-production-database-backup.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 72 | `Then run `step8-capture-production-database-backup.sh`. It refuses to continue if` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step8.py` | 19 | `capture = (SCRIPTS / "step8-capture-production-database-backup.sh").read_text(encoding="utf-8")` |

### `playbooks:roles/diaries/files/sync/scripts/step8-freeze-writes.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 68 | `step8-freeze-writes.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 436 | `- step8-freeze-writes.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 101 | `step8-freeze-writes.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 105 | `step8-freeze-writes.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 211 | `step8-freeze-writes.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step8/capture-shared-files-snapshot.ps1` | 102 | `throw 'Production write freeze confirmation is required. Run the deployed production step8-freeze-writes.sh first, then rerun with -ProductionWriteFreezeConfirmed.'` |
| `FEATURE-TOOL-CALLER` | `playbooks:roles/diaries/files/sync/scripts/step8-capture-production-database-backup.sh` | 47 | `echo "Run ${SCRIPT_DIR}/step8-freeze-writes.sh first." >&2` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/0031-step8/README.md` | 16 | `2. pluto:   ./scripts/step8-freeze-writes.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 60 | `./scripts/step8-freeze-writes.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 64 | `Run `step8-freeze-writes.sh` first. It stops only `diaries-responder`, because the` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step8.py` | 18 | `freeze = (SCRIPTS / "step8-freeze-writes.sh").read_text(encoding="utf-8")` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step8.py` | 29 | `require("Run ${SCRIPT_DIR}/step8-freeze-writes.sh first" in capture,` |

### `playbooks:roles/diaries/files/sync/scripts/step9-reconcile-production.sh`

- **Purpose:** feature/step-specific verification tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/evidence/tooling/production/`
- **Reason:** completed 0031 production migration/reconciliation/deployment helper

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/IMPLEMENTATION-STEPS.md` | 70 | `step9-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 102 | `step9-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 106 | `step9-reconcile-production.sh` |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/README.md` | 213 | `step9-reconcile-production.sh` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/copy.yaml` | 36 | `ansible.posix.synchronize deploys the complete sync/ tree to the production project` |
| `DIRECTORY-DEPLOYMENT-CALLER` | `playbooks:roles/diaries/tasks/main.yaml` | 36 | `main task imports copy.yaml under the copy tag` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 93 | `./scripts/step9-reconcile-production.sh` |
| `LIVE-DOCUMENTATION` | `playbooks:roles/diaries/files/sync/scripts/README.md` | 117 | `stack. Copy only `step9-reconcile-production.sh` into the deployed project's` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step9.py` | 16 | `script = (SCRIPTS / "step9-reconcile-production.sh").read_text(encoding="utf-8")` |

### `playbooks:roles/diaries/tests/verify-0031-backup-semantics.py`

- **Purpose:** production database-only backup/restore pairing and manifest semantics
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `roles/diaries/tests/<feature-neutral-name>`
- **Reason:** protects current production backup/storage-isolation behaviour

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 184 | `'verify-0031-backup-semantics.py',` |

### `playbooks:roles/diaries/tests/verify-0031-step13.py`

- **Purpose:** structural verification of 0031 Step 13 lifecycle tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed 0031 evidence/tooling archive`
- **Reason:** primarily validates completed 0031 feature-step tooling

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 76 | `verify-0031-step13.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 171 | `'verify-0031-step13.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 187 | `'verify-0031-step13.py',` |

### `playbooks:roles/diaries/tests/verify-0031-step14.py`

- **Purpose:** Step 14 deployment helper plus current retained-snapshot broker/config policy assertions
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `roles/diaries/tests/<feature-neutral-name> plus archive`
- **Reason:** mixed: historical Step 14 checks plus current broker/config assertions; split/promote permanent assertions before archiving historical remainder

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 149 | `$remotePreflight = "test -d $quotedRemoteRoot && test -f $quotedRemoteRoot/roles/diaries/tests/verify-0031-step14.py && printf 'OK\n'"` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 188 | `'verify-0031-step14.py'` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 286 | `'roles/diaries/tests/verify-0031-step14.py'` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 125 | `require("verify-0031-step16.py" in runner and "verify-0031-step14.py" in runner,` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step16.py` | 50 | `step14 = read("tests/verify-0031-step14.py")` |

### `playbooks:roles/diaries/tests/verify-0031-step16.py`

- **Purpose:** 0031 final release-candidate gate tied to Step 16 tooling/evidence
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `roles/diaries/tests/<feature-neutral-name>`
- **Reason:** protects current production backup/storage-isolation behaviour

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 172 | `'verify-0031-step16.py'` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 269 | `'scripts/windows/validation/verify-0031-step16.py'` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 244 | ``verify-0031-step16.py` is the portable static gate for the final 0031 release candidate. It checks the committed independent defaults, paired `local.env` precedence, fail-fast ...` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 249 | `python scripts/windows/validation/verify-0031-step16.py` |
| `TEST/VALIDATION-CALLER` | `diaries:scripts/windows/validation/verify-0031-step16.py` | 125 | `require("verify-0031-step16.py" in runner and "verify-0031-step14.py" in runner,` |

### `playbooks:roles/diaries/tests/verify-0031-step8.py`

- **Purpose:** structural verification of 0031 Step 8 migration tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed 0031 evidence/tooling archive`
- **Reason:** primarily validates completed 0031 feature-step tooling

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 72 | `verify-0031-step8.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 167 | `'verify-0031-step8.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 185 | `'verify-0031-step8.py',` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 205 | ``verify-0031-step8.py` performs portable source checks for the Step 8 Windows` |
| `LIVE-DOCUMENTATION` | `diaries:scripts/windows/validation/README.md` | 215 | `python scripts/windows/validation/verify-0031-step8.py` |

### `playbooks:roles/diaries/tests/verify-0031-step9.py`

- **Purpose:** structural verification of 0031 Step 9 reconciliation tooling
- **Initial classification:** `ARCHIVE`
- **Initial final location:** `completed 0031 evidence/tooling archive`
- **Reason:** primarily validates completed 0031 feature-step tooling

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `CURRENT-0032-RECORD` | `diaries:change-control/in-progress/0032-FEAT - clean up completed-feature verification tooling from live script directories/INITIAL-SCRIPT-INVENTORY.md` | 73 | `verify-0031-step9.py` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 168 | `'verify-0031-step9.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 186 | `'verify-0031-step9.py',` |

### `playbooks:roles/diaries/tests/verify-0031-storage-isolation.py`

- **Purpose:** production explicit Files selector/storage-isolation contract
- **Initial classification:** `PROMOTE/RENAME`
- **Initial final location:** `roles/diaries/tests/<feature-neutral-name>`
- **Reason:** protects current production backup/storage-isolation behaviour

| Type | Reference | Line | Match |
| --- | --- | ---: | --- |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 183 | `'verify-0031-storage-isolation.py',` |
| `FEATURE-TOOL-CALLER` | `diaries:scripts/windows/0031-step16/run-final-regression.ps1` | 285 | `'roles/diaries/tests/verify-0031-storage-isolation.py',` |
| `HISTORICAL-RECORD` | `diaries:change-control/complete/0031-FEAT - isolate mutable Files storage by database environment/IMPLEMENTATION-STEPS.md` | 473 | `**Complete — 2026-10-02.** `scripts/windows/common/validate-dataset-pair.ps1` is the common local preflight, with a small batch wrapper for launch-script reuse. It inspects the ...` |
| `TEST/VALIDATION-CALLER` | `playbooks:roles/diaries/tests/verify-0031-step16.py` | 51 | `storage = read("tests/verify-0031-storage-isolation.py")` |

## Runtime deployment reconciliation — `pluto`

The source-reference scan was completed with a read-only runtime inventory captured on `pluto` at `2026-10-03T12:39:30+01:00`.

The deployed `scripts/` directory contains 23 files. Every filename is explained by the current Playbooks deployment model: 14 come from `roles/diaries/files/sync/scripts/` and 9 are rendered from `roles/diaries/templates/scripts/*.j2` by `roles/diaries/tasks/copy.yaml`. There are no unexplained deployed-only scripts.

All seven 0031 production `stepN-*` cleanup candidates and `migration0024ImageCatalogue.sh` are present on `pluto` and match the frozen Playbooks source by size and SHA-256. The only synchronized-file fingerprint mismatch is `README.md`; this is documentation drift, not an executable dependency or hidden cleanup candidate.

This closes the runtime evidence gap that existed when the initial source-side reference map was generated. See `PLUTO-RECONCILIATION.md` for the exact comparison.
