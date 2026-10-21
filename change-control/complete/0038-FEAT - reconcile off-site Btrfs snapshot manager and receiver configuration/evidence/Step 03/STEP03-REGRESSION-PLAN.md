# Step 3 — Regression and receiver-safety plan

**IN PROGRESS. All commands below are read-only or source-only; do not invoke `--apply`.** Existing 0037-FEAT `mars` acceptance is reused by reference.

## Stage A — Mango SSH terminal: source hygiene and targets

```bash
cd /home/richard/playbooks
git rev-parse HEAD
git status --short
git diff --check
bash -n scripts/local-backup.sh
bash -n scripts/remote-backup.sh
ansible-playbook local-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook remote-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook local-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt
ansible-playbook remote-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt
```

Required: no whitespace/syntax errors; local only `mars`, remote only `backup`. Capture output.

## Stage B — Mango SSH terminal: safe wrapper argument paths

```bash
cd /home/richard/playbooks
./scripts/remote-backup.sh --help
if ./scripts/remote-backup.sh --invalid-option; then
  echo 'FAIL: invalid argument accepted'
else
  echo 'PASS: invalid argument rejected'
fi
```

Do not execute `--apply` as part of argument testing. Existing accepted default remote dry-run was `ok=22 changed=5 failed=0`; repeat only if source or environment changes. For source-only non-execution proof of `--apply` dispatch, use a disposable mocked `ansible-playbook` executable in a feature-local `tests/` harness, not a live apply.

## Stage C — Mango SSH terminal: receiver safety source inspection

```bash
cd /home/richard/playbooks
grep -R -n -E 'btrfs_snapshot_(activation_enabled|require_verified_diaries|writer_lock_path|unattended_legacy_prune_enabled)|mars-received|diaries-mars-replica' roles/snapshots roles/remote-backup || true
sed -n '1,160p' roles/remote-backup/tasks/main.yaml
sed -n '1,175p' roles/remote-backup/tasks/native.yaml
sed -n '1,110p' roles/snapshots/templates/btrfs-snapshot-manager.json.j2
```

Check: receiver-only deployed JSON defaults with empty writer lock, `verification.required=false`, no legacy dataset reference; local timer activation disabled; received tree and `.replication-state` continue to be managed exclusively by the native receiver; verify no unintended receiver-side mutations. **Do not assume a grep result proves a negative: inspect task `when` conditions and role imports.**

## Stage D — Source regression selection

Discover available installed regressions under `roles/snapshots/tests/` and `roles/remote-backup/tests/` (where present); select targeted read-only/source-only tests first. Do not blindly run a test that modifies real Btrfs state. Put new feature-specific test drivers/fixtures in this feature's `tests/` directory. Document commands, exit codes and limitations.

**Step 3 exit gate:** record passing results and explicit safety decision; otherwise remain IN PROGRESS. Continue to Step 4 only after acceptance.
