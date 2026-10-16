# 0036-FEAT — Controlled `mars` publication-to-fixed-working-copy migration plan

**Status:** APPROVED AS PROCEDURE ONLY; **NOT EXECUTED**. Execution/authorisation is deferred to **Step 8** after Steps 5–7. Do not treat these instructions as a cutover command sequence.

## Principles and existing constraints

- Current 0034 `mars` publication uses `diaries-backup` as a **symlink** into preserved generations. The Step 4 fixed receiver explicitly **refuses that symlink**; a direct incremental overwrite is neither safe nor supported.
- The fixed receiver writes a real `diaries-backup/` directory **inside the same 0035 snapshot-source Btrfs subvolume**, under the established `backup/pluto/` dataset location, using `rsync --delete`. Keep `database/`, `files/`, `verification/` and `dataset-manifest.json` schema-2 contract unchanged.
- The 0035 repository whole-backup exclusive lock and snapshot eligibility marker must refer to the same snapshot source and be the same resources consumed by existing snapshot orchestration. Before/through mutation invalidate eligibility; after independent verification atomically publish the accepted marker.
- Never run rsync `--delete` against the symlink, generation store, historical snapshots or remote off-site snapshots. Do not create nested Btrfs subvolumes for the receiving dataset, which would break 0035 snapshot/send coverage.

## Pre-cutover gate (Step 8)

1. Review and record **actual deployed** `mars` Btrfs root, `backup/pluto` location, source symlink target, generation directories, verification marker, repository lock and scheduled service/timer units, plus matching `pluto` source location and guards. **No path is inferred from this plan**. Check source bundle and deployed Ansible vars for drift before commands are constructed.
2. Confirm Steps 5–7 acceptance, a recent verified read-only checkpoint retained independently, historical restore discovery and rollback procedure. Confirm sufficient filesystem space and a current verified 0034 publication remains accessible.
3. Keep fixed `pluto` capture and `mars` pull **disabled**. Obtain explicit operator cutover approval. Arrange a maintenance interval; stop/disable competing legacy and new capture/pull jobs, hold snapshot operations through the established writer lock, and check no replication/snapshot/delete operation is currently consuming the receiving location.
4. Capture before-state: symlink target, manifest identity/digest, marker contents, latest accepted snapshot, service state, current off-site receipt and last success. Use a durable journal naming the preserved rollback assets.

## Staged migration (Step 8; exact commands to be generated only after paths verified)

5. **Do not follow or overwrite the symlink.** Rename/move only the current `diaries-backup` symlink into a distinct preserved rollback name **after confirming** it points to the expected legacy generation. Leave the target generation and previous snapshots untouched. Avoid deleting either. A rename is preferable to destructive unlink/recreate.
6. Create the new plain working directory at the now-vacant `backup/pluto/diaries-backup`, beneath the existing 0035 snapshot-source Btrfs boundary (not a nested subvolume). Initialise ownership/permissions according to the existing service account. Invalidate old snapshot eligibility before populating it.
7. Stage/reconcile a verified fixed schema-2 source on `pluto` using the already tested publisher guard; use the fixed receiver under its existing whole-backup lock for the initial `rsync --delete` and independent validator. Acceptance requires expected logical dataset/backup ID, manifest digest, and eligible marker referencing the correct relative path. No snapshot should be taken while the marker is missing.
8. Check 0035 snapshot history/status and protected ancestry are intact; then enable **only the agreed** new unattended workflow, with old capture/pull units still disabled. Do not alter pruning/replication rules without Step 5/6 evidence and explicit approval. Observe at least two unattended cycles and a successful off-site receipt per Step 8, plus targeted recovery evidence.
9. Record new marker, snapshot IDs/timestamps, verified manifest, timer/unit states and replication receipt; formally accept cutover only after these criteria pass.

## Rollback strategy (Step 8)

- Trigger on unsuccessful initial verify, wrong identity/path, missing snapshot marker, failed scheduled cycles, or incompatible history/replication. Immediately stop new producer/receiver timers and ensure writer/snapshot locks are respected.
- **Preserve the partially populated fixed dataset** for diagnosis (rename/move aside under a distinct quarantine name while locks are held); never run `rsync --delete` onto the old generation or rollback symlink.
- Restore the preserved `diaries-backup` symlink to its original name/verified target; verify the existing 0034 publication and original 0035 accepted eligibility and snapshot contract **before** re-enabling old jobs. Regenerate/revalidate marker only using existing supported verification tooling; do not copy a stale eligible marker across differing manifest identities.
- Keep historical read-only Btrfs snapshots, backup-host received snapshots, protected send parents, off-site receipts and legacy generation store untouched. Record failure/rollback in Step 8 evidence. Obtain explicit separate approval for any later cleanup.

## Non-goals / deferred work

No cutover, scheduler migration, production command execution, cleanup, off-site resend, new Docker image, or quantitative transfer benchmarking occurs as part of Step 4. Step 5 tests snapshot/pruning compatibility; Step 6 tests off-site/historical interfaces; Step 7 covers its disposable broader verification; Step 8 owns authorisation, unattended observation and retirement.
