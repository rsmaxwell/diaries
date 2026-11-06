# Step 12 — Simplified runtime: endpoint reconciliation and install-only preview

**Date:** 2026-11-05  
**Status:** Source/integration tests accepted; operational deployment remains OPEN.

## Evidence reviewed

The read-only `ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff` output in `note(20261105-195158).txt` completed with zero failed/unreachable hosts. `mars` had 3 proposed changes, `backup` had 3. Proposed changes were simplified command installation, snapshot-manager pin protection and an unwanted update to the legacy privileged endpoint. This was a check-mode result; no installation was performed.

## Source reconciliation

The additional `receive_staged()` method, private-stream transformer, `--transaction-nonce` and `staged-receiver` allowlist entry originate from the abandoned 12.3 staged transaction implementation. The Playbooks correction removes these from `roles/btrfs-replication/files/btrfs-native-endpoint.py` while retaining the original source/receive/list/inspect/protect/release and constrained legacy receiver-delete operations. **Compare this file against newer local edits in Beyond Compare before replacing it.**

The simplified command uses `/media/usb/@snapshots/.simple-agreed-parent.json` on `mars` and `/@data/mars-received/.replication-state/.simple-agreed-parent.json` on `backup`. The manager computes the former under its configured `snapshot_root` and the latter under `receiver_state_dir`. The receiver manager template uses that state directory. **The live `/etc/btrfs-snapshot-manager.json` on `mars` must still be inspected to confirm its `snapshot_root` is `/media/usb/@snapshots`**. Both manager and new command use `/run/lock/btrfs-snapshot-manager.lock` as local lock.

## Operational boundary

Do not initialise the simplified state or run a live send/receive until `mars` and `backup` existing snapshots, parent UUIDs, SSH/sudo command and inactive staged transaction state have been read back. Do not enable receiver prune. Keep the existing `btrfs-native-push.service` command and 03:30 timer unchanged during installation-only deployment. The developer tests and disposable real-Btrfs tests are formally accepted and need not be repeated unchanged.

## Before installation

1. Apply the Playbooks reconciliation with Beyond Compare; preserve any local endpoint changes unrelated to staged receive.
2. Run `python3 roles/btrfs-replication/tests/verify-0040-simplified-cutover-readiness.py` from `/home/richard/playbooks` on `mango`.
3. Repeat check-mode against `mars,backup` with `btrfs_simplified_replication_install_enabled=true` and `btrfs_simplified_replication_active_enabled=false`, with the standard Vault password file. Confirm there are only the expected command and snapshot-manager changes; **no endpoint update**.
4. Inspect the live host configuration, current protected snapshot identities and existing timer. Only after accepting that preflight should the install-only playbook run without `--check`.

**Step 12 remains OPEN.** A successful check-mode run is not a deployment result.
