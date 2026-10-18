# 0036-FEAT Step 7 — Disposable end-to-end rehearsal: accepted evidence and formal closure

**Decision date:** 2026-10-16  
**Disposition:** **CLOSED** — accepted disposable correctness and efficiency verification; **NOT** production cutover.  
**Execution:** `mars`, operator-supplied rehearsal output and cleanup evidence, 2026-10-16.

## Scope and controlled environment

Rehearsal: `verify-0036-step7-disposable-integration.py` using `pluto` as guarded disposable source and `/media/usb/diaries-0036-rehearsal` as the dedicated disposable Btrfs parent on `mars`. Fixture contained synthetic PostgreSQL artifacts and schema-2 dataset records. Previously accepted Step 3 testing covered real PostgreSQL dump and restore. Active backup timers, publication paths and off-site receiver were not used or modified. Test subvolumes and the remote fixture were disposable.

## Accepted results

| Acceptance check | Evidence | Disposition |
|---|---|---|
| Initial guarded receive | `PASS: initial guarded transfer into disposable Btrfs working subvolume` | PASS |
| Read-only snapshot | `PASS: read-only Btrfs snapshot created and retained` | PASS |
| Incremental transfer selection | `MEASURE: dry-run incremental regular file transfers=5; unchanged large file excluded=True` | PASS |
| Change/add/delete | `PASS: incremental changed/added/deleted files; older snapshot unchanged` | PASS |
| Two historical restore points | `PASS: both historical read-only snapshot datasets pass manifest and disposable Files restore-stage validation` | PASS |
| Btrfs COW efficiency | `PASS: unchanged snapshot Files share physical Btrfs extents (no automatic dedup assumption)` | PASS |
| Rejected receive | `PASS: rejected/failed receive invalidates eligibility and retains previous snapshot` | PASS |
| Stale marker | `PASS: stale source acceptance is rejected; snapshot eligibility revoked` | PASS |
| Overlap refusal | `PASS: overlapping receiver was blocked by writer lock (timeout 5s)` | PASS |
| Verified recovery | `PASS: retry restores eligibility after independent schema-2 validation` | PASS |
| Overall functional rehearsal | `PASS: 0036 Step 7 disposable integration (no production paths touched)` and `Exit status: 0` | PASS |

The five-file count describes a dry-run transfer selection, not byte throughput, storage reduction percentage or a physical Btrfs deduplication process. The actual extent-sharing test independently confirms physical sharing of unchanged data between snapshots.

## Cleanup reconciliation

The script attempted deletion without privileges and issued three `CLEANUP REQUIRED`/EPERM warnings. This is a test-harness privilege limitation, not a failed functional check. Operator inspected the exact test-only paths and removed them with `sudo btrfs subvolume delete`, in order:

1. `diaries-0036-rehearsal/disposable-ecaf51ab9f55-snapshot-second` — subvolume **20782**.
2. `diaries-0036-rehearsal/disposable-ecaf51ab9f55-snapshot` — subvolume **20781**.
3. `diaries-0036-rehearsal/disposable-ecaf51ab9f55` — subvolume **20780**.

Deletion returned success for all three IDs. A subsequent `sudo btrfs subvolume list /media/usb | grep 'diaries-0036-rehearsal/' || true` returned no entries. **Cleanup accepted; no rerun requested.**

## Evidence boundaries and inherited assurance

- New Step 7 evidence is a disposable physical Btrfs/SSH integration and filesystem-efficiency test, **not** an unattended production run.
- PostgreSQL database files in the Step 7 fixture were synthetic; the real PostgreSQL dump/restore check was previously accepted under Step 3.
- No new physical `mars → backup` Btrfs push, receipt or off-site restore occurred during Step 7. Step 6 source/offline compatibility and accepted 0034/0035 live operational evidence are inherited.
- Neither the current legacy `diaries-backup` symlink nor production snapshots, replication ancestry, schedules or publication switches were changed.

## Formal gate decision and hand-off

**Step 7 is CLOSED as of 2026-10-16.** Functional and cleanup evidence are accepted; no further Step 7 tests are required.

**Step 8 remains OPEN:** explicit cutover authorisation; checked rollback and legacy preservation; controlled switch from 0034 publication to fixed working copy; validation of new unattended cycles (at least two) and off-site receipt; reconciliation of temporary feature-prefixed production identifiers and superseded experiment artifacts; and approved close-out. Do not infer Step 8 completion from Step 7 evidence, or remove historical generations without separate approval. No Docker application image build is required for Step 7 closure.
