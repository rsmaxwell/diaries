# 0043-FEAT — Centralise Btrfs maintenance schedules

**Status:** **CLOSED — final operational acceptance 11 November 2026.**
All four implementation steps are accepted. Formal archive movement and the
final Diaries Git commit/push remain administrative actions requiring operator
readback. **Opened:** 10 November 2026.

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
- **PASS — natural 11 November 04:15 UTC prune:** `mars` deleted **16** eligible complete timestamp sets (`selected=16`, `max_delete=32`), preserving checkpoint and replication holds. `backup` ran at 04:15 with `RECEIVER-SIMPLE-DELETED count=0`; no deletions were required. Both services returned `Result=success` and `ExecMainStatus=0`.
- **PASS — post-cycle health at 08:10 UTC:** all seven scheduled timers enabled/active with expected calendars; `mars` 73 and `backup` 34 complete timestamp sets, zero incomplete; stale qgroups zero; source production-backup verification valid; agreed protected parent `20261111-030031Z` on both hosts. The independently accepted 0039 05:30 cleanup ran successfully on both hosts.
- **PASS — source control:** 0043 Playbooks commit `6d7f397048b8ed47c94f973a98096fc6e806e4e8` and Diaries acceptance commit `293a755248982ce7a5db28ca35854310eb0d7235` were published on 10 November. On 11 November, the later Playbooks revision `7dfa93fef6d975aa82f5f4cfdf54497b106e7645` was clean and synchronised; final Diaries feature-closure commit remains to be executed.

See `reports/FINAL-CLOSURE-RECONCILIATION-20261111.md`,
`evidence/Step 3/live-schedule-20261111-081029Z.txt` and
`evidence/Step 3/natural-pruning-20261111.txt`.

The original name-specific installer `scripts/maintenance-schedule.py` and
its `scripts/tests/verify-maintenance-schedule.py` regression are deliberately
retired as redundant. 0043 retains only the established Ansible inventory and
role workflow. Files in `/etc/ansible` are not automatically versioned in Git.

## Other features

0042-FEAT remains CLOSED. 0039-DEF's two-cycle unattended housekeeping
acceptance also passed on 11 November, allowing its separate formal closure.
The approved 05:30 stale-qgroup cleanup activation stays unchanged.

## Closure steps

1. Reconcile standard inventory and offline source regression — **PASS**.
2. Deploy via existing Ansible roles and record readback — **PASS**, 10 November.
3. Read-only host checks — **PASS**, 10 and 11 November; natural pruning
   behaviour — **PASS**, 11 November at 04:15 UTC.
4. Playbooks 0043 source commit and Diaries initial evidence commit — **PASS**,
   published 10 November. Final evidence reconciliation — **PASS**, 11 November.
   Archive move, final Diaries commit and push — **operator action pending**.

All implementation/operational gates are accepted. Archive 0043 under
`change-control/complete/`, commit/publish the closure documentation and verify
Git state. Do not mark the Git publication as successful until the command
returns success. No additional restore or replication test is required.
