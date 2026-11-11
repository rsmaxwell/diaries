# 0043 — Deployment and installed timer reconciliation (10 November 2026)

## Conclusion

**PASS — deployment and timer readback** for the new daily 04:15 UTC source
and receiver pruning schedules. This accepts 0043 Step 2; it does not yet
accept the first natural 04:15 pruning runs due on 11 November.

## Captured terminal evidence

`evidence/Step 2/deployment-20261110-130709.txt` is the unmodified operator
terminal log. The command was executed as `richard` on `mango`.

- Effective Ansible inventory was verified for both hosts before deployment.
- Source cap regression passed including 40 candidates, 32 selected, and
  boundary rejection at 33.
- `ansible-playbook snapshots.yaml --limit mars --tags snapshots`:
  `mars ok=28 changed=2 failed=0 unreachable=0`.
- `ansible-playbook btrfs-replication.yaml --limit 'mars,backup'
  --skip-tags qgroup-maintenance`: `backup ok=25 changed=1 failed=0`;
  `mars ok=14 changed=0 failed=0`.
- `mars` source pruning timer installed and enabled:
  `OnCalendar=*-*-* 04:15:00 UTC`, `Persistent=true`.
- `mars` source pruning service installed with `--max-delete 32`.
- `backup` receiver pruning timer installed and enabled:
  `OnCalendar=*-*-* 04:15:00 UTC`, `Persistent=false`.

## Health and boundaries

The source manager preflight returned `filesystem=btrfs`,
`complete_timestamp_sets=70`, `incomplete_timestamp_sets=0`,
`qgroups_status=ok`, `qgroups_stale=8`, and
`qgroups_under_deletion=0`. The eight stale qgroups remain within the
separate 0039-DEF maintenance investigation, not evidence of a successful
0043 prune or an instruction to run manual qgroup cleanup.

No failure was reported by either playbook, and no manual prune or
replication command was executed in the deployment log. The independent
agreed-parent protections were not disabled or changed.

## Inventory ownership

The operator's authoritative schedule is
`/etc/ansible/group_vars/all/btrfs-maintenance-schedule.yaml` on `mango`.
Ansible discovers it directly. The initial special installer was removed
because it duplicated normal Ansible inventory semantics. No second
`playbooks/inventory/` schedule file is required.

## Still open

1. **COMPLETED:** Read-only host verification on 10 November 13:23:34 UTC
   (all seven timer checks, health and agreed parent), in the separate
   `reports/LIVE-READBACK-ACCEPTANCE-20261110.md`.
2. Observe the next natural daily 04:15 prune on both hosts and subsequent
   05:30 qgroup maintenance, checking protection and status.
3. **COMPLETED:** Playbooks implementation committed as `6d7f397048b8ed47c94f973a98096fc6e806e4e8`.
   Diaries evidence commit and formal closure remain open. 0039 Step 11 is
   separately open.
