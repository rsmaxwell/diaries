# 0036-FEAT — Step 4 receiving implementation, rehearsal evidence and closure

**Recorded:** 2026-10-16  
**Disposition:** **Step 4 CLOSED — implementation, source regression and disposable real-Btrfs verification accepted.**  
**Production cutover:** **NOT AUTHORISED**; remains Step 8.  
**Evidence policy:** Accept reported successful rehearsal and cleanup. No additional tests are required for Step 4 closure.

## Accepted evidence

1. **Source regression on `mango`: PASS.** `python3 roles/local-backup/tests/verify-0036-fixed-destination.py` returned `VERIFIED_FIXED_RECEIVE`, verified fixed working-copy `rsync --delete`, marker creation only after schema-2 validation, marker revocation on failure, refusal to overwrite a legacy publication symlink, and preserved historical directory. Existing `verify-diaries-pull.py` regression also PASS, preserving the 0034 default receiving path and 0035 writer-lock integration.
2. **Real disposable Btrfs rehearsal on `mars`: PASS, exit status 0 (2026-10-16).** `verify-0036-disposable-btrfs-receive.py` used an explicitly empty test parent `/media/usb/diaries-0036-rehearsal` on `/dev/sdb1` Btrfs; source guarded over SSH from `pluto`, using disposable schema-2 fixtures, not production source data. Operator output:
   - `PASS: initial guarded transfer into disposable Btrfs working subvolume`
   - `PASS: read-only Btrfs snapshot created and retained`
   - `PASS: incremental changed/added/deleted files; older snapshot unchanged`
   - `PASS: rejected/failed receive invalidates eligibility and retains previous snapshot`
   - `PASS: retry restores eligibility after independent schema-2 validation`
   - `PASS: disposable Btrfs receiver rehearsal completed (no production paths touched)`
3. **Harness corrections are not production failures.** Initial rehearsal stopped when second fixture manifest was regenerated without removing the old `dataset-manifest.json`; harness corrected to unlink prior disposable manifest. Non-privileged Btrfs deletion reported `EPERM` in `finally`, even though functional tests exited 0. This is a test cleanup privilege limitation, not evidence of failure of the receiver.
4. **Cleanup: PASS.** Operator identified `disposable-19cfa36fb25c` (Btrfs ID 20774) and `disposable-19cfa36fb25c-snapshot` (ID 20775). Both were removed with explicitly targeted `sudo btrfs subvolume delete` commands; subsequent `btrfs subvolume list /media/usb | grep 'diaries-0036-rehearsal/'` returned no matching subvolumes. Previous unsuccessful rehearsal subvolumes were also manually deleted.

## Scope / limits

- Verified real Btrfs snapshot immutability, incremental changed/add/delete, marker lifecycle and retry on **disposable synthetic backup data**; no new real production PostgreSQL dump/restore, end-to-end off-site replication, history-tool migration or unattended scheduled observation is claimed.
- The existing published 0034 source/receiver paths, timers, snapshots, off-site replication and rollback data remain unchanged. Production feature switches remain off.
- No quantitative transfer or allocated-space measurements are required to accept Step 4; any broader 0036 space-efficiency verification is addressed under Step 7 according to its agreed scope.
- Temporary `0036` feature identifiers in test code are permitted; final deployed operational naming is reconciled under Step 8.

## Migration disposition

A controlled **procedure** is defined in `STEP-4-CONTROLLED-MIGRATION-PLAN-20261016.md`. That is design readiness, not permission to execute migration. Final eligibility, real path configuration, scheduler switching, known-good checkpoint and rollback are Step 8 gates. Preserve the old symlink/generations and historical snapshots until separately approved retirement.

**Next:** Step 5 — targeted 0035 snapshot/pruning compatibility. No repeat of this accepted functional rehearsal.
