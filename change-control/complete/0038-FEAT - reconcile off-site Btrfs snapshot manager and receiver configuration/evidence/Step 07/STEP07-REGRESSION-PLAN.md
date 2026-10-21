# Step 07 — Regression plan and gated commands

**Status: IN PROGRESS, 21 October 2026.** Reuse the already accepted check-mode Ansible convergence `note(20261020-205235).txt`: `backup ok=22 changed=0 unreachable=0 failed=0`. This proves predicted convergence, not the separate real-repeat acceptance.

## Stage A — source negative regression (read-only, mango SSH terminal)

```bash
cd /home/richard/playbooks
git diff --check
ansible-playbook remote-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook remote-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt
echo '=== Native receiver endpoint references (inspection only) ==='
grep -nE 'mars-received|replication-state' roles/remote-backup/files/btrfs-native-endpoint.py roles/remote-backup/files/btrfs-native-push-receiver.py
echo '=== Local manager safety defaults ==='
grep -nE 'btrfs_snapshot_(activation_enabled|require_verified_diaries|writer_lock_path|unattended_legacy_prune_enabled)' roles/snapshots/defaults/main.yaml
echo '=== Obsolete replica path in deployment inputs (expect no matches) ==='
if grep -n 'diaries-mars-replica' roles/snapshots/defaults/main.yaml roles/snapshots/templates/btrfs-snapshot-manager.json.j2 roles/remote-backup/tasks/main.yaml; then
  echo 'FAIL: obsolete manager path found'
else
  echo 'PASS: obsolete manager path absent from checked deployment inputs'
fi
```

The `grep` checks validate only **listed inputs** and are not an exhaustive repository proof. Review source configuration precedence/host variables if unexpected output occurs.

## Stage B — installed negative state (read-only, backup SSH terminal)

```bash
sudo btrfs-snapshot-manager status
sudo python3 - <<'PY'
import json
from pathlib import Path
cfg=json.loads(Path('/etc/btrfs-snapshot-manager.json').read_text())
assert cfg['writer_lock_path'] == ''
assert cfg['verification']['required'] is False
assert cfg['verification']['dataset_relative_path'] == ''
assert cfg['verification']['marker_relative_path'] == ''
assert cfg['snapshot_root'] == '/@snapshots'
assert cfg['replication_protection']['required'] is False
assert cfg['checkpoint_holds']['required'] is False
print('PASS: receiver-only local manager configuration')
PY
for timer in btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-legacy-prune.timer; do
  echo "=== $timer ==="
  systemctl is-enabled "$timer" || true
  systemctl is-active "$timer" || true
done
```

Do not run `create`, `prune`, `legacy-delete`, `legacy-prune --execute`, receiver endpoint writes or any manual send/receive for this stage.

## Stage C — real repeat-run idempotency (mutating; separate go/no-go)

The Step 7 implementation plan explicitly calls for repeating **real** Ansible and expecting `changed=0`. After Stages A/B evidence has been reviewed, a separately accepted command on **mango** is:

```bash
cd /home/richard/playbooks
./scripts/remote-backup.sh --apply
```

This is a production-changing capable command even if expected to converge with `changed=0`. Confirm target remains `backup` only and no new source edits or unintended diff exist before approval. Review actual recap and timer/receiver integrity afterwards; do not count check-mode `changed=0` as proof of a real repeat. Close Step 7 only once those outputs and negative checks pass.
