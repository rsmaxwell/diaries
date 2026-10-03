# 0032-FEAT - Initial script inventory

Captured from the Diaries and Playbooks source bundles available when 0032 was opened on 2026-10-03, supplemented by the just-completed 0031 Step 16 tooling.

This is an **initial classification**, not a delete list. Implementation must still search current callers/references before moving anything.

## Windows development

### Historical 0031 feature-step directories — archive/remove candidates

```text
scripts/windows/0031-step8/
  README.md
  capture-local-database-backup.bat
  capture-local-database-backup.ps1
  capture-shared-files-snapshot.bat
  capture-shared-files-snapshot.ps1
  freeze-local-writes.bat
  freeze-local-writes.ps1

scripts/windows/0031-step9/
  README.md
  reconcile-local-shared-files.bat
  reconcile-local-shared-files.ps1

scripts/windows/0031-step10/
  README.md
  seed-local-files-root.bat
  seed-local-files-root.ps1

scripts/windows/0031-step11/
  README.md
  capture-local-mode.bat
  capture-local-mode.ps1
  compare-local-mode-evidence.ps1

scripts/windows/0031-step12/
  compare-step9-step12.py
  reconcile-common-pair.bat
  reconcile-common-pair.ps1

scripts/windows/0031-step13/
  README.md
  run-local-lifecycle.bat
  run-local-lifecycle.ps1
  step13-rpc.cjs

scripts/windows/0031-step16/
  final regression / restore-rehearsal tooling added during 0031 close-out
```

### Permanent-looking Windows infrastructure — retain subject to reference review

```text
scripts/windows/common/
scripts/windows/development-infrastructure/
scripts/windows/local-docker-build/
scripts/windows/local-published-smoke/
```

### Validation directory — classify test-by-test

The bundle contains:

```text
verify-0031-step3.py
verify-0031-step4.py
verify-0031-step4-runtime.bat
verify-0031-step6.ps1
verify-0031-step6.py
verify-0031-step7.py
verify-0031-step8.py
verify-0031-step9.py
verify-0031-step10.py
verify-0031-step11.py
verify-0031-step13.py
```

Step 16 later added its own verifier.

Tests which protect permanent behaviour should survive under feature-neutral names where practical. Tests whose only purpose is proving the existence/shape of retired migration tooling should be archived with 0031.

## Production / Playbooks

### Expected permanent operational scripts

```text
backup-db-to-binary.sh
backup-db-to-sql.sh
dataset-backup-manifest.py
restore-db-from-binary.sh
restore-db-from-sql.sh
```

These implement normal post-0031 backup/restore and matched database/Files safety semantics.

### Historical 0031 production tooling — archive/remove candidates

```text
step8-capture-production-database-backup.sh
step8-freeze-writes.sh
step9-reconcile-production.sh
step12-compare-reconciliation.py
step12-reconcile-production.sh
step13-capture-production-control.sh
step14-production-deployment.sh
```

These are currently beneath:

```text
roles/diaries/files/sync/scripts/
```

and therefore participate in the normal production sync.

### Explicit decision required

```text
migration0024ImageCatalogue.sh
```

Possible outcomes:

1. promote/rename as a supported permanent Image-catalogue reconciliation command; or
2. archive as completed migration tooling.

Do not remove it until current callers have been identified.

## Deployment cleanup observation

The current Ansible task synchronizes:

```text
roles/diaries/files/sync/
```

to the production project using `ansible.posix.synchronize` with:

```text
--omit-dir-times
```

but not `--delete`.

Therefore historical scripts already present on `pluto` will remain there after their source files are removed unless 0032 explicitly deletes those known deployed paths.

The preferred solution is a narrow `state: absent` list for retired helpers, not global sync deletion.

## Intended before/after evidence

0032 should close with three inventories:

```text
development Windows scripts: before / after
Playbooks role source scripts: before / after
pluto deployed scripts:       before / after
```

The close-out should also include a classification table with one row per moved/removed/renamed script, its final location, and the reason for its disposition.
