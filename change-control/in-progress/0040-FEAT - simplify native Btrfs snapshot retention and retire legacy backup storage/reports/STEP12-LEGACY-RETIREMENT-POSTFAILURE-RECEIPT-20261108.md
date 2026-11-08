# 0040-FEAT — Step 12 legacy-code retirement: post-failure reconciliation

**Date:** 8 November 2026  
**Scope:** Finalise evidence for already completed, checksum-guarded executable retirement.  
**Status:** Operational verification accepted; completion receipt still to be generated on `mango`.

## Original execution and independent acceptance

- The original guarded removal (`step12-legacy-retirement-execution-20261108-085903.txt`) verified the approved 8 November unattended receiver-prune receipt, the installed file manifest, the active services and the absence of remaining dependencies.
- Two rollback TAR archives were created and verified **before** deletion:
  - `legacy-code-mars-20261108-085914Z.tar`, SHA-256 `c7c900e99a8dd552a1966cd2ed5185dc38e57a41efd264e453fdd783cf26b638`.
  - `legacy-code-backup-20261108-085914Z.tar`, SHA-256 `7769d82d75a1c4f7bad2428a8df3d247070a8340403a7890c39d566eb892648c`.
- The tool reported removal of **39** exact legacy files on `mars` and **35** on `backup`, then exited nonzero while performing its final audit, before writing the original completion receipt. Neither the failed log nor the two archives is to be discarded.
- An independent read-only verification (`step12-legacy-retirement-postfailure-check-20261108-090527.txt`) confirmed both TAR SHA-256 values, all 74 paths absent, legacy receiver timer `LoadState=not-found`, successful simplified sender status and Diaries backup status, and both active timers enabled and active. The agreed parent remained `20261108-030011Z` with UUID `dcb7bae6-d1b0-824c-9d2d-1f5c7b8a2d58`.
- No second deletion or rollback is necessary; a repeat `--apply` is prohibited because the previous manifest no longer describes existing files.

## Final-audit defect and correction

The previous final audit called `systemctl list-unit-files btrfs-legacy-prune.timer` after removing that unit. On systemd, querying a missing unit by that command can exit 1, which the retirement tool treated as a failure. The new final audit instead checks `systemctl show btrfs-legacy-prune.timer -p LoadState --value` and requires `not-found`, consistent with the independently accepted result. The pre-removal check still requires the old timer to be present, disabled and inactive.

## Receipt-only finalisation

The tool now provides `--finalize` as a separately confirmed, **non-destructive** mode for this already completed removal. It:

1. Verifies the original accepted pruning receipt and exact approved path manifest.
2. Checks the two existing local rollback TAR files against their **previously recorded SHA-256 digests** and compares every TAR member's path, root ownership, mode, size and content digest with the manifest.
3. Read-only checks on `mars` and `backup` confirm all 74 paths remain absent, including dangling symlinks.
4. Rechecks active sender/receiver status, legacy timer absence, remaining dependencies, sudoers absence, and both active schedules.
5. Writes a new, distinct finalisation receipt under `evidence/Step 12/rollback/legacy-code-retirement-20261108-085914Z.json` using exclusive creation. It records original removal stamp and new verification time. The code does not remove, restore or reinstall any remote files, trigger replication or prune snapshots, or invoke `systemctl daemon-reload`.

**Offline verification:** Existing `verify-0040-step12-tools-offline.py` PASSED; new `verify-0040-step12-post-retirement-finalize-offline.py` PASSED (tests missing systemd unit, loaded-unit refusal, archive checksum refusal, receipt non-overwrite and remaining-path refusal). Live finalisation requires a separate execution result; do not mark Step 12 CLOSED from preparation alone.

## Evidence preservation and closure

Transfer original failed execution, independent successful postfailure verification, both TAR rollback archives and the generated JSON receipt from `mango` into the authoritative Windows Diaries feature directory, with SHA-256 verification. Commit the original evidence unchanged. After source/evidence synchronisation, formally reconcile Step 12 and assess the remaining 0040-FEAT closure criteria. No repeat restore or end-to-end replication is required based on the already accepted correctness evidence.
