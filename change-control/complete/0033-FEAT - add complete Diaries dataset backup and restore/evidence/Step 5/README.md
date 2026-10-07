# Step 5 evidence — complete restore preflight, safety backup and Files staging

## Status

**Complete 2026-10-07.**

The real Windows/Docker/NAS rehearsal reached the required fully verified, writer-quiesced, rollback-protected prepared state for the shared local `common` dataset without changing either live durable half.

## Permanent operator surface

All three local modes delegate to `scripts/windows/common/restore-dataset.ps1` and expose:

```bat
restore-dataset.bat preflight <backup-id-or-complete-backup-directory>
restore-dataset.bat prepare   <backup-id-or-complete-backup-directory>
```

The exact staged-Files verifier is `scripts/windows/common/complete-dataset-restore-stage.py`; the permanent Step-5 regression is `scripts/windows/validation/verify-local-complete-dataset-restore-preparation.py`.

## Frozen Step-5 contract

`preflight` is non-mutating. It validates the effective database/Files pair, accepts only completed schema-2 complete media, verifies every recorded hash/inventory, checks the custom dump with `pg_restore --list`, enforces source/target identity matching, rejects database-only inputs, inspects target `.image-staging`, reports practical free-space information and identifies every possible writer.

`prepare` requires the exact token `RESTORE`, records prior writer state, quiesces every writer, rechecks staging, creates and independently validates a fresh complete-dataset safety backup, stages the selected backup Files to a same-parent sibling directory and independently proves exact relative path/size/SHA-256 identity. It then persists status `prepared-awaiting-step6` and deliberately leaves writers stopped.

The Step-5 branch remains non-destructive even though the permanent common engine now also contains Step-6 commands: it does not invoke the database apply helper or Files swap helper, and it reports both live PostgreSQL and live Files as unchanged at hand-off.

## Real preflight — `20261007-105033Z`

`RUNTIME-PREFLIGHT.txt` records the successful non-mutating rehearsal. It proved:

- logical dataset `common` selected through the paired `local.env` override;
- source backup `20261007-105033Z` is completed schema-2 media;
- 89 Files / 100032776 bytes in the source backup;
- `pg_restore --list` validation passed;
- target `.image-staging` contained only the expected benign zero-byte lock condition;
- all three possible responders were already stopped;
- no writer, safety backup or staging directory was changed by preflight.

## Real prepare — safety backup and sibling stage

`RUNTIME-PREPARE-FIRST-ATTEMPT.txt` records the first real `prepare` rehearsal. It successfully created and independently validated mandatory safety backup:

```text
20261007-114623Z
```

It then copied all 89 replacement Files / 100032776 bytes to the sibling stage and proved exact paths/sizes/SHA-256 with transient `.image-staging` absent. The transcript explicitly records:

```text
Writers:       quiesced and intentionally left stopped
Live database: UNCHANGED
Live Files:    UNCHANGED
```

The rehearsal exposed one state-plumbing defect after the operational work had already succeeded: nested safety-backup stdout was accidentally captured into `safetyBackup.directory` together with the real path.

## Permanent correction and prepared-state repair

The common engine now captures child-PowerShell stdout locally, replays it only with `Write-Host`, and derives the authoritative safety-backup path independently from the allocated ID. Permanent regression rejects reintroducing a return-value/stdout coupling.

The already-created prepared state was repaired rather than repeating the safety backup and NAS staging work. `RUNTIME-STATE-REPAIR.txt` proves the persisted state re-read as:

```text
prepared-awaiting-step6
backupId:  20261007-114623Z
directory: ...\data\dataset-backups\common\20261007-114623Z
verified:  true
```

Therefore Step 5 meets its completion criterion: the selected restore is fully verified, all writers remain quiesced, a verified complete pre-restore safety backup protects the old dataset, the exact replacement Files are staged, and neither live durable half has yet been replaced.
