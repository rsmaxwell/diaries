# 0042-FEAT — Implementation and verification

**Status as of 10 November 2026: Steps 1–4 CLOSED upon final closure commit; 0042-FEAT formally accepted.** The completed feature includes source retirement, deployment, rollback evidence, independent host verification and separate source-control receipts. 0039 remains independent and OPEN.

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

Step 3 was accepted from the successful read-only host audit and subsequent backup-status readback. The source-control receipts and feature closure are recorded in Step 4 below.


## Executed-stage evidence reconciliation — 10 November 2026

| Step | Technical outcome | Evidence | Formal status |
|---|---|---|---|
| 1 — Source verification and archive | 215 exact source files hash-checked, archived and retired; all eight regression suites passed | Step 1 evidence plus Playbooks commit `328b81b` | **CLOSED** |
| 2 — Syntax and deployment | Ansible syntax passed; preview and real deployment both 0 changed/0 failed | `evidence/Step 2/deployment-20261110.txt`; preview in Step 1 | **CLOSED** |
| 3 — Host acceptance | 39 `mars` and 35 `backup` legacy paths absent; equal parent; timers active; snapshots and latest production backup verified | `evidence/Step 3/post-deployment-20261110.txt`, `final-readback-20261110.txt` | **CLOSED** |
| 4 — Source-control reconciliation and formal closure | Separate 0042 commits verified; rollback archive SHA-256 matches receipt and is explicitly tracked in closure commit; 0039 changes excluded | `evidence/Step 4/playbooks-source-commit-20261110.txt`, `diaries-evidence-commit-20261110.txt`, `reports/FINAL-CLOSURE-20261110.md` | **CLOSED on final closure commit** |

## Step 4 — Formal acceptance and final repository move

The Playbooks retirement was committed as `328b81b3606ebff98fc8787d2a08eff3627d2a78` (215 deletions and eight 0042 updates). The Diaries acceptance evidence was committed as `e8907ba9c7544d239671e6acf6fedc7eaa194947` (17 files). Both commits kept the uncommitted 0039 changes separate. The final 10 November readback verified archive SHA-256 `d00f75fd7d3d5000f234f633ad65887331f122f57a58c3e9b1302971facba37b` and 215 archive members. `diaries-backup-status --json` showed verified production backup `20261110-003113Z` and identical parent `20261110-030004Z`.

The raw rollback archive had been copied to Windows but was excluded by the repository's generic `change-control/**/evidence/**/*.tar.gz` rule. The final closure change therefore tracks this one archive using `git add -f` and then moves the feature directory, including the tracked archive, from `in-progress` to `complete`. This is an explicit evidence-preservation exception, not a change to the general ignore rules. Historical raw logs remain unchanged.

**Acceptance:** The previously agreed implementation, regression, deployment and host criteria have been satisfied. Steps 1–4 are formally closed when the operator applies and commits the reviewed closure move. No further host action or new restore test is required. 0039-DEF remains in progress and must not be staged or committed as part of 0042.
