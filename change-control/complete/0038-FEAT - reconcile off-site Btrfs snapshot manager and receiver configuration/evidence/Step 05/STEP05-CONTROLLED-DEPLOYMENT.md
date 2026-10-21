# Step 5 — Controlled reconciliation on backup

**IN PROGRESS — includes mutating deployment.** Step 4 `--check --diff` accepted 20 October 2026; all four installed-file rollback copies were verified in Step 2. Do not delete snapshots or change receiver receipts.

## A. Before deploying — backup SSH terminal (read-only)

```bash
sudo ls -la /root/remote-backup-pre-reconcile/
sudo sh -c 'sha256sum /root/remote-backup-pre-reconcile/*'
sudo btrfs subvolume list / | grep 'mars-received/@data/'
for timer in btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-legacy-prune.timer; do
  echo "$timer"
  systemctl is-enabled "$timer" || true
  systemctl is-active "$timer" || true
done
```

Expect the verified four root-owned rollback files, existing received snapshots, and inactive/disabled local timers. The legacy timer may be absent pre-deployment. Stop and investigate any unexpected difference.

## B. Deploy — mango SSH terminal (MUTATING)

Only after confirming A is unchanged:

```bash
cd /home/richard/playbooks
./scripts/remote-backup.sh --apply
```

Expected: host `backup` only, five intended changes, `failed=0`; no local timer activation. Capture the **full real-run log**. Stop on errors; do not attempt blanket rollback or repeat the deployment without reviewing the actual error.

## C. Immediate checks — backup SSH terminal (read-only)

```bash
sudo btrfs-snapshot-manager status
sudo python3 -m json.tool /etc/btrfs-snapshot-manager.json
for timer in btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-legacy-prune.timer; do
  echo "$timer"
  systemctl is-enabled "$timer" || true
  systemctl is-active "$timer" || true
done
sudo btrfs subvolume list / | grep 'mars-received/@data/'
sudo ls -ld /@data/mars-received/@data /@data/mars-received/.replication-state
```

Expected manager `status` no longer references retired `diaries-mars-replica`; local timers remain disabled/inactive. Compare received snapshot identities with pre-deployment values, not just their count. Never dump private replication receipt contents or mutate them.

## Gate

Keep Step 5 **IN PROGRESS** until the actual deployment output and post-install receiver checks are reviewed. Step 6 covers deeper operational verification and Step 7 real-playbook idempotency. Retain `/root/remote-backup-pre-reconcile` until closure/rollback disposition is agreed.
