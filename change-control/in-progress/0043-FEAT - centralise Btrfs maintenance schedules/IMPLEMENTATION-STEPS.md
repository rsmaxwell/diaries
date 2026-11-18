# 0043-FEAT implementation and acceptance

## Design decisions

**Parallel 04:15 pruning** is acceptable because `mars` and `backup` use
independent Btrfs filesystems and manager locks. Source and receiver pruning
both validate the shared agreed-parent state and protected checkpoints. The
03:30 replication normally finishes before 04:15. `AccuracySec=1min` means
“same time” is approximate, not atomic coordination. Neither prune should
require a global lock spanning both machines.

Pruning generally **queues** asynchronous Btrfs subvolume cleanup. Its
service may finish before disk blocks and qgroups are reclaimed. Concentrating
up to 32 deletions daily creates a burst of housekeeping, possibly extending
into the 05:30 stale-qgroup run. 0039 handles busy qgroups only when their IDs
match pending deletions. A daily prune retains more expired snapshots during
the day than hourly pruning, so watch free space and qgroup backlog.

**Capacity correction:** source makes ~24 hourly snapshots/day, so the old
source service limit 10 could not keep up if run daily. Source cap therefore
becomes 32 (still bounded, all candidate validation performed, protected
agreed parents and checkpoint holds untouched). The receiver gets only one
latest replication snapshot per normal cycle, so its existing cap 10 is
unchanged. The 48/14/12/24/5 retention buckets are unchanged.

**Timer behaviours:** creation and source pruning retain `Persistent=true`;
receiver pruning and qgroup maintenance retain `Persistent=false`. Do not
change the independent timer activation flags.

## Step 1 — baseline and local regressions

On **mango SSH terminal**, before applying the Playbooks ZIP:

```bash
cd /home/richard/playbooks
git status --short --branch
git rev-parse HEAD
git diff --check
```

Expected baseline on 10 November is Playbooks `ba8dfe59dd720dc2c84c6d9480552d5d475e8aca`, clean `main`.
Apply `0043-FEAT-playbooks-central-maintenance-schedule-20261110.zip`
using Beyond Compare 4 to `/home/richard/playbooks`. Then run:

```bash
cd /home/richard/playbooks
python3 roles/snapshots/tests/verify-0040-step13-source-prune-cap.py
python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py
python3 roles/snapshots/tests/verify-0040-prune-source-selection.py
python3 roles/snapshots/tests/verify-checkpoint-holds.py
python3 roles/snapshots/tests/verify-native-prune-subvolume-id.py
python3 roles/snapshots/tests/verify-btrfs-clear-stale-qgroups.py
python3 scripts/tests/verify-maintenance-schedule.py
python3 scripts/maintenance-schedule.py --plan
```

`--plan` MUST report no conflicting `group_vars` or `host_vars` definitions.
If it refuses, inspect effective inventory and reconcile before applying;
do not overwrite existing inventory files blindly.

## Step 2 — deploy central schedule and code

On **mango SSH terminal**, with accepted plan:

```bash
cd /home/richard/playbooks
sudo -n python3 scripts/maintenance-schedule.py --apply \
  --vault-password-file /home/richard/.vault_pass.txt
python3 scripts/maintenance-schedule.py --verify \
  --vault-password-file /home/richard/.vault_pass.txt
ansible-playbook snapshots.yaml --limit mars --tags snapshots \
  --check --diff --vault-password-file ~/.vault_pass.txt
ansible-playbook btrfs-replication.yaml --limit 'mars,backup' \
  --skip-tags qgroup-maintenance --check --diff \
  --vault-password-file ~/.vault_pass.txt
```

Inspect both previews, especially manager cap, `btrfs-snapshot-prune.timer`,
`btrfs-receiver-simple-prune.timer` and any unrelated changes. **If accepted**,
run the same two playbook commands without `--check`; retain `--diff`.
No extra `--tags qgroup-maintenance` operation is needed; its existing 05:30
activation must not be disturbed.

## Step 3 — read-only host acceptance

On **Windows Cygwin**, from the Windows Diaries repo root:

```bash
bash 'change-control/in-progress/0043-FEAT - centralise Btrfs maintenance schedules/tools/verify-0043-live-schedule.sh'
```

The script captures a timestamped report under this feature's `evidence/Step 3`.
It verifies installed `OnCalendar` values, enabled timers, manager cap 32,
snapshot status and agreed-parent equality. It triggers no prune, transfer,
subvolume deletion, quota rescan or cleanup. Record the first natural 04:15
prune executions on 11 November and avoid conflating ongoing Btrfs deletion
with a completed systemd invocation.

## Step 4 — source control and formal closure

Commit only the Playbooks 0043 files; keep feature evidence and readbacks in
the Windows Diaries repository. Do not treat inventory `/etc/ansible` as a
Git repository. Its canonical file is versioned under `playbooks/inventory`.
Preserve terminal evidence and Git revisions in this feature, record final
acceptance, then move the directory to `complete` only once reviewed.

## Rollback

The installer can remove its own **unchanged** managed inventory file:

```bash
cd /home/richard/playbooks
sudo -n python3 scripts/maintenance-schedule.py --remove
```

Re-run the normal source/receiver playbooks (Step 2) to restore inherited
role-default calendars. If you need to preserve the previous configured
schedule instead, edit the canonical Playbooks YAML, re-install and deploy it.
The manager's supported 32-set bound is backward compatible with the
previous 10-set default. No snapshot restoration, state reset or destruction
of recovery holds is part of rollback. Do not run `--remove` unless the
inventory schedule has been verified and a corresponding redeployment is
planned.
