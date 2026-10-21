# Step 4 — Final Ansible rehearsal and acceptance gate

**IN PROGRESS. Read-only planning only; no `--apply`.**

## Terminal: mango (SSH)

```bash
cd /home/richard/playbooks
git status --short
git diff --check
ansible-playbook remote-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt
ansible-playbook remote-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
./scripts/remote-backup.sh
```

## Exact change review

- Target must be `backup` only, with no inventory parser warnings.
- Anticipated five changed tasks: manager executable, history executable, manifest verifier, JSON configuration, and installation of two systemd legacy prune **unit files** in one task (do not confuse unit installation with timer activation).
- JSON: remove obsolete `diaries-mars-replica` writer-lock/dataset paths; set local verification false and writer lock empty; preserve `snapshot_root=/@snapshots`; checkpoint/replication protections false for `backup` only.
- Native receive tree `/@data/mars-received/@data` and receipts `/@data/mars-received/.replication-state` must not appear as changed targets. No subvolume creation/deletion, snapshot pruning, receiver receipt modification, replication policy or schedule change.
- Creation/prune/legacy-prune timer activation must remain skipped. Existing Snapper timers should remain disabled. Confirm no other unrelated diffs.
- Record `ok`, `changed`, `failed`, `skipped` and command provenance; explicitly approve only the exact reviewed deployment scope.

**Gate:** accept or reject final actual diff before Step 5 deployment. Ansible check mode is predictive, not proof of runtime health. Do not repeat full restore or off-site send.
