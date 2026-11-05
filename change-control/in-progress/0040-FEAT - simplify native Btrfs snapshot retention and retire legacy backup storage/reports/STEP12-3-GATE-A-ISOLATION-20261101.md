# 0040-FEAT Step 12.3 — isolated Gate A installer

Apply this ZIP to the **Diaries repository root** using Beyond Compare 4, not to Playbooks. The feature-specific playbook is stored in this feature's `tools/` directory. It uses only the 11 modules already present in `/home/richard/playbooks/roles/btrfs-replication/files` on mango.

The playbook **does not import** `btrfs-replication` role tasks. It rejects any host other than `backup`, checks source hashes, refuses replacement of existing differing files, and installs only missing non-executable Python modules (`0644`). No SSH route, sudo rule, key, snapshots, timer, or operational receiver is changed. The old operational modules remain untouched.

From the **mango SSH terminal**, run with cwd `/home/richard/playbooks`:

```bash
cd /home/richard/playbooks
GATE_A='/home/richard/diaries/change-control/in-progress/0040-FEAT - simplify native Btrfs snapshot retention and retire legacy backup storage/tools/install-step12-3-dormant-receiver.yaml'
ansible-playbook "$GATE_A" --limit backup --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook "$GATE_A" --limit backup --check --diff --vault-password-file ~/.vault_pass.txt
```

Review the output **before** running the installation without `--check`. Expected preview: 11 missing files, no operational modifications. If any existing destination differs, the assert fails closed and no install task starts. It is possible that some files are already present; expected count must then be adjusted after inspecting results.

The eventual installation and idempotency checks should be run only after explicit acceptance of the preview. Save terminal evidence under this feature's `evidence/` directory. Step 12.3 remains OPEN.
