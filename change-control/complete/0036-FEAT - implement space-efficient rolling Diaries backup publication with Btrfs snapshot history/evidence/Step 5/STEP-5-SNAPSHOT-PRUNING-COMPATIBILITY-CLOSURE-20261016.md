# 0036-FEAT — Step 5 targeted 0035 snapshot/pruning compatibility closure

**Date:** 2026-10-16  
**Disposition:** **CLOSED — source-level targeted compatibility accepted; production cutover not authorised.**  
**Dependencies:** Steps 1–4 CLOSED; original 0035-FEAT accepted and CLOSED.

## Evidence accepted without further tests

1. On `mango`, `python3 roles/snapshots/tests/verify-0036-fixed-working-snapshot-compatibility.py` completed with `PASS: 0036 Step 5 targeted compatibility regression`. It confirmed:
   - Existing 0035 verification accepts a fixed schema-2 working dataset with a current acceptance marker.
   - Missing marker blocks eligibility, and changed manifest is rejected until the marker is republished.
   - Mismatched marker path is rejected; a subsequently accepted fixed receive becomes eligible.
   - Exclusive receiver lock blocks the 0035 snapshot lock during active writes.
   - 0035 pruning does not target the fixed working directory (`RETENTION sets: total=0 keep=0 sources=1`, `Would delete 0 complete timestamp sets` in the disposable scope test).
2. The first run of `python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py` completed the relevant retention, snapshot and locking checks but failed a *deployment launcher assertion* requiring a launcher that accepts `mars` (default) and `backup` explicitly. This was not a Btrfs manager failure.
3. After correcting `scripts/snapshots.sh` to accept `host="${1:-mars}"` and restrict the case to `mars|backup`, the existing 0035 regression was rerun on `mango` and fully PASSED: `PASS: snapshot launcher explicitly supports mars-first then backup deployment`, `PASS: 0035 native Btrfs snapshot-manager regression verified`, and `PASS: verified receiver snapshot creation requires pre-provisioned non-symlink writer lock`. Its retention, timestamp namespace, read-only native snapshot, verification-marker, writer interlock, shared role and default-off scheduling checks passed.
4. Inherited evidence from Step 4: a disposable guarded transfer into a real Btrfs subvolume on `mars` created a read-only snapshot, retained its original content across an incremental changed/added/deleted Files receive, rejected an unaccepted source and recovered. Final rehearsal exit was 0, and both disposable subvolumes were subsequently removed and absence confirmed. This supplements, but does not substitute for, later production cutover evidence.

## Decision and scope boundaries

- **Accepted:** Existing 0035 snapshot-manager and pruning algorithms require no production changes for the fixed working-copy layout. Existing verified marker, backup identity, shared lock and snapshot retention boundaries remain the integration contract. Logical schema-2 backup IDs and UTC timestamped Btrfs snapshot names remain distinct; timestamped pruning operates on managed snapshot sets rather than the mutable receiving directory.
- **No additional Step 5 test runs required.** Both source regression suites have accepted passing evidence. Pruning safety was checked in a disposable/mock scope, **not by deleting production snapshots**; the real Btrfs snapshot preservation was established at Step 4.
- **Inherited, not newly exercised:** independently scheduled progressive pruning at `mars` and `backup`, replication-protected parents, existing history/status/restore discovery for historical snapshots and actual unattended schedules. These remain governed by 0035 closure and must not be represented as fresh Step 5 runtime tests. Changed off-site and historical interfaces belong to Step 6; actual fixed-location operating configuration, unattended observations and deployment belong to Step 8.
- **Operational state unchanged:** no production snapshot timer, retention policy, published 0034 symlink, receiver mode, history or off-site replication was switched. No Diaries Docker image build is needed.

## Closure approval

**0036-FEAT Step 5: CLOSED on 2026-10-16.** Proceed to **Step 6 — Targeted off-site push and historical compatibility**. Feature 0036 remains **IN PROGRESS**. The future Step 8 migration plan remains unexecuted.
