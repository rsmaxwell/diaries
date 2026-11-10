# 0043-FEAT — Centralise Btrfs maintenance schedules

**Status:** IN PROGRESS — deployment, read-only host acceptance and Playbooks
source commit accepted; first natural daily prune and Diaries source-control
reconciliation pending. **Opened:** 10 November 2026.

## Purpose

Source and receiver pruning will both run daily at **04:15 UTC**, with source
prune bounded to **32** snapshot sets per cycle, receiver prune bounded to
**10**, and unchanged snapshot retention/parent/checkpoint protection.
The other clocks (hourly creation, 01:30 pull, 03:30 send, 05:30 stale-qgroup
cleanup) stay as configured. No activation flags change.

## Central configuration

The schedule is ordinary Ansible inventory; no custom installation script
is necessary. The authoritative operational schedule is
`/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml` on `mango`.
The standard `group_vars/all` path is automatically loaded by the default
Ansible inventory. There is **no required Playbooks `inventory/` copy**,
and no custom installer. Edit the `/etc/ansible` inventory directly, check
its effective host values, and apply the existing Playbooks roles. This
operational inventory is outside Git; preserve its content in this feature
evidence and through the established host-configuration backup. See
`IMPLEMENTATION-STEPS.md` and Playbooks `MAINTENANCE-SCHEDULE.md`.

## Evidence/status (10 November)

- **PASS:** 32-set source prune cap and protected-parent tests, including a
  40-snapshot backlog selection simulation.
- **PASS:** standard inventory file exists and Ansible discovers the renamed
  `btrfs-maintenance-schedule.yaml` file automatically.
- **PASS:** follow-up readback shows no remaining `mars` override. Effective
  source and receiver pruning calendars are both `04:15 UTC`; the caps are
  32 and 10 respectively.
- **PASS:** live source and receiver Ansible deployment on 10 November;
  `mars` source prune and `backup` receiver prune are installed and enabled
  for 04:15 UTC, and the `mars` service contains `--max-delete 32`.
- **PASS:** source manager preflight reported 70 complete sets, zero incomplete,
  qgroup status OK. Eight stale qgroups remain for separate 0039 follow-up.
- **PASS:** read-only Step 3 acceptance, 10 November 13:23 UTC. All seven
  maintenance timers were enabled/active with expected calendars; installed
  source pruning cap 32, snapshot health and agreed-parent equality verified.
- **PASS:** Playbooks 0043 commit
  `6d7f397048b8ed47c94f973a98096fc6e806e4e8` (clean working tree,
  ahead of origin/main by one commit at readback).
- **NOT YET ACCEPTED:** the first natural 04:15 daily prune cycle
  (11 November), subsequent 05:30 qgroup cleanup, and final Diaries Git commit.

The original name-specific installer `scripts/maintenance-schedule.py` and
its `scripts/tests/verify-maintenance-schedule.py` regression are deliberately
retired as redundant. 0043 retains only the established Ansible inventory and
role workflow. Files in `/etc/ansible` are not automatically versioned in Git.

## Other features

0042-FEAT remains CLOSED. 0039-DEF remains OPEN in Step 11; its approved
05:30 stale-qgroup cleanup activation must stay unchanged.

## Closure steps

1. Reconcile standard inventory and offline source regression — **PASS**.
2. Deploy via existing Ansible roles and record readback — **PASS**, 10 November.
3. Read-only host checks — **PASS**, 10 November; natural pruning
   behaviour — **OPEN**, next event 11 November at 04:15 UTC.
4. Playbooks 0043 source commit — **PASS**; Diaries evidence commit and
   formal closure — **OPEN**.

Keep 0043 under `change-control/in-progress/` until host and source-control
acceptance gates are met. No additional restore or replication test is required
when existing accepted correctness evidence remains sufficient.
