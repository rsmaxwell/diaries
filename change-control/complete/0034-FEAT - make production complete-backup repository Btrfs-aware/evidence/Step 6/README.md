# 0034-FEAT Step 6 — replication-safe read contract

**Status: isolated transfer mechanism implemented and tested; live replication integration remains OPEN.**

The new opt-in `complete-dataset-replication.py transfer` uses the Step 5 publisher `pin-run` to hold a shared advisory flock, select and verify a single immutable generation and run rsync from the pinned directory into a private receiving staging directory. The receiving schema-2 manifest and inventory are independently verified. The output JSON handoff includes `backupId`, `logicalDataset`, `sourceGeneration`, `receivedDirectory`, and status `verified-staged-awaiting-promotion`. `snapshotEligible` is always **false**: no script creates snapshots, mutates the live receiving mirror, or authorises 0035 promotion.

The source/receiver parameters are explicit and the commands are opt-in. The existing `local-backup` Ansible rsync templates were **not** rewritten: supplied files do not establish live `pluto → mars` paths, users, locking or schedules. This is necessary before safe integration. The initial helper is for filesystem-local or shared-directory staging experiments; it is not a remotely deployed receiver service or an SSH-to-mars orchestration implementation.

## Isolated execution

On mango from `~/playbooks`:

```bash
python3 roles/diaries/tests/verify-complete-dataset-replication.py
python3 roles/diaries/tests/verify-complete-dataset-publisher.py
python3 roles/diaries/tests/verify-production-deployment-contract.py
```

The three prescribed suites were rerun on `mango` on **2026-10-09** after applying the overlay. All passed, as captured verbatim in [`RUNTIME-MANGO-REGRESSIONS-20261009.txt`](RUNTIME-MANGO-REGRESSIONS-20261009.txt):

- `verify-complete-dataset-replication.py`: **PASS** — pinned rsync, independently verified received schema-2 tree, duplicate-ID and unpinned-copy refusal, failure cleanup and non-eligible handoff.
- `verify-complete-dataset-publisher.py`: **PASS** — successful publication, corruption rejection, concurrent-reader locking, prior generation preservation, duplicate-ID refusal and temporary artefact cleanup.
- `verify-production-deployment-contract.py`: **PASS** — including the permanent approved production script set and managed scripts synchronization contract.

These are source-level and isolated tests on `mango`; they **do not** establish successful transfer to `mars`, mirror promotion, or 0035 snapshot eligibility.

## Pending Step 6 acceptance gates

1. Inventory live rsync process, SSH users, destination trees and scheduling on pluto, mars and backup.
2. Establish durable receiving staging on mars and promotion coordinated with the complete whole-backup sync.
3. Test interrupted network transfer, missing/deleted and corrupted files, and concurrent publication with actual deployed rsync commands.
4. Produce an accepted handoff only after receiving-side verification and stable mirror promotion, and keep all failed transfers snapshot-ineligible.
5. Integrate with 0035 only after its safe activation gates.

No production backup capture, deployed rsync job, snapshot timer or restore operation is changed by Step 6's isolated implementation.

## Formal manual-pilot closure — 2026-10-09

**CLOSED for manually invoked, verified `mars` pull. NOT approved for scheduled/unattended activation.** See [CLOSEOUT.md](CLOSEOUT.md), [live pull](RUNTIME-MARS-LIVE-PULL-20261009.txt), [receiver verification](RUNTIME-MARS-VERIFY-CURRENT-20261009.txt) and [four-suite test index](RUNTIME-MANGO-FOUR-SUITES-20261009.txt). The `--delete` safety audit and permanent `local-backup` role reconciliation remain mandatory gates before automatic scheduling. The handoff remains `snapshotEligible: false`.
