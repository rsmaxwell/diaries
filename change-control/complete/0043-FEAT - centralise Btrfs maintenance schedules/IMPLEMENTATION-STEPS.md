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
Apply the 0043 Playbooks files using Beyond Compare 4 to `/home/richard/playbooks`. Then run:

```bash
cd /home/richard/playbooks
python3 roles/snapshots/tests/verify-0040-step13-source-prune-cap.py
python3 roles/snapshots/tests/verify-btrfs-snapshot-manager.py
python3 roles/snapshots/tests/verify-0040-prune-source-selection.py
python3 roles/snapshots/tests/verify-checkpoint-holds.py
python3 roles/snapshots/tests/verify-native-prune-subvolume-id.py
python3 roles/snapshots/tests/verify-btrfs-clear-stale-qgroups.py
```

Confirm the source schedule is installed under `/etc/ansible/group_vars/all/`
and use `ansible-inventory --host mars` and `--host backup` to verify **effective**
values. Host/group overrides take precedence over `all`; the former hourly
`mars` prune override has already been removed and both 04:15 values verified.

## Step 2 — deploy central schedule and code

On **mango SSH terminal**, use the normal `richard` account with its vault
password file, and confirm the authoritative `/etc/ansible` inventory values:

```bash
cd /home/richard/playbooks
test -f /etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml
ansible-inventory --host mars --yaml --vault-password-file ~/.vault_pass.txt
ansible-inventory --host backup --yaml --vault-password-file ~/.vault_pass.txt
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

Commit only the Playbooks 0043 implementation and documentation files; keep
feature evidence and readbacks in the Windows Diaries repository. The single
authoritative schedule lives under `/etc/ansible/group_vars/all/` on `mango`
and is not itself in Playbooks Git. Record its effective values and retain a
configuration recovery copy within feature evidence/normal system backup.
Preserve terminal evidence and Git revisions in this feature, record final
acceptance, then move the directory to `complete` only once reviewed.

## Rollback

Rollback is a schedule value change, not removal of the active inventory.
Restore the old calendars in the authoritative
`/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml`, verify effective
inventory for both hosts, and reapply the regular source/receiver playbooks.
The manager's supported 32-set bound is backward compatible with the
previous 10-set default. No snapshot restoration, state reset or destruction
of recovery holds is part of rollback. The retired installer is not used for rollback.

## 10 November inventory reconciliation

The operator renamed the schedule to `btrfs-maintenance-schedule.yaml`, and
standard Ansible discovery correctly loaded it from `/etc/ansible/group_vars/all`.
An obsolete source-prune calendar at `host_vars/mars/local-backup.yaml` took
precedence initially. The follow-up readback confirmed the host override was
absent and both host-effective prune calendars were 04:15 UTC. Source cap 32,
receiver cap 10. Installer tests failed only because of hard-coded old filename;
the dedicated installer and its tests are removed from this feature instead of
maintained. The 10 November live deployment subsequently passed on both hosts.
`mars` source and `backup` receiver pruning both have `OnCalendar=*-*-*
04:15:00 UTC`, are enabled, and the source service runs with `--max-delete 32`.
See `reports/DEPLOYMENT-RECONCILIATION-20261110.md` and Step 2 raw evidence.
The first natural daily prune was subsequently verified on 11 November;
see the final closure reconciliation below.

## 10 November live acceptance and Playbooks commit

The existing Windows feature script `tools/verify-0043-live-schedule.sh`
completed successfully at 13:23:34 UTC, writing
`evidence/Step 3/live-schedule-20261110-132334Z.txt`. All seven timer
checks passed. Both prune timers are **enabled and active**, with their next
elapses at **11 November 04:15 UTC**. The installed source service specifies
`--max-delete 32`. The two snapshot-manager readbacks returned 70 (`mars`)
and 33 (`backup`) complete timestamp sets, none incomplete, and qgroup status
OK. `mars` had eight stale qgroups and none under deletion; `backup` had none.
This is accepted as a read-only health result, not evidence of stale-qgroup
cleanup. The shared protected parent was verified as `20261110-030004Z`.

Playbooks source changes were committed as
`6d7f397048b8ed47c94f973a98096fc6e806e4e8` on `main`; five files
changed, including the bounded source manager, unit configuration, regression
test and maintenance documentation. The commit was published 10 November;
0043 Diaries evidence was published as
`293a755248982ce7a5db28ca35854310eb0d7235` the same day.
The Windows feature's `evidence/Step 4/playbooks-source-commit-20261110.txt`
preserves the source readback.

## 11 November natural-execution acceptance — Steps 3 and 4 CLOSED for operational acceptance

- At 04:15:02 UTC, `mars` reported `RETENTION sets: total=85 keep=69 sources=1`,
  `PRUNE-CAP eligible=16 selected=16 max_delete=32` and deleted all 16 selected
  complete timestamp sets. The journal listed both checkpoint holds and
  protected replication snapshot timestamps before deletion. The service
  returned `Result=success`, `ExecMainStatus=0` at 04:15:03 UTC.
- At 04:15:02 UTC, `backup` reported `RECEIVER-SIMPLE-DELETED count=0`,
  `Result=success`, `ExecMainStatus=0`. Zero receiver deletions was an ordinary
  successful result, not a failure to execute.
- The 08:10 UTC read-only verifier passed all seven timer checks and returned
  zero incomplete timestamp sets, zero stale/under-deletion qgroups on both
  hosts and valid production-backup verification on `mars`. The agreed
  protected parent matched as `20261111-030031Z`.
- The separate 0039 cleanup services completed at 05:30 UTC on both hosts;
  no manual prune, rescan, replication or restore was used for this acceptance.
- The operational and source-control acceptance gates are **PASS**. The final
  action is to archive the feature into `change-control/complete/`, commit the
  11 November receipts and verify GitHub publication; that action is not
  assumed successful before the operator's Git output.

**Evidence:** `evidence/Step 3/live-schedule-20261111-081029Z.txt`,
`evidence/Step 3/natural-pruning-20261111.txt`, and
`reports/FINAL-CLOSURE-RECONCILIATION-20261111.md`.
