# Step 1 — Operator read-only commands

Use the existing **backup SSH terminal**:

```bash
printf '%s\n' '=== existing manager and config ==='
sudo btrfs-snapshot-manager status || true
sudo python3 -m json.tool /etc/btrfs-snapshot-manager.json
sudo sha256sum /etc/btrfs-snapshot-manager.json /usr/local/sbin/btrfs-snapshot-manager /usr/local/sbin/diaries-backup-history
printf '%s\n' '=== timers ==='
for timer in btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-legacy-prune.timer; do
  printf '%s: enabled=' "$timer"
  systemctl is-enabled "$timer" || true
  printf '%s: active=' "$timer"
  systemctl is-active "$timer" || true
done
printf '%s\n' '=== native receiver ==='
sudo btrfs subvolume list / | grep 'mars-received/@data/' || true
sudo ls -ld /@data/mars-received /@data/mars-received/@data /@data/mars-received/.replication-state
```

Use the existing **mango SSH terminal**:

```bash
cd /home/richard/playbooks
git rev-parse HEAD
git status --short
git diff --check
ansible-inventory --host backup --vault-password-file ~/.vault_pass.txt --yaml | grep -E 'btrfs_snapshot_|btrfs_filesystem_path|btrfs_subvolume_path|btrfs_native_' || true
```

Use the existing **Cygwin terminal** for Diaries source status:

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
git rev-parse HEAD
git status --short
```

Capture terminal outputs as `evidence/Step 01/` after redacting secrets. All commands above are read-only; `status` is deliberately allowed to fail in the baseline.
