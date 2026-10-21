# Step 2 — Review and rollback preparation (no deployment yet)

## Architecture acceptance

- [x] `remote-backup.yaml` targets only the `remote_backup` group = `backup`, with no `mars` in scope.
- [x] Receiver uses `/<at-data>/mars-received/@data` (actual `/@data/mars-received/@data`) and `.replication-state`; snapshot manager uses `/@snapshots`, independent of received history.
- [x] Manager config rendered with `verification.required=false`, empty writer lock, and no obsolete `diaries-mars-replica` path.
- [x] Native creation, native pruning and legacy pruning **not enabled** on `backup`; merely installing service files is not activation.
- [x] Do not run any snapshot create/prune, legacy deletion, forced send/receive, or retention mutation.

## Rollback acceptance

- [x] Identify exact installed manager/history/manifest-verifier/config paths and SHA-256 baseline from Step 1.
- [x] Decide and record a restrictive root-owned rollback directory *before* Step 5, including permissions, contents and retention; perform backup only at Step 5.
- [x] Establish rollback order for executables, JSON and `systemctl daemon-reload` if needed; use Ansible for the durable forward fix.
- [x] Identify potential impact of deploying shared `roles/snapshots` on `backup`, including added unit files, unrelated role tasks and native receiver tasks.

## Source acceptance

- [x] Resolve carriage returns / blank EOF formatting and check-mode-only wrapper behaviour without discarding intentional local edits.
- [ ] Full source regressions deferred to Step 3; repeat final `--check --diff` in Step 4. Existing post-wrapper dry-run passed, but is not final deployment approval.
- [x] Technical Step 2 acceptance based on operator-provided checks and rollback comparison; production mutation deferred to Step 5.

## Read-only commands — mango SSH terminal

```bash
cd /home/richard/playbooks
git status --short
git diff --check
git diff -- local-backup.yaml remote-backup.yaml scripts/local-backup.sh scripts/remote-backup.sh
ansible-playbook remote-backup.yaml --list-hosts --vault-password-file ~/.vault_pass.txt
ansible-playbook remote-backup.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
```

Do not replace local edits with repository HEAD or run full `remote-backup.yaml` in real mode yet.

**Acceptance note:** earlier checklist deferred rollback-copy creation to Step 5; explicit operator approval led to copying during Step 2 instead. Hashes and comparisons verified. Source-regression and refreshed final-diff checks are intentionally moved to Steps 3–4, not claimed complete here.
