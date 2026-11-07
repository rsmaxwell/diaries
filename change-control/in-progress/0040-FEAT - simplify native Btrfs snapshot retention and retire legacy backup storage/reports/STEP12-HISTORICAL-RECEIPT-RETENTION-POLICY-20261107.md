# 0040-FEAT Step 12 — Historical receipt retention-policy correction

**Status:** Implementation prepared and source regressions passed. **Live deploy, new disposable Btrfs test and any destructive prune remain unaccepted.** Step 12 OPEN.

## Accepted starting evidence

- Simplified sender scheduled 7 November 03:30 UTC: success, with matching source and receiver agreed-parent states at `20261107-030031Z` and previous `20261106-160001Z`.
- Receiver retention installed on `backup` with `receiver_prune_enabled=false`, pruning timer disabled/inactive, matching installed manager checksum `da9d7f02b9145c162b8bf4c75bab5921b885f55c8b9fde1f94c95894f6cf8274`.
- Previous disposable real-Btrfs receiver prune test passed, including parent/hold and receipt preservation.
- Receiver plan on 7 November: 30 retained, 27 historical receipts, 2 explicit checkpoint holds, zero deletion candidates.

## Defect in migration policy

The first receiver implementation unconditionally added all timestamps with historical receipt files to the retention keep-set, even when they expired under the normal shared bucket policy; it also refused any historical receipt whose snapshot had already been removed. These protections made legacy receipts an indefinite retention dependency despite the simplified sender not creating or reading them.

## Integrated correction

1. Preserve existing timestamped legacy receipt files **unchanged** as forensic evidence, without trusting their contents as Btrfs identity or pinning their snapshots.
2. Treat an orphan historical receipt as preserved evidence after an authorised snapshot prune. Still reject unsafe receipt paths such as symlinks and non-regular paths.
3. Continue validating every present received Btrfs subvolume read-only status and Received UUID; retain agreed parent/prior, holds, legacy parent pins, newer-than-parent snapshots and normal bucket keeps.
4. The plan reports receipt count, receipt-backed candidates and historical orphan-receipt count. Receipt-backed candidate lines are visibly marked.
5. Do not change the existing deletion gate, bounded per-run limit, fail-closed prune journal, 03:30 sender, or disabled 04:15 receiver timer.

## Retention calculation caveat

The existing shared policy `hourly=48, daily=14, weekly=12, monthly=24, yearly=5` keeps the 48 **newest occupied hourly buckets**, not only snapshots from the last 48 elapsed hours. Re-evaluating the 30 timestamps in the accepted 7 November receiver plan against that policy still yields **zero candidates**, even without the legacy receipt pin, because all snapshots occupy fewer than 48 distinct hourly buckets. Actual candidate counts must be determined by a new read-only plan on `backup` after deployment. No live deletion is warranted on the basis of the source fixture alone.

## Verification and remaining gates

- Consolidated source-only fixture regressions: 10 selected scripts PASS, including 17 receiver-retention tests, in the attached feature raw log.
- Updated disposable real-Btrfs fixture explicitly verifies pruning a receipt-backed snapshot and retaining its exact receipt bytes while the parent and checkpoint hold remain protected. It **has not yet been re-run** with the updated code.
- Apply reviewed Playbooks ZIP via Beyond Compare 4 on `mango`, preserving uncommitted changes. Check source hash, test suite, and Ansible `--check --diff` with receiver pruning explicitly disabled; install just the shared manager; verify installed hash, timer disabled/inactive, and read-only retention plan.
- An eventual live deletion requires reviewed exact candidates and explicit user approval. Preserve recovery checkpoints and retain the journal for reconciliation on uncertainty. Never delete legacy receipts as part of pruning.

**Step 12 stays OPEN.** Do not infer closed acceptance from the current source tests or prior tests of the superseded retention policy.
