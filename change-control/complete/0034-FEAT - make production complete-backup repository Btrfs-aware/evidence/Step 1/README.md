# 0034-FEAT Step 1 evidence — freeze the 0033 production backup contract and current storage baseline

Date prepared: 2026-10-08
Status: **COMPLETE — 2026-10-08 (source and production evidence accepted)**

## Purpose

Step 1 establishes the regression boundary before any Btrfs-aware behaviour is introduced.

It freezes two different things deliberately:

1. the **logical 0033 complete-backup contract**, which must not change as 0034 is implemented; and
2. the **current production storage baseline**, which must be measured from `pluto` rather than inferred from a path name or from the intended future Btrfs repository.

No backup format, production script, Playbooks variable, restore behaviour, live data, Docker service, NAS Files content, mount or filesystem is changed by this step.

## Frozen 0033 contract

The authoritative pre-0034 behaviour is the completed 0033 record. The Step-1 semantic regression is:

```text
python "change-control/in-progress/0034-FEAT - make production complete-backup repository Btrfs-aware/evidence/Step 1/tooling/verify-frozen-0033-contract.py"
```

It proves that the source tree still records the following invariants:

```text
complete media schema             schemaVersion = 2
backup type                       complete-dataset
completed backup directory        <backup-id>/
non-restorable workspace          .<backup-id>.partial/
backup ID                         UTC YYYYMMDD-HHmmssZ
required database media           database/diaries.dump
                                  database/diaries.sql
required Files media              files/
required verification media       verification/database.sha256
                                  verification/files.sha256
                                  verification/inventory.json
manifest                          dataset-manifest.json
Files correctness gate            exact path + size + SHA-256
transient staging                 .image-staging excluded
promotion                         only after candidate verification
restore                           ordinary schema-2 content; no Btrfs dependency
```

The current production orchestration remains the 0033 flow:

```text
preflight
quiesce responder writer while PostgreSQL remains available
capture custom + SQL database dumps
capture durable Files excluding .image-staging
independently reread/verify exact Files paths, sizes and SHA-256
write and verify schema-2 manifest in .partial workspace
same-filesystem atomic promotion
verify completed backup
restore prior responder-running state
```

0034 may optimise how `files/` is initially materialised, but it must not weaken or redefine any item above.

## Historical production baseline already proven by 0033

0033 Step 8 recorded the production layout as:

```text
project root:             /home/richard/projects/diaries
logical dataset:          production
complete-backup root:     /home/richard/projects/diaries/data/dataset-backups/production
complete-restore root:    /home/richard/projects/diaries/data/dataset-restores/production
live Files selector:      files
Docker NAS volume:        diaries_nas-photo
```

The last production backup proved by 0033 was:

```text
backup ID:                20261007-145013Z
durable Files:            89
durable Files bytes:      100032776
source comparison:        exact paths/sizes/SHA-256
manifest:                 schema-2, valid as candidate and completed media
```

This historical evidence establishes the starting contract, **not** the current filesystem type of the backup root.

## Current production storage baseline capture

**Captured successfully on `pluto` at 2026-10-08T07:51:31Z**, before any Step-2 repository configuration change. The read-only capture script was run via the existing host project directory.

The script can be copied to `pluto` temporarily or its contents can be run from `/tmp`. It does not create a backup and it does not stop a writer. Example after copying it to `/tmp`:

```bash
chmod +x /tmp/0034-step1-capture-production-baseline.sh
/tmp/0034-step1-capture-production-baseline.sh \
  /home/richard/projects/diaries \
  | tee 0034-step1-production-storage-baseline.txt
```

The capture records:

- UTC time, host and kernel;
- resolved project/backup/restore paths;
- `findmnt`, `stat -f` and `df` evidence for the current backup root;
- Btrfs filesystem/usage information **only when the current root actually reports `btrfs`**;
- current completed and `.partial` backup directory inventory;
- the newest completed backup;
- normal schema-2 validation of that newest completed backup;
- `backup-dataset.sh preflight`, proving the current production identity without creating a workspace or stopping the responder;
- SHA-256 identities of the deployed 0033 complete-dataset scripts.

The capture is intentionally fail-closed for missing required 0033 production tooling or an invalid newest completed backup. A non-Btrfs filesystem is **not** a Step-1 failure: it is a legitimate baseline result to be addressed by later 0034 provisioning/configuration steps.

## Required retained runtime evidence

Save the command output under this directory as, for example:

```text
RUNTIME-PRODUCTION-STORAGE-BASELINE.txt
```

Do not edit the raw capture to make it appear Btrfs-capable. Step 1 is recording the starting point.

## Step 1 completion criteria

Step 1 is **closed** because the retained Windows regression and `pluto` transcript establish all of the following:

- the source semantic freeze regression passes;
- the current production complete-backup root is resolved explicitly;
- its real filesystem/mount identity is recorded;
- current free/used/allocation information is recorded;
- current completed/partial backup inventory is recorded;
- the newest completed backup validates with the unchanged schema-2 validator;
- production `backup-dataset.sh preflight` still succeeds and remains non-mutating;
- deployed complete-dataset script hashes are captured for comparison after later 0034 changes;
- no backup, restore, service restart, data mutation or repository migration was performed merely to close Step 1.

## Accepted evidence and formal closure — 2026-10-08

- `RUNTIME-WINDOWS-CONTRACT-REGRESSION.txt`: all five source-side contract tests passed.
- `RUNTIME-PRODUCTION-STORAGE-BASELINE.txt`: `pluto` baseline capture finished with `STEP-1 BASELINE CAPTURE PASSED`.
- Storage identity: repository `/home/richard/projects/diaries/data/dataset-backups/production` is on the root ext4 filesystem (`/dev/mapper/ubuntu--vg-ubuntu--lv`), **not Btrfs**; 67G total, 41G used, 23G available (65% used).
- Backup inventory: one valid completed backup (`20261007-145013Z`) and one earlier non-restorable workspace (`.20261007-143438Z.partial`). Neither was altered.
- The newest completed backup passed the **unchanged schema-2 manifest validator**: dataset `production`, 89 Files.
- Non-mutating production preflight passed with the responder running and `diaries_nas-photo` as the effective Docker NAS volume.
- Deployed backup, restore and verification script SHA-256 values are frozen in the runtime transcript.
- The first attempted invocation failed solely because the script had not yet been copied to `/tmp`; the later invocation in the same transcript completed successfully. That initial path error is retained as evidence, not concealed.

See `CLOSEOUT.md` for the acceptance decision and preserved constraints. **No Docker image build, Playbooks deploy, filesystem migration or backup creation is required by Step 1.**

## Boundary for Step 2

Step 1 does **not** choose the future repository variable name, mode (`auto`, `required-btrfs`, `full-copy`), Btrfs destination path, reflink base-selection algorithm or reconciliation implementation. Those belong to later 0034 steps.

0035 must also remain undeployed while this baseline is captured; the existing Snapper layer remains the safety baseline until the separately planned snapshot-manager replacement is intentionally rolled out.
