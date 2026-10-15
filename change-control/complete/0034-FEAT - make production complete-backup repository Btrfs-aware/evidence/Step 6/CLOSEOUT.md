# 0034-FEAT — Step 6 formal close-out

Date: 2026-10-09  
Decision: **CLOSED — manual, opt-in replication-safe pull and independently verified receiving publication**  
Scope limitation: **not approved for unattended scheduling or 0035 snapshot acceptance**.

## Accepted evidence

1. **Mango regressions**: `RUNTIME-MANGO-REGRESSIONS-20261009.txt` records isolated replication, publisher, and production deployment-contract PASS. A later four-suite run additionally passed `verify-diaries-pull.py` (operator transcript `note(20261009-095408).txt`; recorded below).
2. **Controlled installation**: Ansible installed tools on `pluto` and `mars` and passed non-mutating preflights. The corrected pilot installed the `mars` helper and validators under `/home/richard/scripts/backup`, owned by `richard:richard`, mode 0755 (operator transcript `note(20261009-135007).txt`).
3. **SSH direction and identity**: `richard@mars` successfully connected without prompting to `richard@pluto` on the configured SSH service (`note(20261009-132704).txt`). Root SSH was deliberately not used.
4. **Source publication**: prior completed schema-2 dataset `20261007-145013Z`, logical dataset `production`, 89 Files verified; first generation published on `pluto`, then `verify-current` and `show-current-id` succeeded. Symlink points to `.diaries-backup-generations/20261007-145013Z` (operator transcripts `note(20261009-133100).txt`, `note(20261009-133231).txt`, `note(20261009-133325).txt`, `note(20261009-133406).txt`).
5. **Mars preflight**: `PREFLIGHT OK`, no capture, transfer or publication (`note(20261009-135103).txt`).
6. **First live pull**: `richard@mars` initiated the transfer. Receiver verified schema-2 backup ID `20261007-145013Z` and 89 Files, published and verified; returned `state: verified-published` and explicitly `snapshotEligible: false` (`RUNTIME-MARS-LIVE-PULL-20261009.txt`).
7. **Independent receiver confirmation**: `verify-current` returned `VERIFIED 20261007-145013Z`; `show-current-id` returned the same ID; fixed symlink targets `.diaries-backup-generations/20261007-145013Z` (`RUNTIME-MARS-VERIFY-CURRENT-20261009.txt`).

## Explicit residual risks and future gates

- The existing root/user backup scripts on `mars`, including rsync `--delete --delete-excluded`, **have not yet been demonstrated unable to remove or overwrite** the published Diaries mirror or its private generation store. Prior to unattended activation, inspect the actual include/exclude files and dry-run both relevant jobs against the new paths, or physically isolate their destination scopes. This is a **blocking future activation gate**.
- The isolated installer now runs the pull as `richard`, but permanent `roles/local-backup` installation and ownership conventions **are not yet reconciled**. Reconcile and regression-test in Step 8 prior to scheduling.
- The old root-installed pilot helper copies have **not** been confirmed removed. Remove only with the controlled cleanup option and after verifying dependencies.
- A verified published Diaries backup is **not** proof of a consistent whole-backup Btrfs snapshot. Handoff remains `snapshotEligible: false`; 0035 owns the receiving snapshot acceptance barrier, retention and remote `backup` pull.
- Only one real backup ID and one live transfer were tested in this manual pilot. Later end-to-end steps must cover successive generations, concurrent live mutation, interruptions and recovery.
- The 0033 complete-dataset capture pipeline is not yet automatically wired to this publisher; Step 9/feature completion must address the production producer.

## Closure boundary

Step 6 is closed **for its isolated and operator-invoked `mars`-pull implementation, preflight, verification and first live transfer acceptance**. Closure authorises neither cron activation nor unattended rsync deletion, nor changing existing Snapper/native Btrfs timers. These remain planned work, not silently accepted risks. No Docker rebuild, production restore, or new snapshot is required for this close-out.
