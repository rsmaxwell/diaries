# 0042-FEAT — Implementation and verification

**Status as of 10 November 2026: Steps 1–2 VERIFIED; Step 3 CORE CHECKS PASSED WITH BACKUP-STATUS READBACK PENDING; FORMAL ACCEPTANCE PENDING.** All historical raw evidence is preserved under this feature. The 215 Playbooks deletions remain staged and not yet committed. 0039 changes must be kept distinct.

## Step 1 — Verify source and archive obsolete Playbooks code

1. In **Windows Beyond Compare 4**, apply `0042-FEAT-diaries-source-retirement-20261110.zip` to the authoritative Diaries repo; apply the Playbooks ZIP to the **mango** Playbooks repo. Compare `native.yaml` and `defaults/main.yaml` against the already uncommitted 0039 changes; preserve anything newer.
2. On **mango**, inspect `cd /home/richard/playbooks; git status --short --branch; git rev-parse HEAD; git diff --check` and run the five active regression commands below.
3. Synchronise the new Diaries feature from Windows to `/home/richard/diaries` on mango (the script lives ONLY in the feature directory). Verify it is present and matches Windows before running.
4. Run the feature-local tool `--plan` from `/home/richard/playbooks`. It checks all 215 exact tracked paths and SHA-256 hashes, refuses modified/staged/symlink files, validates that the active simplified service is retained, and confirms 0039 qgroup integration.
5. Only after accepting the resulting exact list, run `--apply --expect-count 215 --confirm RETIRE-0042-PLAYBOOKS-ONLY`. This makes a verified compressed rollback archive **before** staging `git rm` of the exact 215 files. It touches **only Playbooks source**; no host files, Btrfs state, or running service. Synchronise generated receipts and rollback archive from mango into the Windows Diaries feature before closing Step 1.

Run from **mango SSH terminal**, with working directory `/home/richard/playbooks`:

```bash
cd /home/richard/playbooks
python3 '/home/richard/diaries/change-control/in-progress/0042-FEAT - retire obsolete native Btrfs replication implementation/tools/retire-0042-playbooks-source.py' --plan
# Once the plan is reviewed and accepted:
python3 '/home/richard/diaries/change-control/in-progress/0042-FEAT - retire obsolete native Btrfs replication implementation/tools/retire-0042-playbooks-source.py' --apply --expect-count 215 --confirm RETIRE-0042-PLAYBOOKS-ONLY
```

### Active source regressions (mango, `/home/richard/playbooks`)

```bash
python3 roles/btrfs-replication/tests/verify-0040-legacy-retirement-source.py
python3 roles/btrfs-replication/tests/verify-0040-simplified-cutover-readiness.py
python3 roles/btrfs-replication/tests/verify-0040-simplified-replication.py
python3 roles/btrfs-replication/tests/verify-0040-simplified-protection.py
python3 roles/btrfs-replication/tests/verify-0040-step12-3-shared-retention.py
python3 roles/snapshots/tests/verify-0040-simplified-receiver-retention.py
python3 roles/snapshots/tests/verify-diaries-backup-status.py
python3 roles/snapshots/tests/verify-btrfs-clear-stale-qgroups.py
```

## Step 2 — Ansible and deployment

On **mango**, confirm Playbooks branch, HEAD and working-tree changes; run:

```bash
cd /home/richard/playbooks
ansible-playbook btrfs-replication.yaml --syntax-check --vault-password-file ~/.vault_pass.txt
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff --skip-tags qgroup-maintenance --vault-password-file ~/.vault_pass.txt
```

Review that the preview retains the simplified sender service and receiver pruning timers, with no snapshot/data deletion or unexpected units. **Do not run the unrestricted full playbook while 0039 timer activation is supplied only by extra-vars.** This feature explicitly uses `--skip-tags qgroup-maintenance` to preserve the existing enabled 05:30 timers on both hosts; 0039 owns their activation and host-specific configuration. After reviewing changes, one normal `ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --skip-tags qgroup-maintenance --vault-password-file ~/.vault_pass.txt` is sufficient; it does **not** initiate a replication cycle or prune. Record actual output; do not claim deployment until run.

## Step 3 — Consolidated post-deployment acceptance

Run the feature-local read-only host-retirement audit (from a synced feature on **mango**):

```bash
cd /home/richard/diaries
python3 'change-control/in-progress/0042-FEAT - retire obsolete native Btrfs replication implementation/tools/verify-0042-host-retirement.py'
```

This checks **39 accepted 0040 paths on mars and 35 on backup** for continued absence. It does not remove anything. If a path has reappeared, stop and investigate before considering a new exact-file removal.

Verify **read-only** on mars and backup: `systemctl show ... -p ExecStart`, `btrfs-simplified-replication sender status`, `receiver status`, status report `diaries-backup-status --json`, all enabled timers, absence of the old endpoint sudoers, and current snapshot-manager health. The accepted production parent from the 10 November baseline is `20261110-030004Z` and both ends reported `relation=equal`, `receiver_parent_verified=true`; the *later* parent may have advanced normally. Compare sender and receiver, not against a frozen date. Check that older host binaries did not reappear; do not delete host files from this feature. Reuse accepted 0040 restore and transfer evidence.

Step 3 and overall feature close only after user acceptance; preserve a separate change package and Git receipts for Diaries and Playbooks.


## Executed-stage evidence reconciliation — 10 November 2026

| Step | Technical outcome | Evidence | Formal status |
|---|---|---|---|
| 1 — Source verification and archive | 215 exact source files hash-checked, archived, archive read back, and staged with `git rm`; all eight regression suites passed after correcting the root-ownership test fixture | `evidence/Step 1/0042-source-retirement-20261110-081412Z.json`, `0042-retired-playbooks-20261110-081412Z.tar.gz`, `source-retirement-plan.txt`, `source-verification-20261110.txt` | Awaiting user acceptance and Playbooks Git receipt |
| 2 — Syntax and deployment | Ansible syntax passed; preview 0 changed/0 failed; deployed with `--skip-tags qgroup-maintenance`, `mars` 14 OK/0 changed, `backup` 25 OK/0 changed | `evidence/Step 2/deployment-20261110.txt`; preview in Step 1 verification | Awaiting user acceptance |
| 3 — Host acceptance | Previously retired 39 `mars` and 35 `backup` paths absent; same verified parent at both ends; timers active; snapshot integrity passed; 0039 qgroup functionality intact | `evidence/Step 3/post-deployment-20261110.txt` | Awaiting final backup-status readback and user acceptance |

Outstanding for formal closure: one read-only `diaries-backup-status --json` check on `mars` (planned in Step 3 but not present in the uploaded execution logs), verification that the rollback archive hash equals the receipt's `archive_sha256` after synchronisation, separate Git commit receipts for 0042 Playbooks and Diaries, and explicit acceptance of Steps 1–3. Avoid staging uncommitted 0039 files indiscriminately. No fresh restore, snapshot deletion or replication transfer is required.
