# 0041-FEAT — Step 12 scheduled replication verification correction (2026-11-16)

## Result of first scheduled run

The scheduled `btrfs-native-push.timer` triggered on 2026-11-16 at 03:30:05 UTC and the `btrfs-send` service completed successfully at 03:30:25 with status 0. Journal evidence showed dedicated SSH to `btrfs-receive`, a successful incremental receive, and the agreed parent advanced from `20261115-140017Z` to `20261116-030016Z`. Independent verification confirmed matching sender/receiver protected-parent SHA-256 hashes, root:root 0600 state files and equal verified receiver identity.

## Verification-script failure

The read-only Step 12 verification then failed at its backup-health section: `diaries-backup-status --limit 2` ran under the unprivileged SSH login and could not read `/etc/btrfs-snapshot-manager.json` (permission denied). No production replication failure was reported.

## Correction

Run the existing reporting program through `sudo -n` on mars, consistent with its root-protected configuration and the project's routine backup-health invocation. No change to filesystem permissions, users, sudoers, Btrfs operations, Playbooks or production service settings. Retain the original failed log and rerun the same read-only Step 12 verifier to finish acceptance, including the subsequent candidate-service check.

## Acceptance

Step 12 is technically successful through parent reconciliation, but the full verifier remains OPEN until the corrected rerun completes and its new log is accepted. Do not repeat the transfer.
