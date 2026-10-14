# 0034-FEAT Step 7 — Preserve historical restore and compatibility

**Status:** CLOSED — source regressions, deployment and non-destructive live acceptance passed.  
**Date:** 2026-10-09.

## Implemented contract

The production complete-dataset restore remains the 0033 schema-2 restore. Step 7 changes only how completed media may be selected:

- a historical UTC `<backup-id>` still resolves beneath `DIARIES_COMPLETE_BACKUP_REPOSITORY_ROOT` exactly as before;
- `diaries-backup` and `diaries-backup/` select the stable current publication beneath that repository root;
- an explicit directory path selects an independently accessible completed schema-2 dataset, including a future read-only path returned by 0035 `diaries-backup-history path BACKUP_ID`.

All three forms pass through the same schema-2 manifest validation, production target identity checks, custom-dump structural check, Files inventory checks, mandatory safety backup, exact `RESTORE` / `APPLY` confirmations, rollback and postflight machinery. Partial workspaces remain non-restorable.

## Prepared-source pinning

A restore prepared from the fixed publication or a snapshot path must not silently change media if `diaries-backup` later advances. The prepared restore state already records the resolved source directory. Step 7 now makes `apply`, `rollback` and `postflight` by bare backup ID prefer that recorded directory and verifies that the selected source still equals the prepared source.

This also avoids a same-ID legacy directory taking precedence over the externally prepared source. If the recorded source is no longer available, continuation fails closed rather than falling back to different media.

## 0035 boundary

0035 owns `diaries-backup-history`. Its `path` operation is defined as a read-only discovery handoff only. It returns a path under a manager-owned read-only snapshot tree; it **does not** call `restore-dataset.sh`, ask for destructive confirmation, modify a snapshot, or restore any data.

The operator flow is deliberately two-step:

```text
SNAPSHOT_PATH="$(diaries-backup-history path BACKUP_ID)"
./restore-dataset.sh preflight "$SNAPSHOT_PATH"
```

Only a subsequent explicit operator `prepare` and exact `RESTORE`, followed later by explicit `apply` and exact `APPLY`, can change the target dataset.

## Source regression

New permanent regression:

```text
python3 roles/diaries/tests/verify-production-restore-source-compatibility.py
```

It uses disposable synthetic schema-2 sources and no Docker/production mutation. It verifies:

- legacy `<backup-id>` resolution and non-destructive preflight;
- bare and trailing-slash `diaries-backup` selection;
- explicit snapshot-style directory selection;
- logical-dataset mismatch refusal;
- exact uppercase `RESTORE` confirmation and no writer stop on failed confirmation;
- prepared-source precedence over a conflicting same-ID legacy directory;
- source pinning after the public fixed pointer advances; and
- partial-workspace refusal.

`SOURCE-REGRESSIONS-20261009.txt` also records PASS for the existing manifest, production database-only backup/restore, complete-dataset tooling, storage-isolation and deployment-contract suites.

## Runtime acceptance and formal close-out — completed 2026-10-09

On `mango`, all six source regressions from `APPLY-NOTES.md` passed, including permanent source-compatibility coverage of exact `RESTORE` confirmation, dataset mismatch, source pinning, and partial-directory refusal.

Normal `./scripts/diaries.sh` deployment to `pluto` finished with `ok=46 changed=2 unreachable=0 failed=0 skipped=12`. The managed scripts sync updated the deployed production restore engine.

Three **live, non-destructive** `preflight` commands on `pluto` passed for historical backup ID `20261007-145013Z`, the fixed `diaries-backup` selector and the explicit `.diaries-backup-generations/20261007-145013Z` directory. Each validated a completed schema-2 `production` dataset with 89 Files totaling 100,032,776 bytes, and ended `PREFLIGHT OK` with responder still running. The explicit-path test was against a generation directory, **not** an actual 0035 read-only Btrfs snapshot.

The `printf 'NO\n' | ... prepare diaries-backup` live command in the original acceptance notes was **not run** in the supplied transcript. The same failed-confirmation guard and non-mutation behavior were exercised in the disposable regression instead. Accordingly, this close-out does **not** claim live production negative-confirmation execution or any live `prepare`/`apply`/`rollback`. No destructive production restore was performed.

**Disposition: Step 7 CLOSED.** Further actual 0035 snapshot restore rehearsals and cross-feature integration belong to later steps. Full evidence and source filenames are in `CLOSEOUT.md`.
