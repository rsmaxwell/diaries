# Step 12 — Simplified receiver retention, preview and rollback

## Source and operating terminals

- **Windows Cygwin**: authoritative Diaries Git checkout at `/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries`. Apply the Diaries ZIP with Beyond Compare 4.
- **mango SSH**: Playbooks Git at `/home/richard/playbooks`, also compare/apply Playbooks ZIP with Beyond Compare 4. Logs belong under `/home/richard/diaries/change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/evidence/Step 12/raw-logs/`, then synchronise back into the Windows Diaries checkout.
- Do not assume `mango` Diaries files have been synchronised. Preserve all uncommitted work on both repositories.

## Installation preview (read-only, safe)

Terminal: **SSH to mango**:

```bash
cd /home/richard/playbooks
ansible-playbook btrfs-replication.yaml --limit backup --tags simplified-receiver-retention --check --diff --vault-password-file ~/.vault_pass.txt -e '{"btrfs_simplified_receiver_retention_install_enabled":true,"btrfs_simplified_receiver_prune_enabled":false}'
```

Only the shared manager executable, receiver manager JSON and the new dormant service/timer units should change. The systemd state task is skipped in check mode if the unit is not installed yet; its actual disabled status must be verified after installation.

## Install-only after accepting preview; **no deletion**

Terminal: **SSH to mango**:

```bash
cd /home/richard/playbooks
ansible-playbook btrfs-replication.yaml --limit backup --tags simplified-receiver-retention --vault-password-file ~/.vault_pass.txt -e '{"btrfs_simplified_receiver_retention_install_enabled":true,"btrfs_simplified_receiver_prune_enabled":false}'
ssh backup 'sudo -n systemctl is-enabled btrfs-receiver-simple-prune.timer; sudo -n systemctl is-active btrfs-receiver-simple-prune.timer'
ssh backup 'sudo -n /usr/local/sbin/btrfs-snapshot-manager --config /etc/btrfs-snapshot-manager.json receiver-simple-plan'
```

Expected timer reports: `disabled` and `inactive` (these are not errors). On backup, read-only plan results must include verification of current/prior parent UUIDs. It may REFUSE due to a historical anomaly; if so, inspect and classify without deleting anything.

## Disposable real-Btrfs acceptance

After Windows Diaries and mango Diaries sources are synchronised:

Terminal: **SSH to mango**:

```bash
cd /home/richard/diaries
FEATURE='change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage'
python3 "$FEATURE/tests/verify-0040-step12-receiver-retention-real-btrfs.py"
# Only when ready for explicitly isolated Btrfs fixture creation/deletion:
# sudo -n python3 "$FEATURE/tests/verify-0040-step12-receiver-retention-real-btrfs.py" --run
```

The second command is destructive **only to temporary loop-backed Btrfs test images** and never references the live production snapshot paths. Inspect the test implementation and check there are no active loop-device/mount conflicts before running.

## Rollback and refusal

If a read-only check fails, leave `btrfs_simplified_receiver_prune_enabled: false` and the timer disabled. Reverting only the new preview/installation does not require restoring Btrfs data. Do not manually remove `.simple-prune-pending.json` after uncertain deletion; it is required for forensic recovery. Live rollback after any approved prune can disable the timer but **cannot reconstruct deleted snapshots** unless their retained recovery counterparts are available. Live deletion therefore requires separate approval and evidence.
