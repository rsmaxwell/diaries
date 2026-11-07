# 0040-FEAT — Increment 3E: gated receiver observation deployment

Status: IMPLEMENTED, awaiting mango regression and Ansible `--check --diff` review. Not authorised for production deployment.

Adds two independent flags (both default `false`):
- `btrfs_agreed_parent_receiver_observer_install_enabled`: copies dormant endpoint and dependency modules on `backup` only.
- `btrfs_agreed_parent_receiver_observer_sudo_enabled`: permits only the literal `--observe-receiver` command for `richard`; requires installation gate.

The existing `diaries-native-btrfs` sudoers retirement remains in place. The new rule is separate. No snapshots, state records, receipts, pruning, timers or sender operations are changed. The observer still refuses execution when agreed-parent state is absent. The configured source and receiver filesystem UUIDs in the endpoint require live read-only verification before any activation.

## Acceptance sequence (mango)

```bash
cd /home/richard/playbooks
python3 roles/btrfs-replication/tests/verify-0040-agreed-parent-ansible-gates.py
for t in state protocol evidence ssh receiver endpoint; do python3 roles/snapshots/tests/verify-0040-agreed-parent-${t}.py || exit 1; done
python3 -m py_compile roles/snapshots/files/btrfs-agreed-parent-*.py
ansible-playbook btrfs-replication.yaml --limit backup --check --diff --vault-password-file ~/.vault_pass.txt
```

Inspect the entire diff, especially sudoers, role defaults, and any pre-existing btrfs-replication tasks. Do not apply yet. The default check must not install observer files or grant observer sudo. Follow with separately approved opt-in check and runtime gate only after baseline review.
