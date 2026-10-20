# 0034 Step 10.P9 / 0035 Step 10: restricted remote-backup cleanup

This package is based on the uploaded Playbooks source bundle dated 2026-10-13 17:08 and the previous source-cleanup patch. The actual `mango` tree may already contain these changes; review `git diff` before committing.

**Scope:** Only `roles/remote-backup/`, plus this README and a one-shot removal script at repository root. It does **not** modify `roles/local-backup/`, `roles/snapshots/`, `roles/diaries/`, `roles/bootstrap/`, any other role, or host data. Do not delete the checkpoint `20261013-171228Z` or its hold.

## Source changes

Modify: tasks/main.yaml (delegate to shared snapshots role without obsolete rsync pull deployment); tasks/native.yaml (deploy source push and receiver; remove only old installed native-pull executable on backup); defaults/main.yaml; README.md; tests/verify-native-btrfs-static.py; tests/verify-replication-protection.py.

Remove from source (idempotently): files/btrfs-native-pull.py, files/whole-backup-pull.py, templates/whole-backup-pull.sh.j2, tests/verify-whole-backup-pull.py, tests/verify-native-btrfs-incremental.py.

Retain: all current native push, endpoint, receiver, sudoers template, accepted receipts, snapshots and checkpoint-hold state. Legacy Snapper helper source is retained pending a separate reference audit. `roles/local-backup/` has **no modifications**.

## Apply on mango

From ~/playbooks: inspect the ZIP then extract its files into the repository root. Run `bash remove-obsolete-remote-pull.sh`. Run:

```
python3 roles/remote-backup/tests/verify-native-btrfs-push.py
python3 roles/remote-backup/tests/verify-native-btrfs-static.py
python3 roles/remote-backup/tests/verify-replication-protection.py
python3 roles/remote-backup/tests/verify-native-btrfs-mounts.py
ansible-playbook --syntax-check native-btrfs.yaml
ansible-playbook --syntax-check remote-backup.yaml
git status --short -- roles/remote-backup
git diff -- roles/remote-backup
```

Review changed files before any playbook execution. `native-btrfs.yaml` installs the push paths and removes `/usr/local/bin/btrfs-native-pull` on backup, **but does not run a transfer**. If a job or rollback script still calls the old pull executable, review/remove that dependency before deploying the cleanup. Existing rsync pull binaries on backup are **not** deleted by this package; check systemd, cron and installed scripts before a separately controlled retirement. Do not delete stored replica data, receipts or historical snapshots.

After deployment verify on mars: `btrfs-native-push --snapshot <newer-snapshot> --preflight`, `sudo btrfs-snapshot-manager hold-list`, `sudo btrfs-snapshot-manager prune --dry-run`; on backup, verify latest accepted receipt and readonly received snapshot. Record results before step closeout.
