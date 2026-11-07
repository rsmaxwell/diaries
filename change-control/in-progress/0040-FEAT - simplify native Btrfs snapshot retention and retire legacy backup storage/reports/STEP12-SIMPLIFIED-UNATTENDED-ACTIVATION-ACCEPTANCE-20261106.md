# 0040-FEAT — Step 12 simplified unattended activation acceptance

**Date:** 6 November 2026  
**Gate:** Latest-snapshot implementation deployment and systemd activation **ACCEPTED**.  
**Feature status:** Step 12 **OPEN** pending durable inventory acceptance and successful first unattended scheduled run.

## Accepted evidence and source identity

- Accepted prior baseline: legacy journal archived without destroying historical snapshots/receipts; independent common parent bootstrap and manual replication cycle passed. See the existing Step 12 manual-cutover acceptance report and raw log `step12-controlled-cutover-execute-20261106-155222-1432.txt`.
- A subsequent source inventory found 121 snapshots newer than `20261101-150004Z`; the initial simplified sender selected oldest-first. The 6 November corrected Playbooks source selects **newest eligible snapshot** and transfers **one snapshot per invocation**, restoring the existing daily `--latest` scheduling behaviour.
- Current Playbooks source verified before deployment: `roles/btrfs-replication/files/btrfs-simplified-replication.py`, SHA-256 `cfa8a696b36eb49935d518cfd2c99d38e28fe3fbbfaa7a0faa6618a485e2fd36`. Playbooks checkout was on `main` at commit `813b7210d08865337770ae821bb9d88529115188`, with preserved, uncommitted feature edits.
- Source regression and check-mode previews: `evidence/Step 12/raw-logs/step12-latest-selection-acceptance-preview-20261106-165117.txt`; operator output `note(20261106-165153).txt`. Accepted preview: one binary replacement each on `mars` and `backup`, and source-only `btrfs-native-push.service` plus timer activation changes on `mars`, without other resource changes.
- Production deployment output: `evidence/Step 12/raw-logs/step12-latest-selection-deployment-20261106-165837.txt`; operator output `note(20261106-170429).txt`. The guarded deployment script reports `PASS: Simplified replication deployment and activation` and `PASS: Step 12 operational activation` (exit status zero). The script checked installed hashes, performed a controlled newest-snapshot cycle, and compared source/receiver agreed-parent JSON states. The abbreviated terminal output does not expose the new parent timestamp; obtain it from the raw log or independent readback rather than inventing it.
- Observed `systemctl show -p ExecStart`: `/usr/local/bin/btrfs-simplified-replication sender cycle`. Timer next trigger: **Saturday 7 November 2026, 03:30 UTC**.

## Outstanding acceptance conditions

1. **Durable inventory values.** The source bundle `playbook-sources-20261106-163125.zip` contains `roles/btrfs-replication/defaults/main.yaml`, where `btrfs_native_push_schedule_enabled`, `btrfs_simplified_replication_install_enabled`, and `btrfs_simplified_replication_active_enabled` all default to `false`. Deployment used explicit `-e` values. The live `/etc/ansible` inventory was not included in the bundle, so it is not yet demonstrated that a future ordinary Playbooks run will preserve the activation. Inspect the effective mars and backup inventory and source files before editing, then conduct a check-mode preview **without `-e` overrides**. The desired configuration is: `mars`: schedule/install/active true; `backup`: install true and active false.
2. **First unattended timer cycle.** After 7 November 2026 at 03:30 UTC, inspect `journalctl -u btrfs-native-push.service` around the trigger, verify success/exit status and the next timer trigger, and read back matching `schema=1`, `parent`, and `prior` state JSON files on both hosts. Confirm the snapshot UUID/read-only transport identities if the run advanced. Do not assume a successful scheduled run from an enabled timer alone. A no-new-snapshot run may succeed without advancing.
3. **Evidence reconciliation.** Consolidate evidence created on `mango` into the authoritative Windows Diaries change-control repository. Preserve live journal archive and historical recovery points. No new restore or full end-to-end repeat is required solely to retest the already accepted manual transfer. Record remaining acceptance and rollback evidence before formally marking Step 12 closed.

## Safety boundaries

No further bootstrap, journal retirement, manual Btrfs transfer, snapshot deletion, or receiver pruning is authorised by this report. It records observed acceptance, not a new operation. Any inventory edits must preserve existing assignments and take account of host-over-group precedence. Avoid routine un-overridden Playbooks reruns until the inventory gate is completed; an unguarded run with role-default `false` values could restore the legacy service definition and disable the timer.
