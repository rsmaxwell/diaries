# 0039-DEF — Step 8 inventory preparation and Step 9 shared source proposal

**Date:** 9 November 2026. **Source status:** offline change proposal prepared.
**Accepted gates:** only historical Steps 1–7. **Not accepted:** live Step 8 baseline,
Step 9 host compatibility, Step 10 deployment/activation, recurrence verification
and defect closure. **No production command or Git commit has been executed by
this proposal.**

## Inputs and repository provenance

- Diaries ZIP `diaries-sources-20261109-122400.zip` (SHA-256
  `d745caae5c413dff16871ed859e89ec2d4ffe85a4e167e8c1084d166c598c044`).
- Playbooks ZIP `playbook-sources-20261109-122355.zip` (SHA-256
  `c224e0958053b4663f717b5d6ca43a24ad4b2b629cd9b3538826fd61ac5ccd2e`).
- 9 November 0039 scope-confirmed documentation ZIP applied only to the
  *isolated extracted copy* when preparing the proposed Diaries package.
- The exported ZIPs contain no `.git` working-tree metadata. They cannot
  establish Windows/mango branch, current HEAD, uncommitted changes or actual
  installed binaries. Validate **before** applying either ZIP:

**Windows Cygwin terminal (Diaries repo):**

```bash
cd '/cygdrive/c/Users/Richard/git/github.com/rsmaxwell/diaries-application/diaries'
git status --short --branch
git rev-parse HEAD
git submodule status
cat .gitmodules
```

**Existing SSH terminal on mango (Playbooks repo):**

```bash
cd /home/richard/playbooks
git status --short --branch
git rev-parse HEAD
git remote -v
```

Do not assume a Windows Diaries ZIP has been synchronised to mango.

## Step 8 — findings from source inspection, not a live host diagnosis

1. The previous cleaner, at `roles/snapshots/files/btrfs-clear-stale-qgroups.py`,
   targeted `/` and the receiver writer lock only. Its previous lock order was
   **writer then manager**, contrary to the current manager-then-writer order
   in the 0040 agreed-parent receiver path.
2. Its installer and timer tasks were in generic `roles/snapshots/tasks/main.yaml`
   and restricted to `inventory_hostname == 'backup'`, but that role first
   refuses `remote_backup` hosts. The intended receiver deployment was
   therefore unreachable via the ordinary generic snapshots role.
3. The prior timer was default-off. The supplied ZIPs establish *source
   configuration only*; installed timers must be observed on both hosts.
4. 0040 evidence reported 606 stale qgroups on mars on 9 November. It suggests
   repeated entries after snapshot operations, **not** a proven kernel-level
   diagnosis. The current receiver version/marker support is still unknown.

A read-only, direct-SSH baseline collector is added under
`tools/collect-0039-step08-host-baseline.sh`. It records versions, mounts,
qgroup/subvolume inventories, effective manager configuration and timer state
separately for mars and backup, under `evidence/Step 08/`. Correlate captured
subvolume IDs with qgroup IDs and observe subsequent prune/replication cycles
before attributing a cause. **Step 8 remains OPEN.**

## Step 9 — code proposal (one shared implementation)

**Playbooks modifications:**

- Preserve one executable at `roles/snapshots/files/btrfs-clear-stale-qgroups.py`.
  Its CLI reads a local `/etc/btrfs-stale-qgroups.json` file rendered
  from endpoint-specific Ansible variables and cross-checks the existing
  snapshot-manager configuration. It defaults read-only; only `--execute` can trigger the native operation.
- Take `manager` then `writer` nonblocking locks. The writer lock must exist;
  lock files must be regular and unlinked. No new writer lock is created.
- Verify Btrfs mountpoint and UUID, manager's role/config/lock contract,
  supported qgroup output including path column, and independent active
  subvolume IDs. Distinguish `<stale>`, `<under deletion>` and unmarked orphans;
  refuse unexpected marker/live-subvolume discrepancies.
- Detect native `btrfs qgroup clear-stale` support; fail closed if missing.
  Do **not** issue `qgroup destroy`, `quota rescan`, `subvolume delete`, or
  changes to replication/parent/receipt state. Refuse batches of more than
  2,000 stale qgroups to avoid unattended mass deletion on unexpected backlog.
- Retire the unreachable generic snapshots-role installer and place
  installation/activation under `roles/btrfs-replication/tasks/qgroup-maintenance.yaml`,
  included by `native.yaml` for both endpoints. Render the same service/timer templates on each host, but give each its own
  `/etc/btrfs-stale-qgroups.json` (`0600`) for mode, filesystem, writer lock
  and cleanup limit. No host-specific script or service command line is needed.
- Both install and timer-activation gates are `false` by default in
  `roles/btrfs-replication/defaults/main.yaml`; no host_vars or inventory
  activation is included in the source ZIP.

**Source-level tests executed in the isolated container copy:** 14 new offline
qgroup tests PASS, existing qgroup audit PASS and 18 historical cleanup tests
PASS. Bash collector syntax, five YAML files and four Jinja template renders
PASS. See `evidence/Step 09/SOURCE-TEST-RESULTS-20261109.txt`. These tests use
mocks/local temporary locks, **not** a real Btrfs filesystem.

**Still to verify on mango:** after applying Playbooks ZIP, run the source test,
`ansible-playbook --syntax-check btrfs-replication.yaml`, read-only Step 8 host
baselines, inventory check/diff, and both host dry-runs. No acceptance is
claimed for the live Ansible inventory or any kernel/Btrfs feature level.

## Activation and rollback boundaries (Step 10; not executed)

After Step 8 and Step 9 review, optionally install with
`btrfs_stale_qgroup_maintenance_install_enabled: true` on each host but
`btrfs_stale_qgroup_maintenance_enabled: false` until dry-run acceptance.
Only when the operator has approved mutating housekeeping, enable that
second variable and deploy through `btrfs-replication.yaml` on mango. The
05:30 UTC default is proposed, not proof of a conflict-free schedule; locks
must safely defer overlapping transfers/prunes. Roll back by disabling the
timers through the same variable, without trying to undo valid quota removals.
Record resulting Ansible commands, revisions, timer/journal state and host
results under `evidence/Step 10/`.

This code does not resolve kernel qgroup lifecycle defects: it implements
periodic safe reconciliation where supported. A host that cannot meet the
capability/classification gates **blocks** Step 11 acceptance; do not silently
close the defect or bring Ubuntu upgrades back into scope.
