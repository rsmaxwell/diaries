# 0049 — Package application and next verification instructions

**Status:** APPLY/VERIFY INSTRUCTIONS ONLY. Neither ZIP was applied to the user's checkout, `mango`, `mars`, or `backup` by this source build. The feature remains `in-progress`.

## Compare, do not overwrite local work

Two repository-relative ZIP packages:

1. `0049-FEAT-diaries-change-control-implementation.zip` — copy the `change-control/in-progress/0049-FEAT - rationalise Btrfs and Diaries backup management/` directory into the **Windows Diaries parent repository** using Beyond Compare 4. Reconcile changes to existing feature files rather than replacing local edits.
2. `0049-FEAT-playbooks-implementation.zip` — compare/apply changed `roles/...` files to the **actual Playbooks Git submodule on `mango`**, using the remote Beyond Compare tab. It is **not** a ZIP for the Ansible-controller root or private inventory. Preserve any more recent local changes. The 0041 gate, sudoers, SSH forced-command and privileges must not be changed by a conflicted merge.

Expected bundle baseline: Playbooks `main` HEAD `0904bc7ebe801e391a3aa4dc59bbc9ccc7dfa532`; controller parent `e3252278c0daad974a84c8a145edee4a229fd4fd`. The latest uploaded Playbooks tree was under `ansible-controller/playbooks/`. The historical `/home/richard/playbooks` may be a different checkout; confirm paths first.

### 1. Read-only checkout inspection

**On an existing `mango` SSH terminal:**

```bash
for p in /home/richard/ansible-controller /home/richard/ansible-controller/playbooks /home/richard/playbooks; do
  if git -C "$p" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    printf '\n=== %s ===\n' "$p"
    git -C "$p" rev-parse --show-toplevel
    git -C "$p" branch --show-current
    git -C "$p" rev-parse HEAD
    git -C "$p" status --short
  fi
done
git -C /home/richard/ansible-controller submodule status
```

**On the Windows Cygwin terminal:**

```bash
cd /cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries
git branch --show-current
git rev-parse HEAD
git status --short
git submodule status
```

Ensure checked-out revisions and dirty files are reconciled with the baseline before applying the ZIPs.

### 2. Run source tests and Ansible preview on mango

The following assumes the inspected Playbooks checkout is the **current** `/home/richard/ansible-controller/playbooks`, matching the uploaded bundle. If a different checkout is active, use that actual path consistently rather than copying files into an obsolete clone.

**mango SSH terminal:**

```bash
cd /home/richard/ansible-controller/playbooks
python3 roles/btrfs-replication/tests/verify-0049-backup-management.py
python3 roles/btrfs-replication/tests/verify-0041-restricted-identity.py
python3 roles/btrfs-replication/tests/verify-replication.py
python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py
python3 roles/snapshots/tests/verify-diaries-backup-history.py
python3 roles/snapshots/tests/verify-diaries-backup-status.py
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' --check --diff --vault-password-file ~/.vault_pass.txt
```

The `--check --diff` command is only a preview: it cannot prove systemd timers were migrated, nor does it execute a replication or receiver-prune cycle. Inspect its changes for 0041 accounts and sudoers, receiver max-delete=10, original 03:30/04:15 UTC schedules, as well as all new and old unit names. Be cautious about recording Ansible diffs of secret files: store only appropriately redacted evidence in this feature directory.

**Private inventory is not included.** The new neutral variable names temporarily fall back to the existing inventory names so an unmodified private inventory should retain the existing schedules. Review effective values on each host before actual deployment, and make deliberate changes to the private inventory submodule as a separate controlled edit; do not commit secrets to Playbooks.

### 3. Deployment gate and host acceptance (not yet authorised/executed by package)

Deployment requires a reviewed inventory and source/regression result. Do not start a manual push/prune or run new and old timers simultaneously. Install runtime/gates, stop old timer, check old service not running, then enable new timer; the Ansible task order enforces this and fails closed for in-flight work. Apply receiver before sender if the approved cutover proceeds.

The feature contains `tools/verify-0049-live-readonly.sh`, which checks source/receiver state after installation without initiating backup operations. Copy/synchronise the Windows feature directory to `mango` before running it; do **not** assume it exists in the mango Diaries checkout merely because the Windows ZIP was applied. The script checks local-only JSON, snapshot status/list and prune dry-run, unit exclusivity and parent file hashes; preserve its output under this feature's evidence folder. It treats health warnings as failures to investigate, not proof of irrecoverable backups.

### 4. Rollback

Stop new timers before restoring old files and units from the pinned Playbooks revision. Only re-enable former timers after ensuring no dual activity. Restore 0041 dedicated identities/gates (never privileged `richard` or blanket sudo). **Never** reset `.simple-agreed-parent.json`, remove snapshot data, prune on production as a test, or rebootstrap an agreed parent. Record rollback verification before accepting the feature.
