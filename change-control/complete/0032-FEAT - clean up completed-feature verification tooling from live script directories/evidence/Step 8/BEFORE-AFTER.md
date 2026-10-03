# 0032 Step 8 - final before/after inventory comparison

## Status

Prepared from the frozen Step 1 before inventories, the actual Step 4/5 source after-state and the verified Step 6 `pluto` post-deployment inventory.

| Area | Before | After | Net | Final result |
| --- | ---: | ---: | ---: | --- |
| Windows `scripts/windows` files | 108 | 72 | -36 | seven completed `0031-step*` directories removed; permanent validators promoted to feature-neutral names; Step 7 recurrence guard added |
| Windows permanent validation files | 28 | 21 | -7 | historical structural validators archived; behavioural checks retained/renamed; `verify-live-script-policy.py` added |
| Playbooks `roles/diaries/files/sync/scripts` files | 14 | 6 | -8 | eight historical migration/control helpers removed; five supported data tools plus README remain |
| Playbooks `roles/diaries/tests` files | 7 | 3 | -4 | historical step tests archived; three behaviour-oriented permanent regressions remain |
| `pluto:/home/richard/projects/diaries/scripts` files | 23 | 15 | -8 | exactly eight approved retired helpers removed; supported static and templated operator scripts remain |

## Windows source delta

The whole Windows tree changed from 108 files to 72 files. The filename-level comparison has 51 removals and 15 additions because promoted validators appear as a removed feature/step name plus an added behaviour-oriented name.

### Removed paths

```text
0031-step10/README.md
0031-step10/seed-local-files-root.bat
0031-step10/seed-local-files-root.ps1
0031-step11/README.md
0031-step11/capture-local-mode.bat
0031-step11/capture-local-mode.ps1
0031-step11/compare-local-mode-evidence.ps1
0031-step12/compare-step9-step12.py
0031-step12/reconcile-common-pair.bat
0031-step12/reconcile-common-pair.ps1
0031-step13/README.md
0031-step13/run-local-lifecycle.bat
0031-step13/run-local-lifecycle.ps1
0031-step13/step13-rpc.cjs
0031-step16/README.md
0031-step16/rehearse-common-restore.bat
0031-step16/rehearse-common-restore.ps1
0031-step16/run-final-regression.bat
0031-step16/run-final-regression.ps1
0031-step8/README.md
0031-step8/capture-local-database-backup.bat
0031-step8/capture-local-database-backup.ps1
0031-step8/capture-shared-files-snapshot.bat
0031-step8/capture-shared-files-snapshot.ps1
0031-step8/freeze-local-writes.bat
0031-step8/freeze-local-writes.ps1
0031-step9/README.md
0031-step9/reconcile-local-shared-files.bat
0031-step9/reconcile-local-shared-files.ps1
validation/step13-image-http.cjs
validation/step13-image-http.test.cjs
validation/step13-proxy-routing.cjs
validation/step13-proxy-routing.test.cjs
validation/step13-retained-snapshot.cjs
validation/step13-retained-snapshot.test.cjs
validation/test-verify-0026-step14.py
validation/verify-0026-step13.ps1
validation/verify-0026-step14.ps1
validation/verify-0026-step14.py
validation/verify-0031-step10.py
validation/verify-0031-step11.py
validation/verify-0031-step13.py
validation/verify-0031-step16.py
validation/verify-0031-step3.py
validation/verify-0031-step4-runtime.bat
validation/verify-0031-step4.py
validation/verify-0031-step6.ps1
validation/verify-0031-step6.py
validation/verify-0031-step7.py
validation/verify-0031-step8.py
validation/verify-0031-step9.py
```

### Added/promoted paths

