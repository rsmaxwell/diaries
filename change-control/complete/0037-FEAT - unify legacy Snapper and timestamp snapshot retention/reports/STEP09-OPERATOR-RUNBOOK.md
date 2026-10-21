# Step 09 — Stage Playbooks deployment with deletion disabled

**Execution model:** Windows Diaries Cygwin terminal for evidence captures; existing `mango` terminal for one targeted Ansible installation. Avoid staging scripts on `mars` or `backup`.

## Gate A — Source and no-approval preflight

In `mango` SSH terminal:

```bash
cd ~/playbooks
python3 -m py_compile roles/snapshots/files/btrfs-snapshot-manager.py
python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py
sha256sum roles/snapshots/files/btrfs-snapshot-manager.py
ansible mars --list-hosts
```

Confirm Step 7 regression remains valid for this source version. Verify no recent unreviewed change to manager source.

In Windows Cygwin at Diaries repository root:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step09-capture-from-cygwin.sh" pre
```

Inspect `evidence/Step 09/pre/` before deployment. Do not proceed if baseline preflight fails. In particular compare `manager-sha` with the `mango` source hash, and review unit definitions and the active timer schedule.

## Gate B — Targeted copy on mango (no full role execution)

```bash
cd ~/playbooks
ansible mars -b -m ansible.builtin.copy \
  -a "src=roles/snapshots/files/btrfs-snapshot-manager.py dest=/usr/local/sbin/btrfs-snapshot-manager owner=root group=root mode=0755 backup=yes"
```

Retain the `backup_file` returned by Ansible, and capture the console log into the feature's evidence (do not put log files into Playbooks). **No feature-wide Ansible playbook is run**, so role-managed scheduler resources cannot be changed by this deployment command.

## Gate C — Post-deployment capture

In Cygwin:

```bash
bash "change-control/in-progress/0037-FEAT - unify legacy Snapper and timestamp snapshot retention/tools/step09-capture-from-cygwin.sh" post
```

Review both capture directories. Check explicitly:

1. `post/manager-sha.txt` matches the source SHA-256 from `mango`.
2. `pre/unit-definitions.txt` and `post/unit-definitions.txt` match; timers and enabled-state match (times until next execution can move).
3. Service definitions invoke only `create` and `prune`, never `legacy-delete`.
4. Both native and legacy planning checks succeeded; confirm deletion actions were not executed.
5. Journals show no newly introduced errors; a scheduled run may legitimately create or prune native sets while captures are taken.
6. `backup` receiver was not modified, and no directories were created for its obsolete diagnostic path.

## Rollback (only if a gate fails)

Do not improvise removal or delete any snapshots. Capture errors first. Use the exact Ansible-generated `backup_file` path, NOT a guessed filename. In the `mango` terminal, after ensuring no snapshot-manager job is active and recording the decision, restore only the executable using a targeted Ansible copy from a trusted controller-side copy or an audited remote restore operation. Re-run the post capture. If uncertain, stop and request review before rollback. Native timers remain untouched.

## Close-out

Capture logs/hashes inside `evidence/Step 09/`; update implementation steps and close Step 9 **only after** comparing all gates and reviewing operator evidence. Step 9 must not authorise Step 10 pilot candidates.
