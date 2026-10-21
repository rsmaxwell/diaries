# Step 14 — non-destructive operator evidence collection

On **mango**, from the Playbooks repository:

```bash
cd /home/richard/playbooks
git rev-parse HEAD
git status --short
git diff --check
python3 roles/local-backup/tests/verify-diaries-pull.py
ansible-playbook local-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ssh mars 'for f in diaries-pull.py complete-dataset-publisher.py complete-dataset-manifest.py; do if sudo test -e "/root/scripts/backup/$f"; then echo "STILL PRESENT: $f"; else echo "ABSENT: $f"; fi; done; stat -c "%a %U:%G %n" /home/richard/scripts/backup; systemctl is-enabled diaries-pull.timer btrfs-snapshot-create.timer btrfs-snapshot-prune.timer btrfs-legacy-prune.timer; sudo btrfs-snapshot-manager status'
```

On **Windows/Cygwin**, from the Diaries repository root:

```bash
git rev-parse HEAD
git status --short
git diff --check
```

Before deleting or relocating any source or host workspaces, inventory them and review each item. Commit/record exact revisions first. After approval, move the entire feature directory under `change-control/complete/`; do not recreate it without the evidence tree. No new production mutation or destructive Btrfs action is required for this gate.
