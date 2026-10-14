# 0034 Step 2 apply notes

Apply the companion Playbooks overlay to the Playbooks repository root and this Diaries overlay to the Diaries repository root.

## Source verification

From the Playbooks repository root run:

```bash
python3 roles/diaries/tests/verify-complete-dataset-manifest.py
python3 roles/diaries/tests/verify-production-backup-restore-semantics.py
python3 roles/diaries/tests/verify-production-complete-dataset-tooling.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
python3 roles/diaries/tests/verify-production-storage-isolation.py
```

All five must pass before deployment.

## Deployment verification

Step 2 does not require new Docker images. Deploy the Diaries Playbooks copy/configuration changes by the normal Ansible path when ready. The default values intentionally preserve the existing `pluto` paths.

After deployment, inspect `/home/richard/projects/diaries/.env` and confirm these effective values before running any complete backup:

```text
DIARIES_FILES_DIR=files
DIARIES_COMPLETE_BACKUP_REPOSITORY_ROOT=/home/richard/projects/diaries/data/dataset-backups/production
DIARIES_COMPLETE_RESTORE_STATE_ROOT=/home/richard/projects/diaries/data/dataset-restores/production
DIARIES_COMPLETE_BACKUP_STORAGE_MODE=auto
```

Then run only the non-destructive preflight:

```bash
cd /home/richard/projects/diaries
./scripts/backup-dataset.sh preflight
```

It should report the explicit backup repository, restore-state root and storage mode while continuing to report the frozen full-copy capture strategy for Step 2. Do not move the repository or enable an operational `required-btrfs` assertion until Step 3 adds capability probing.

Retain the deployment/preflight transcript under this evidence directory before formally closing Step 2.
