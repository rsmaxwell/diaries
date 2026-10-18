# 0036-FEAT — Step 6 off-site push and historical compatibility: evidence reconciliation and closure

**Date:** 2026-10-16  
**Disposition:** **CLOSED** — targeted offline compatibility; not production activation or new off-site transfer acceptance.  
**System under test:** Playbooks source and existing 0034/0035 backup/replication/history contracts.

## Accepted operator evidence on `mango`

Commands executed from `~/playbooks` (operator log `note(20261016-130414).txt`):

```bash
python3 roles/remote-backup/tests/verify-0036-offsite-history-compatibility.py
python3 roles/remote-backup/tests/verify-native-btrfs-push.py
python3 roles/remote-backup/tests/verify-replication-protection.py
python3 roles/snapshots/tests/verify-diaries-backup-history.py
```

All **PASS**. Explicit output accepted:

- Historical generation-symlink and fixed-directory snapshots coexist in read-only history. Historical schema-2 restore references remain discoverable without rewriting snapshots.
- Off-site incremental parent selection uses verified source Btrfs UUID, not dataset directory layout; receiver receipt checks ancestry and rejects an incorrect parent UUID.
- Existing native push regression: full/incremental transfer, verified parent, reseed and receipt guards — PASS (regression/mocked test, not a new network push).
- Existing replication protection regression: invalid/missing protection fails closed and source pin lifecycle wired — PASS.
- History regression: repeated backup IDs grouped into occurrences; incompatible same-ID manifest identities reported as conflicts; symlink escape rejected; safe fixed publication resolved and corrupted live publication rejected — PASS.

## Compatibility decision

**No production change required** to the sender, off-site receiver, snapshot manager, pruning or history algorithms for Step 6. Off-site replication operates on immutable Btrfs snapshots and verified UUID ancestry. Contents may hold historical generation-backed datasets or the 0036 fixed working directory; historical schema-2 format and restore references stay intact.

## Limits, inheritance and remaining gates

The new 0036 compatibility test is **offline**, with disposable fixtures and mocked endpoints. These passing regressions are not evidence of a newly executed live `mars → backup` push, receiver acceptance or physical restore under the revised fixed-working-copy setup. Previously accepted 0034/0035 real operational transfer, receipt and restore evidence is inherited; no repeat of their full acceptance matrix is needed to close this targeted gate.

**Step 7:** disposable integrated revised-workflow rehearsal, with its own approved scope and new evidence.  
**Step 8:** actual fixed-publication migration, controlled scheduler activation, observed unattended cycles, off-site receipt, rollback and carefully approved legacy cleanup. Do not change production timers or sources, delete snapshots, reseed remote replicas or alter receipts as part of Step 6 closure.

## Formal closure

**Step 6 — CLOSED on 2026-10-16.** All agreed targeted compatibility and inherited regressions passed on `mango`; no outstanding Step 6 blocker. **0036-FEAT remains IN PROGRESS** with Steps 7 and 8 open. No Docker image build required.