```text
validation/imagefragment-image-http.cjs
validation/imagefragment-image-http.test.cjs
validation/imagefragment-proxy-routing.cjs
validation/imagefragment-proxy-routing.test.cjs
validation/imagefragment-retained-snapshot.cjs
validation/imagefragment-retained-snapshot.test.cjs
validation/verify-dataset-pair-guard.ps1
validation/verify-dataset-pair-guard.py
validation/verify-direct-development-files-config.py
validation/verify-direct-development-files-runtime.bat
validation/verify-effective-dataset-diagnostics.py
validation/verify-imagefragment-reader.ps1
validation/verify-live-script-policy.py
validation/verify-local-backup-restore-semantics.py
validation/verify-local-dataset-layout.py
```

## Windows permanent validation delta

The validation tree changed from 28 files to 21 files.

### Removed historical/old-name validation paths

```text
step13-image-http.cjs
step13-image-http.test.cjs
step13-proxy-routing.cjs
step13-proxy-routing.test.cjs
step13-retained-snapshot.cjs
step13-retained-snapshot.test.cjs
test-verify-0026-step14.py
verify-0026-step13.ps1
verify-0026-step14.ps1
verify-0026-step14.py
verify-0031-step10.py
verify-0031-step11.py
verify-0031-step13.py
verify-0031-step16.py
verify-0031-step3.py
verify-0031-step4-runtime.bat
verify-0031-step4.py
verify-0031-step6.ps1
verify-0031-step6.py
verify-0031-step7.py
verify-0031-step8.py
verify-0031-step9.py
```

### Added/promoted permanent validation paths

```text
imagefragment-image-http.cjs
imagefragment-image-http.test.cjs
imagefragment-proxy-routing.cjs
imagefragment-proxy-routing.test.cjs
imagefragment-retained-snapshot.cjs
imagefragment-retained-snapshot.test.cjs
verify-dataset-pair-guard.ps1
verify-dataset-pair-guard.py
verify-direct-development-files-config.py
verify-direct-development-files-runtime.bat
verify-effective-dataset-diagnostics.py
verify-imagefragment-reader.ps1
verify-live-script-policy.py
verify-local-backup-restore-semantics.py
verify-local-dataset-layout.py
```

## Playbooks production script-source delta

The synchronized static script source changed from 14 files to 6 files.

### Removed

```text
migration0024ImageCatalogue.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
step8-capture-production-database-backup.sh
step8-freeze-writes.sh
step9-reconcile-production.sh
```

### Added

No new production operator script was introduced by the cleanup. The retained README was rewritten in place; the retained five static operational tools keep their existing names.

## Playbooks permanent-test delta

The role test directory changed from 7 files to 3 files.

### Removed historical/old-name tests

```text
verify-0031-backup-semantics.py
verify-0031-step13.py
verify-0031-step14.py
verify-0031-step16.py
verify-0031-step8.py
verify-0031-step9.py
verify-0031-storage-isolation.py
```

### Added/promoted tests

```text
verify-production-backup-restore-semantics.py
verify-production-deployment-contract.py
verify-production-storage-isolation.py
```

## `pluto` deployed-script delta

The verified Step 6 deployment changed the production script directory from 23 files to 15 files.

Exactly these eight deployed files were removed:

```text
scripts/migration0024ImageCatalogue.sh
scripts/step12-compare-reconciliation.py
scripts/step12-reconcile-production.sh
scripts/step13-capture-production-control.sh
scripts/step14-production-deployment.sh
scripts/step8-capture-production-database-backup.sh
scripts/step8-freeze-writes.sh
scripts/step9-reconcile-production.sh
```

No unapproved deployed file was added by the cleanup.

Step 6 evidence also proves the retained supported production files remained present, the five static source-managed helpers matched approved source hashes, production configuration fingerprints/selectors were unchanged, and all required Diaries services were healthy.

## Step 7 managed-directory refinement

After Step 6, Step 7 refined the future deployment mechanism so `scripts/` is synchronized as its own managed directory with `--delete` and `--delete-excluded`, while the wider project-root sync excludes `scripts/`. Templated permanent scripts are explicitly protected during rsync and then rendered by Ansible normally.

That refinement does not change the expected 15-file `pluto` inventory above. Its source contract and synthetic rsync semantics are covered by Step 7 and the final Playbooks deployment-contract regression.
