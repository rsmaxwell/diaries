# 0040-FEAT Step 12.3 — Gate A dormant installation acceptance

Date: 2026-11-01. **Technical Gate A: ACCEPTED; Step 12.3 remains OPEN.** This is the narrow *dormant module deployment gate*, not an assertion that all six governing Step 12.3 closure gates are complete.

## Accepted command evidence (user-uploaded terminal logs)

- Isolated preview of `install-step12-3-dormant-receiver.yaml` on `backup`: 11 absent targets, 11 proposed copies, `ok=6 changed=1 failed=0`; check mode only.
- Actual deployment: 11 named copies `changed`, `ok=6 changed=1 unreachable=0 failed=0`.
- Post-deployment: all 11 source-to-target comparisons PASS, with `root:root`, `0644`, non-symlink regular files.
- Idempotency: `ok=5 changed=0 unreachable=0 failed=0 skipped=1`.
- `/usr/local/bin/btrfs-agreed-parent-receiver` absent. Existing `/usr/local/bin/btrfs-native-push-receiver`, `/usr/local/libexec/btrfs-native-endpoint`, `/usr/local/sbin/btrfs-snapshot-manager` present and executable. Historical pre/post hashes of these operational files were not compared; isolated installer did not target them.
- No snapshots, SSH configuration, sudoers, timers, receipts or agreed-parent state were changed by this isolated installer.

## Evidence preservation and provenance

The corresponding raw console transcripts are the 2026-11-01 uploads `note(20261101-121942).txt` (preview), `note(20261101-122317).txt` (deployment), `note(20261101-122426).txt` (file comparison), `note(20261101-122549).txt` (idempotency), `note(20261101-122618).txt` (inactivity and installed operational paths). Copy the originals, without redaction or reconstruction, into `evidence/Step 12/Gate A/` in the authoritative Windows Diaries checkout. This report does not claim raw logs are already archived.

The isolated playbook remains under this feature's `tools/`. A working copy was staged in `/home/richard/playbooks` to execute Ansible on mango; authoritative feature ownership stays in Diaries on Windows.

## Hold

The new entrypoint is **not enabled**. Do not execute Btrfs send/receive, promote parents, prune snapshots, change timers, or expose new sudo/SSH commands as a consequence of Gate A acceptance.
