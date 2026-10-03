# 0031 Step 12 — Reconcile every new effective database + Files-root pair

## Status

**COMPLETE — 2026-10-02.**

Step 12 is deliberately read-only. It reruns the existing 0024 Image catalogue reconciliation against each post-split durable pair and compares the result with the authoritative Step 9 pre-split baseline. No Image row or physical file is created, updated or deleted by this step.

Both authoritative post-split reconciliations have now passed:

```text
runtime/local-common-20261002-182452/
runtime/production-20261002-184656/
```

The local comparison reported `PASS: Step 12 local-common reconciliation matches the Step 9 semantic baseline.` The production comparison reported `PASS: Step 12 production reconciliation matches the Step 9 semantic baseline.` See [`CLOSE-OUT.md`](CLOSE-OUT.md) for the closure decision.

The two independent durable datasets currently in scope are:

| Dataset | Effective database | Step 12 Files root |
| --- | --- | --- |
| local common | `./data/database/common` | `files-development-common` |
| production | production PostgreSQL dataset | `files` |

The three local modes intentionally share the first pair. One post-split reconciliation is therefore authoritative for that durable local dataset; Step 11 separately proved that all three modes resolve to it.

## What the comparison requires

For each dataset, Step 12 compares the new 0024 dry-run with Step 9 and requires:

- `DRY_RUN_COMPLETE` from the current 0024 reconciliation;
- the same database name;
- identical reconciliation-status counts;
- an identical semantic `0024-file-inventory.csv` after excluding `lastModified` and normalizing directory `size` metadata;
- the expected effective Files selector;
- for local common, a changed physical root (`files` -> `files-development-common`);
- for production, the same Docker-visible Files root and `DIARIES_FILES_DIR=files`.

The semantic inventory still compares `relativePath`, `imageId`, `status`, `kind`, `sha256`, `mimeType`, `width`, `height` and `detail`, and it compares `size` for every regular file. Directory byte-size is normalized because it is filesystem metadata and can legitimately differ after a copy. A copy/split cannot therefore turn a match into a missing file, add an untracked application file, alter file bytes/size or change catalogue identity without failing Step 12.

`databaseIdentity` and the filesystem `rootKey` are captured as informational evidence rather than hard requirements. A database container address/port can change without changing the durable dataset, and the copied local root is expected to have a new filesystem identity.

The 0024 reconciler deliberately excludes `.image-staging`. Each Step 12 runner therefore also captures a separate `STAGING-INVENTORY.tsv`. The empty/transient `.image-staging/catalogue.lock` seen before the split was explicitly excluded from the Step 10 copy and is not an application-data mismatch.

## Local common reconciliation

Preconditions:

1. Step 11 is closed.
2. The common local database is available.
3. No Image/File mutation is occurring.
4. Production Image/File writes remain frozen.
5. `config/environments/local.env` still selects the approved common pair:

```text
DIARIES_DB_DATA_DIR=./data/database/common
DIARIES_FILES_DIR=files-development-common
```

From the Diaries repository root run:

```bat
scripts\windows\0031-step12\reconcile-common-pair.bat -ProductionWriteFreezeConfirmed
```

The runner:

1. applies the normal `development-infrastructure.env` then `local.env` precedence;
2. refuses any pair other than `./data/database/common + files-development-common`;
3. calls the Step 4 `prepare-responder-config.bat` path;
4. verifies the generated responder config selects `files-development-common`;
5. runs `:diaries-responder:migration0024ImageCatalogue` in **dry-run** mode only;
6. discovers the latest `evidence/Step 9/runtime/local-common-*` baseline unless `-Step9Run` is supplied;
7. writes a normalized `STEP12-REPORT.json/.md` and fails if semantic reconciliation drift is found.

Evidence is written beneath:

```text
evidence/Step 12/runtime/local-common-YYYYMMDD-HHMMSS/
```

including:

```text
PAIR.json
STAGING-INVENTORY.tsv
reconciliation-console.txt
reconciliation/0024-summary.json
reconciliation/0024-file-inventory.csv
reconciliation/0024-conflicts.csv
reconciliation/SHA256SUMS.txt
STEP12-REPORT.json
STEP12-REPORT.md
```

## Production reconciliation on `pluto`

The Playbooks Step 12 package adds:

```text
roles/diaries/files/sync/scripts/step12-reconcile-production.sh
roles/diaries/files/sync/scripts/step12-compare-reconciliation.py
```

As with Step 9, these can be copied to the deployed Diaries `scripts/` directory without running a playbook that might disturb the current write freeze. From the Playbooks repository on Windows, for example:

```bat
scp roles\diaries\files\sync\scripts\step12-reconcile-production.sh pluto:/home/richard/projects/diaries/scripts/
scp roles\diaries\files\sync\scripts\step12-compare-reconciliation.py pluto:/home/richard/projects/diaries/scripts/
```

Then on `pluto`, with `diaries-db` running and `diaries-responder` stopped:

```bash
cd /home/richard/projects/diaries
chmod +x scripts/step12-reconcile-production.sh scripts/step12-compare-reconciliation.py
./scripts/step12-reconcile-production.sh --write-freeze-confirmed
```

The runner refuses a production `.env` that does not contain:

```text
DIARIES_FILES_DIR=files
```

It discovers the latest Step 9 production baseline beneath:

```text
data/0031-step9/production-*
```

and writes the new evidence beneath:

```text
data/0031-step12/production-YYYYMMDD-HHMMSS/
```

Preserve the entire successful `production-*` directory and copy it into the permanent Step 12 evidence before close-out.

## Pass/fail interpretation

A `PASS` report means the split/repointing did not alter the database/catalogue/File semantics recorded in Step 9. The local run must differ only in the intended physical Files-root identity. Production must continue to use its original `files` root.

Any critical `FAIL` is a stop condition for Step 13. Do not copy a missing file from the other dataset, run 0024 `apply`, upload a replacement, or delete an unexpected file merely to make the report green. Investigate and record the dataset-specific cause first.

## Step boundary

Step 12 contains no destructive lifecycle test. Upload/delete isolation belongs to **Step 13** and must not begin until both Step 12 reports are PASS or any exception has been explicitly reviewed and documented.

Step 12 is complete: the local-common and production post-split reports were both captured, reviewed and compared successfully with Step 9. Controlled destructive isolation testing now belongs to **Step 13**.
