# Step 2 evidence — complete-backup directory and manifest contract

Date: 2026-10-07

## Purpose

Step 2 freezes the media contract which later 0033 backup/restore orchestration must produce and consume. It deliberately does **not** run `pg_dump`, copy a live Files root, stop a responder, mutate PostgreSQL, or deploy production changes.

The existing schema-1 database-only `.dataset.json` sidecars remain unchanged. Complete backup media uses its own directory-level `dataset-manifest.json` with `schemaVersion = 2`.

## Backup identity and directory naming

A complete backup ID is a UTC timestamp with no local-time ambiguity:

```text
YYYYMMDD-HHmmssZ
```

Example:

```text
20261007-120000Z
```

A final restorable backup directory is named exactly with that ID. Work is assembled under the same parent using the non-restorable convention:

```text
.<backup-id>.partial
```

For example:

```text
.20261007-120000Z.partial
```

The manifest validator rejects a partial workspace in normal `verify` mode. `verify --allow-partial-workspace` exists only so backup finalisation can validate the candidate immediately before same-filesystem promotion/rename to the final `<backup-id>` directory.

The complete-backup namespace remains based on the **effective logical dataset**, not the launch-mode wrapper. A shared local `common` pair therefore has one namespace:

```text
<dataset-backup-root>/common/<backup-id>/
```

## Frozen logical layout

Every final complete backup has this logical shape:

```text
<dataset-backup-root>/
└── <logical-dataset>/
    └── <backup-id>/
        ├── dataset-manifest.json
        ├── database/
        │   ├── diaries.dump
        │   └── diaries.sql
        ├── files/
        │   └── <exact durable mutable Files snapshot>
        └── verification/
            ├── database.sha256
            ├── files.sha256
            └── inventory.json
```

The required component names are fixed. A later implementation may add non-conflicting evidence fields/files only if schema compatibility rules are respected; it must not silently rename the required components within schema 2.

`.image-staging` is **not** part of the durable Files snapshot. Its inspected source disposition is recorded in the manifest instead.

## Relative-path rule

Every path which references backup media is canonical POSIX-style relative text such as:

```text
database/diaries.dump
verification/inventory.json
files/nested/image.jpg
```

The validator rejects absolute paths, Windows drive paths, UNC paths, backslashes, `.`/`..` path segments and symbolic-link traversal.

This restriction applies to **component references**. Identity fields such as `database.storageIdentity` and `files.resolvedPhysicalRoot` intentionally record the source/runtime identity and may therefore contain host-specific absolute/NAS values.

## Complete manifest schema 2

A valid complete manifest requires these top-level completion markers:

```json
{
  "schemaVersion": 2,
  "backupType": "complete-dataset",
  "completeDatasetBackup": true,
  "status": "complete"
}
```

It also requires:

- `backupId`, matching the final or permitted partial workspace directory name;
- timezone-aware `createdStartedAt` and `createdCompletedAt` with completion not preceding start;
- a safe `logicalDataset` identifier;
- source launch mode, known consumers and application/runtime identity;
- a positive writer-quiescence record (`status = quiesced`, method, writer list and evidence);
- `.image-staging` inspection/disposition and explicit `snapshotIncluded = false`;
- Image row, catalogued-file and durable-file counts;
- database storage identity and database name;
- custom and SQL dump descriptors;
- effective Files selector and resolved source Files-root identity;
- exact Files snapshot count/bytes plus inventory/hash-list references;
- the database hash-list descriptor.

For schema 2 the required database descriptors are:

```text
database/diaries.dump  format=postgresql-custom
database/diaries.sql   format=postgresql-plain-sql
```

Each records a positive byte size, lowercase SHA-256 and `verification = verified`.

The Files directory itself is represented by its deterministic inventory rather than by pretending a directory has a byte hash. The manifest records:

```text
files/
verification/inventory.json
verification/files.sha256
```

plus durable file count, total bytes and SHA-256 identities of the inventory/hash-list files.

`verification/database.sha256` must contain exactly the hashes of `database/diaries.dump` and `database/diaries.sql`.

`verification/files.sha256` must contain exactly one entry for every durable file in `files/` and no extra entry.

`verification/inventory.json` has its own small schema-1 inventory format:

```json
{
  "schemaVersion": 1,
  "root": "files",
  "fileCount": 2,
  "totalBytes": 123,
  "files": [
    {
      "path": "files/example.jpg",
      "sizeBytes": 123,
      "sha256": "..."
    }
  ]
}
```

The validator recalculates actual Files paths, sizes and SHA-256 values and requires an exact match. `.image-staging` content is rejected from the backup snapshot/inventory.

## Staging disposition contract

Schema 2 permits two source staging outcomes:

```text
empty
excluded-benign
```

`empty` requires `entryCount = 0`. `excluded-benign` is reserved for later orchestration to record specifically understood, non-durable staging state. In both cases `snapshotIncluded` must be `false` and a human-readable note is required.

Unexplained staging state is deliberately **not** a valid completed-manifest disposition; later capture orchestration must stop for review rather than manufacture a complete manifest.

## Schema compatibility

The validator supports schema version 2 only. Unknown future versions are rejected before restore can rely on their semantics. Future extensions may add fields within schema 2 only when they do not weaken or redefine required schema-2 fields/components. Any incompatible semantic change requires a new schema version and an explicitly upgraded validator/restore implementation.

Schema-1 database-only sidecars are a separate existing contract and are not accepted as complete backup manifests.

## Permanent implementation

The same `complete-dataset-manifest.py` implementation is stored in both permanent operator surfaces:

```text
Diaries:
  scripts/windows/common/complete-dataset-manifest.py

Playbooks:
  roles/diaries/files/sync/scripts/complete-dataset-manifest.py
```

It provides:

```text
write   generate dataset-manifest.json from an already captured and verified candidate
verify  validate manifest semantics, required media, counts, hashes and Files inventory
```

`write` does not copy Files or invoke PostgreSQL. It refuses to create a manifest unless the Step-2 required component/inventory/hash files already exist and are coherent. After writing it performs the same candidate validation and removes the manifest again if that validation fails.

The implementations are intentionally byte-identical at Step 2 so local and production media semantics cannot diverge.

## Permanent regressions

The synthetic regression is available in both repositories:

```text
Diaries:
  python scripts/windows/validation/verify-complete-dataset-manifest.py

Playbooks:
  python roles/diaries/tests/verify-complete-dataset-manifest.py
```

The tests create temporary synthetic dumps and Files only. They prove:

- schema-2 manifest generation from coherent candidate media;
- normal rejection of `.<backup-id>.partial`;
- pre-promotion validation with `--allow-partial-workspace`;
- successful validation after rename to `<backup-id>`;
- unsupported-schema rejection;
- wrong `backupType` rejection;
- `completeDatasetBackup != true` rejection;
- `status != complete` rejection;
- invalid logical-dataset rejection;
- absolute and escaping component-path rejection;
- missing and syntactically invalid SHA-256 rejection;
- missing required component rejection;
- changed Files bytes rejection through exact inventory/hash verification.

Captured output is in `REGRESSION.txt`.

## Step 2 conclusion

Step 2 is complete when these contract regressions pass from both refreshed source trees. The next step can implement the local capture engine against this frozen format without inventing backup media semantics while it is also manipulating live data.
