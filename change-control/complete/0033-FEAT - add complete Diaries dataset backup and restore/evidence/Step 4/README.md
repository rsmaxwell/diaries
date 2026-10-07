# Step 4 evidence — local complete backup verification and atomic promotion

Date: 2026-10-07

## Scope implemented

Step 4 converts a successful Step-3 `.<backup-id>.partial` capture into a trustworthy complete backup. It remains additive: the schema-1 database-only commands are unchanged.

The permanent operator entry point remains each mode's thin `backup-dataset.bat` wrapper. After Step 4:

```text
backup-dataset.bat preflight
    non-mutating effective-dataset/writer/staging check

backup-dataset.bat
    capture + verify + schema-2 manifest + atomic promotion + prior-writer-state restoration

backup-dataset.bat finalise YYYYMMDD-HHmmssZ
    finalise an existing Step-3 .<backup-id>.partial candidate without recapture
```

The last form is specifically available so the real Step-3 candidate `.20261007-105033Z.partial` can be completed rather than discarded and recaptured.

## Verification semantics

Before promotion the common engine keeps/re-proves application writer quiescence and performs all of the following:

1. validates the PostgreSQL custom dump with `pg_restore --list` inside the selected running `diaries-db` container;
2. checks the plain SQL dump is readable UTF-8 pg_dump text with both standard dump and completion markers;
3. computes SHA-256 for `database/diaries.dump` and `database/diaries.sql`;
4. computes a complete relative-path/size/SHA-256 inventory for the captured durable Files tree;
5. computes the same durable inventory from the live Files root while `.image-staging` remains excluded;
6. requires exact source/captured equality of paths, sizes and hashes;
7. writes `verification/database.sha256`, `verification/files.sha256` and `verification/inventory.json`;
8. writes schema-2 `dataset-manifest.json` only from the verified capture facts;
9. validates that manifest in explicit partial-candidate mode;
10. re-proves writers stopped immediately before promotion.

The helper `scripts/windows/common/complete-dataset-verification.py` owns the deterministic hash/inventory/source-comparison work. `complete-dataset-manifest.py` remains the schema-2 media validator from Step 2.

## Atomic promotion and writer-state restoration

A candidate is promoted with a same-parent directory rename:

```text
.<backup-id>.partial  ->  <backup-id>
```

Normal manifest validation is then run against the final directory name. If that validation unexpectedly fails, the directory is renamed back to its `.partial` name so an invalid artifact cannot remain final-looking.

Only after final validation succeeds is the prior responder state from `capture-state.json` restored. Verification failures leave the partial workspace and writers quiesced. If writer restart fails *after* successful promotion, the valid complete backup is retained and the capture state explicitly records `complete-writer-restore-failed`; the backup is not demoted or destroyed.

For the real Step-3 candidate all discovered writers were already stopped before capture, so finalising that candidate should preserve the stopped state rather than starting a responder.

## Permanent focused regression

Run:

```text
python scripts/windows/validation/verify-local-complete-dataset-finalisation.py
```

The captured output is in `REGRESSION.txt`. The regression uses only synthetic temporary media. It proves:

- exact source/snapshot hash matching;
- required database and Files hash lists/inventory;
- SQL readability rejection;
- source drift/extra-file rejection;
- schema-2 candidate generation;
- normal rejection of `.partial` as restorable media;
- validation in explicit candidate mode;
- successful same-filesystem promotion;
- independent final validation;
- rejection of deliberate post-promotion byte corruption;
- orchestration order: verify -> promote -> final verify -> writer-state restore;
- failed final validation is demoted back to `.partial`;
- all three wrappers remain thin and can finalise an existing candidate.

## Runtime evidence and close-out

Step 4 is formally complete from real Windows/Docker/NAS evidence collected on 2026-10-07 for the shared `common` dataset.

The Step-3 candidate was:

```text
data/dataset-backups/common/.20261007-105033Z.partial
```

The first finalisation attempt is retained as [`RUNTIME-FIRST-ATTEMPT.txt`](RUNTIME-FIRST-ATTEMPT.txt). It successfully reached writer-quiescence, `pg_restore --list`, exact Files source/snapshot comparison and SQL readability, then stopped before manifest creation because Windows PowerShell 5.1 stripped quotes from the raw native-command `--application-identity-json` argument. The candidate remained `.partial`; no final-looking backup was left behind and no recapture was required.

The implementation was corrected to send the same UTF-8 application-identity JSON through the Windows-safe `--application-identity-base64` argument. `complete-dataset-manifest.py` retains the direct JSON option for non-PowerShell callers, and the permanent Step-4 regression guards the Base64 path.

The successful retry is retained verbatim as [`RUNTIME-FINALISATION.txt`](RUNTIME-FINALISATION.txt). It proves:

```text
logical dataset:       common
backup ID:             20261007-105033Z
writer state:          quiesced before verification
custom dump:           pg_restore --list verified
SQL dump:              readable PostgreSQL plain dump
durable Files:         89
Files bytes:           100032776
source/snapshot match: exact paths/sizes/SHA-256
candidate manifest:    schema 2 validated while .partial
final manifest:        schema 2 independently validated after promotion
final backup:          data/dataset-backups/common/20261007-105033Z
partial workspace:     none after atomic promotion
prior writer state:    restored
Image rows:            85
catalogued files:      85
```

The final backup's own `dataset-manifest.json` and `verification/` directory remain the authoritative media-resident manifest, checksums and inventory. They are not duplicated into source control; the runtime transcript records that both candidate and final schema-2 validation succeeded against those artifacts.

This satisfies the Step-4 completion criterion: one operator command can create/finalise a self-contained, independently verifiable local complete backup which cannot be confused with a partial backup.

**Step 4 completed 2026-10-07.**
