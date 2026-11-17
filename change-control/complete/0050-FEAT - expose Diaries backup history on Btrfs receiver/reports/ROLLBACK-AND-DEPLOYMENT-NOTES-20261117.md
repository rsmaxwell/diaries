# 0050 — Deployment and rollback notes (pre-deployment)

This implementation has no database migrations, snapshot mutations, timer changes, or 0041 identity/SSH changes. It adds `diaries_history` to the existing receiver manager config and installs the reader/status/verifier executables. **Do not disable source/receiver snapshot-manager protection** to make history work.

Prior to deployment capture: Playbooks and Ansible-controller HEADs/submodule status and uncommitted changes, `backup`'s `/etc/btrfs-snapshot-manager.json` checksum/mode (do not publish file contents without reviewing for secrets), installed command presence and hashes, and the read-only `btrfs-snapshot-manager status` plus `prune --dry-run --max-delete 10` and replication parent/prior. Verify that the expected `backup/pluto/diaries-backup/dataset-manifest.json` and `backup/.diaries-snapshot-verified.json` are accessible inside at least two received snapshots.

To roll back an unexpected parser/integration regression, restore only the previous Playbooks receiver-manager template and receiver history installation tasks using a reviewed Git revert or earlier approved package; reapply the restricted receiver playbook **without** destructive cleanup of snapshots or identity state. Existing reader executables may remain installed harmlessly; do not reset/checkpoint parent, receipts, holds or prune retention. Capture checksums/state before and after. Do not execute an unreviewed `git reset --hard` in a shared/uncommitted checkout.

A successful Ansible run does **not** prove history accuracy; use `sudo -n diaries-backup-status` and receiver-only fixtures followed by an explicitly selected full schema-2 verify on the receiver, and establish strict `changed=0` on reapply before accepting the step.
