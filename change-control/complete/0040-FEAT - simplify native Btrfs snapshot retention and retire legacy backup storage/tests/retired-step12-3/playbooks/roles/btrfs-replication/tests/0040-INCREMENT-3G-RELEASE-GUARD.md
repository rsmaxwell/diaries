# 0040-FEAT Increment 3G — Source release guard (candidate)

Status: source candidate; **NOT deployed**. Based on Playbooks export 2026-10-30 13:01.

## Change

`roles/btrfs-replication/files/btrfs-native-endpoint.py` reads optional root-owned
`/media/usb/@snapshots/.agreed-parent.json` while holding the existing manager
lock, before `release-source` mutates legacy protection. When present it refuses
releasing established, pending or previous snapshots. Missing state preserves
legacy behaviour. Corrupt/unsafe state fails closed. Existing `prune_protected`
checks remain intact. No automatic state bootstrap or protection migration.

## Important remaining gates

- This does NOT yet integrate agreed-parent protection into `btrfs-snapshot-manager`
  prune selection. That must happen **before** durable agreed-parent state is created.
- `btrfs-native-push` currently logs release failures as warnings; a refused
  release is safe but must be checked operationally.
- Existing 3G snapshot pin remains protected by `prune_protected`, independently.
- Coordinate timers and live locks before any initial state write. Never rely on
  the existence of this ZIP as protection on installed hosts.
- Test both established/pending/previous Btrfs pruning on disposable fixtures;
  audit sender and receiver lock ordering and exact Ansible destination paths.
- Perform `--check --diff` on `mars`, explicitly review changes and obtain a
  separate deployment decision. No scheduling changes approved here.

## Verification on mango

```sh
cd /home/richard/playbooks
python3 roles/btrfs-replication/tests/verify-0040-agreed-parent-release-guard.py
python3 -m py_compile roles/btrfs-replication/files/btrfs-native-endpoint.py
ansible-playbook btrfs-replication.yaml --limit mars --check --diff \
  --vault-password-file ~/.vault_pass.txt
```

The final Ansible command is for REVIEW ONLY, not approval to deploy. Inspect
unrelated changes; the source export predates later 3E role edits.
