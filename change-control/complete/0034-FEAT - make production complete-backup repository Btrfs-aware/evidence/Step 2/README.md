# 0034-FEAT Step 2 evidence — explicit production complete-backup configuration contract

Date prepared: 2026-10-08  
Status: **CLOSED — 2026-10-08 (source regression and production preflight verified)**

## Purpose

Step 2 removes the production complete-dataset engine's implicit dependency on the project-local paths introduced by 0033. The mutable Files identity, complete-backup repository, and complete-restore state are now three separately identified configuration inputs.

The schema-2 media format, full-copy capture implementation, writer-quiescence behaviour, verification gate and restore semantics remain unchanged. No Btrfs capability probe or reflink seeding is introduced in this step; those belong to Step 3 and later.

## Playbooks contract

The Diaries role now defines these explicit variables:

```yaml
diaries_complete_backup_repository_root: "{{ diaries_project_dir }}/data/dataset-backups/production"
diaries_complete_restore_state_root: "{{ diaries_project_dir }}/data/dataset-restores/production"
diaries_complete_backup_storage_mode: auto
```

The path defaults deliberately preserve the frozen 0033 production baseline on `pluto`. Applying Step 2 by itself therefore does **not** relocate existing backup media or restore state. A later inventory override can point `diaries_complete_backup_repository_root` at the deliberately provisioned Btrfs repository without changing the Python code.

The role validates that the two configured roots are non-empty absolute POSIX paths and are not equal. The production engine additionally rejects equal or nested backup/restore roots.

The mutable Files root remains independently identified by the existing production dataset configuration:

```text
DIARIES_NAS_CONTENT_PATH + DIARIES_FILES_DIR
        -> responder Docker volume /data/files
        -> resolved physical/UNC Files root in production preflight
```

The complete-backup repository and restore-state roots remain host-side paths and are not derived from the mutable Files selector.

## Generated runtime contract

`roles/diaries/templates/.env.j2` now renders:

```text
DIARIES_COMPLETE_BACKUP_REPOSITORY_ROOT={{ diaries_complete_backup_repository_root }}
DIARIES_COMPLETE_RESTORE_STATE_ROOT={{ diaries_complete_restore_state_root }}
DIARIES_COMPLETE_BACKUP_STORAGE_MODE={{ diaries_complete_backup_storage_mode }}
```

For the current defaults on `pluto`, the expected rendered values are:

```text
DIARIES_FILES_DIR=files
DIARIES_COMPLETE_BACKUP_REPOSITORY_ROOT=/home/richard/projects/diaries/data/dataset-backups/production
DIARIES_COMPLETE_RESTORE_STATE_ROOT=/home/richard/projects/diaries/data/dataset-restores/production
DIARIES_COMPLETE_BACKUP_STORAGE_MODE=auto
```

The production complete-dataset engine now requires these values from deployed `.env`; it no longer contains the 0033 expressions which constructed `data/dataset-backups/production` or `data/dataset-restores/production` from the project path. Backup and restore preflight output also reports the effective repository root, restore-state root and configured storage mode.

## Storage-mode contract

Exactly these values are accepted:

```text
auto
required-btrfs
full-copy
```

Their feature-level semantics remain the 0034 contract:

- `auto` — use reflink-aware seeding only when the actual repository proves Btrfs + reflink capability; otherwise full copy;
- `required-btrfs` — require Btrfs + a successful reflink probe and fail closed otherwise;
- `full-copy` — deliberately use the frozen 0033 physical-copy path.

Step 2 establishes and validates these names as runtime configuration. Until Step 3 implements repository capability probing and effective strategy selection, the existing capture implementation remains the frozen 0033 full-copy path. Production should therefore retain the default `auto` and should not be deliberately switched to `required-btrfs` as an operational Btrfs assertion until Step 3 is installed.

## Permanent regression coverage

The permanent Playbooks regressions now verify that:

```text
all three supported storage-mode names are accepted
invalid mode names are rejected
equal backup/restore roots are rejected
nested backup/restore roots are rejected
.env renders all three new inputs
Ansible creates the configured roots
production-complete-dataset.py consumes those inputs
the Python engine no longer infers roots from project layout
the existing mutable Files selector remains independent
schema-2 helper fingerprints and 0033 restore semantics remain unchanged
```

The full regression transcript is retained as `SOURCE-REGRESSION.txt`.

## Step boundary

This step does **not** choose the eventual Btrfs mount path. The 0034 design intentionally leaves that path to production provisioning/inventory. It also does not call `findmnt`, probe `cp --reflink=always`, choose a base backup, reconcile a reflink clone, or alter restore. Those are subsequent steps.

No Docker image build is required for Step 2. The runtime changes are Playbooks-managed `.env`, operator script and documentation changes.

## Formal close-out (2026-10-08)

Step 2 is **CLOSED**. Source regression and deployed production preflight evidence is retained in this directory:

- `RUNTIME-MANGO-REGRESSIONS.txt`: all five permanent Playbooks regression commands completed successfully, including the Step 2 storage-isolation assertions, negative mode/path tests, schema-2 manifest and restore/deployment regressions. The transcript ends with `PASS: production storage-isolation contract verified`.
- `RUNTIME-PLUTO-PREFLIGHT.txt`: `./backup-dataset.sh preflight` succeeded on `pluto` with `PREFLIGHT OK: no writer was stopped and no backup workspace was created.`

The observed runtime contract is:

```text
logical dataset:     production
database identity:   docker-volume:diaries-db-data / diaries
Files selector:      files
backup repository:   /home/richard/projects/diaries/data/dataset-backups/production
restore state root:  /home/richard/projects/diaries/data/dataset-restores/production
storage mode:        auto
effective strategy:  full-copy (Step 2 compatibility)
responder running:   True
staging:             excluded-benign (1 entries)
preflight:           PASS, non-destructive
```

**Acceptance decision:** The explicit repository, restore-state and storage-mode configuration contract is implemented, regression-tested and exercised by the deployed production preflight. Existing 0033 roots, schema-2 media and copy/restore semantics are preserved. The evidence is sufficient to close Step 2 without a new live backup or destructive restore. The submitted transcript verifies effective runtime values, not an independent direct dump of each generated `.env` line; the rendered-input contract was separately checked by the Playbooks regression suites.

**Out of scope / remaining:** Step 3 will implement actual Btrfs/reflink capability probing and strategy selection. No Btrfs-aware capture is claimed by this close-out. Overall 0034-FEAT remains **In progress**. No Docker image build is required for this documentation-only closure.
