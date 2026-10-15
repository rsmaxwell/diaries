# 0034-FEAT — Step 8 formal close-out

**Step:** 8 — Update Playbooks configuration, source regression and operator guidance  
**Date:** 2026-10-09  
**Status:** **CLOSED**  
**Scope of closure:** Playbooks source configuration, regression and operator guidance; **not** production migration/deployment.

## Accepted deliverables

1. Explicit, non-overlapping stable publication root (`diaries_complete_backup_published_root` / `DIARIES_COMPLETE_BACKUP_PUBLISHED_ROOT`) separate from the preserved legacy repository and restore-state root.
2. Unchanged schema-2 backup format, legacy backup-ID restore semantics, explicit snapshot-path compatibility and historical classification of the superseded Step 3 reflink test.
3. Opt-in, unscheduled, normal-user-owned `mars` pull installation and wrapper; bounded rsync deletions, explicit legacy root cleanup opt-in and permanent guards.
4. Operator instructions for publication, failure/abort handling, last-good state, duplicate IDs, receiver verification, cleanup, disk pressure, path migration and rollback.
5. Permanent source regressions integrated with existing manifest, publisher, replication, restore and deployment suites.

## Verification evidence

- `mango` source regression transcript: **11 of 11 suites PASS**.
- Python syntax check: **four changed Python files compiled with no errors**.
- Evidence summary: [`RUNTIME-MANGO-REGRESSIONS-20261009.md`](RUNTIME-MANGO-REGRESSIONS-20261009.md).
- Earlier ad-hoc production runtime invocation reported a missing `compose.yaml` because it was run outside its deployment context; this was *not* a regression-suite failure and is not presented as production verification.

## Decision and carry-forward

**Step 8 is formally CLOSED** on the basis of successful source acceptance evidence from `mango`.

**Not performed in Step 8:** deploying new publication-root configuration to `pluto`, migrating the Step 6 pilot publication, running live capture/replication, switching schedules or triggering snapshots or restores. The new configured publication path must not be deployed casually while the pilot path is still in use.

**Step 9 owns:** pre-deployment inventory/backup, safe `pluto` configuration migration, validation of existing historical backups, first and second production publications, concurrent-reader/rsync consistency and deployment rollback evidence. No new Docker images are needed for Step 8.
