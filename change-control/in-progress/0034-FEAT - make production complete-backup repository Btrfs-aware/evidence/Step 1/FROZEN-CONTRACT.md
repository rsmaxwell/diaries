# Frozen 0033 production complete-backup contract

This file is the concise 0034 Step-1 regression reference. It does not supersede the completed 0033 record.

## Media contract

```text
schemaVersion: 2
backupType: complete-dataset
completeDatasetBackup: true
status: complete
backup ID: YYYYMMDD-HHmmssZ (UTC)
partial workspace: .<backup-id>.partial
```

Required completed-media layout:

```text
<backup-id>/
├── dataset-manifest.json
├── database/
│   ├── diaries.dump
│   └── diaries.sql
├── files/
└── verification/
    ├── database.sha256
    ├── files.sha256
    └── inventory.json
```

Backup-media paths in the manifest are canonical relative POSIX-style paths. `.image-staging` is not durable backup content.

## Correctness contract

A candidate is not publishable until the normal 0033 verification proves:

```text
custom PostgreSQL dump descriptor/hash valid
plain SQL dump descriptor/hash valid
schema-2 manifest semantics valid
exact durable Files path set
exact durable Files sizes
exact durable Files SHA-256 values
logical dataset identity correct
partial/completed workspace semantics correct
```

The final Files source comparison is authoritative. Physical extent sharing is never a substitute for content verification.

## Production orchestration contract

The supported production entry points remain:

```text
scripts/backup-dataset.sh
scripts/restore-dataset.sh
```

The 0033 backup sequence is frozen in meaning:

```text
preflight -> quiesce writer -> capture DB + Files -> independent verification
-> schema-2 manifest -> verify partial -> atomic promotion -> verify completed
-> restore previous writer state
```

Failure before successful final verification publishes no completed backup and does not weaken the existing fail-closed writer-state rules.

## Restore contract

Restore consumes ordinary schema-2 files only. It must not require:

```text
Btrfs UUID
subvolume ID
generation number
extent ID
reflink relationship
snapshot ID
```

A completed backup copied onto a non-Btrfs filesystem must remain ordinary valid restore media.

## Current pre-0034 production paths

These are the paths recorded by completed 0033 Step 8 and are frozen only as the **starting baseline**, not as the final 0034 configuration model:

```text
project root              /home/richard/projects/diaries
backup root               /home/richard/projects/diaries/data/dataset-backups/production
restore state root        /home/richard/projects/diaries/data/dataset-restores/production
live Files selector       files
Docker NAS volume         diaries_nas-photo
```

0034 is expected to make the backup repository root explicit through Playbooks later; changing that configuration must not change the schema-2 media contract above.
