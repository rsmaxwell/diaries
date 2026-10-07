# Step 3 evidence — common local complete-dataset backup engine

Date: 2026-10-07

## Scope implemented

Step 3 adds the local capture half of the 0033 complete-dataset workflow. It is deliberately additive: the existing database-only backup/restore commands remain unchanged.

Permanent entry points are now:

```text
scripts/windows/development-infrastructure/backup-dataset.bat
scripts/windows/local-docker-build/backup-dataset.bat
scripts/windows/local-published-smoke/backup-dataset.bat
scripts/windows/common/backup-dataset.ps1
```

At the Step 3 checkpoint, each wrapper supported:

```text
backup-dataset.bat preflight
backup-dataset.bat
```

`preflight` is non-mutating. The Step 3 capture phase creates a Step-2-style incomplete workspace:

```text
data/dataset-backups/<logical-dataset>/.<YYYYMMDD-HHmmssZ>.partial/
```

Step 3 itself does **not** create `dataset-manifest.json`, verification hashes/inventory, or promote the directory to its final name. Step 4 subsequently extends the normal `backup-dataset.bat` operator command so this capture phase flows directly into verification/promotion; the Step 3 phase and its `.partial` safety boundary remain unchanged internally.

## Environment and effective-dataset contract

The common engine loads the committed mode environment first and `config/environments/local.env` second, invokes the existing `validate-dataset-pair.ps1`, and resolves the effective dataset with `resolve-effective-dataset.ps1`.

The permanent regression models both supported topologies:

```text
isolated committed defaults:
  development-infrastructure -> development-infrastructure / files-development-infrastructure
  local-docker-build         -> local-docker-build         / files-local-docker-build
  local-published-smoke      -> local-published-smoke      / files-local-published-smoke

paired common local.env override:
  all three modes -> common / files-development-common
```

Therefore invoking any wrapper for the shared pair targets the same namespace:

```text
data/dataset-backups/common/
```

rather than creating mode-specific duplicate backup trees.

## Preflight and writer policy

Before mutation the engine:

1. validates the dataset pair;
2. resolves the database identity, Files selector/root and logical dataset;
3. refuses an unavailable Files root;
4. inspects `.image-staging`, accepts only an empty directory or the expected zero-byte `catalogue.lock`, and refuses every other unexplained entry;
5. proves the selected mode's `diaries-db` service is running;
6. discovers every local launch mode selecting the same pair;
7. records running Docker responders for those consumers;
8. inspects direct Windows Java responder processes when development-infrastructure is a consumer;
9. refuses known migration/maintenance Java writers rather than trying to terminate them implicitly.

During capture, running Docker responders are stopped through their own Compose projects. A direct-development responder is stopped by PID. Writer absence is then re-proved before any database dump or Files copy is performed. PostgreSQL remains running throughout.

## Capture semantics

With writers quiesced, the engine:

- records Image row and catalogued-path counts from PostgreSQL;
- creates a PostgreSQL custom dump;
- creates a PostgreSQL plain SQL dump;
- copies both dumps from the container without routing binary data through PowerShell text redirection;
- copies the durable Files tree using `robocopy /E /COPY:DAT /DCOPY:DAT`;
- excludes `.image-staging` from the snapshot while recording `empty` or `excluded-benign` staging disposition;
- writes `capture-state.json` recording dataset identity, source identity, counts, prior writer state and the Step-4 finalisation requirement.

The workspace after a successful Step 3 capture is conceptually:

```text
.<backup-id>.partial/
├── capture-state.json
├── database/
│   ├── diaries.dump
│   └── diaries.sql
└── files/
    └── <durable Files snapshot; no .image-staging>
```

## Failure and writer restart policy

Step 3 never makes a candidate look complete. If a failure occurs after workspace creation, it records:

```text
status = failed-incomplete
```

and retains the partial workspace for diagnosis.

A writer stopped by Step 3 is intentionally **not** restarted after successful capture or failure. `capture-state.json` records the prior running state. Step 4 must first generate/verify hashes and inventory, write/validate the schema-2 manifest and atomically promote the directory; only then may it restore the prior writer-running state. This prevents an incomplete capture from being followed by silent application writes and a false success impression.

## Static/focused regression

Run:

```text
python scripts/windows/validation/verify-local-complete-dataset-backup-engine.py
```

The captured output is in `REGRESSION.txt`.

This regression is non-destructive. It does not stop Docker containers, kill a responder, access a live Files root or create PostgreSQL dumps.

## Runtime completion evidence

Step 3 was exercised against the normal shared local dataset on Windows on 2026-10-07. The exact transcripts are retained as:

```text
RUNTIME-PREFLIGHT.txt
RUNTIME-CAPTURE.txt
```

The successful capture proved:

- effective dataset `common` selected from the paired `local.env` override;
- Files selector `files-development-common`;
- PostgreSQL container running throughout capture;
- Docker responders for `local-docker-build` and `local-published-smoke` stopped;
- direct Windows responder stopped;
- staging disposition `excluded-benign` with exactly one expected zero-byte `catalogue.lock`;
- custom dump `database/diaries.dump`;
- SQL dump `database/diaries.sql`;
- durable Files snapshot copied with `.image-staging` excluded;
- 89 Files / 95.39 MB copied with zero mismatches and zero failures;
- 85 Image rows and 85 catalogued paths recorded;
- resulting candidate retained as `data/dataset-backups/common/.20261007-105033Z.partial`.

This satisfies Step 3's completion criterion. The candidate is intentionally left non-restorable until Step 4 generates verification media, validates the schema-2 manifest and atomically promotes it.

### Runtime preflight correction — expected catalogue lock

The first real Windows preflight against `files-development-common` found exactly one staging entry: `.image-staging/catalogue.lock`. Earlier 0031 reconciliation evidence and responder tests establish that this zero-byte lock file is normal runtime control state. The initial Step 3 guard incorrectly treated every staging entry as unexplained.

The guard now accepts only either an empty staging directory or exactly one zero-byte `catalogue.lock` at the staging root, records that state as `excluded-benign`, and still rejects any other file, directory, nested payload or non-zero lock. Staging is also inspected a second time after writer quiescence to close the race between preflight inspection and responder shutdown. The staging directory remains excluded from the durable Files snapshot.
